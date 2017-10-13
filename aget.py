import asyncio
import aiohttp
import logging
import os

from tqdm import tqdm

LOGGER = logging.getLogger(__name__)


class ClosedRange:
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

    def __iter__(self):
        yield self.begin
        yield self.end

    def __str__(self):
        return '[{0.begin}, {0.end}]'.format(self)

    def __len__(self):
        return self.end - self.begin + 1


class Download:
    def __init__(self, url, output, num_blocks, max_retries):
        self.url = url
        self.output = output
        self.num_blocks = num_blocks
        self.max_retries = max_retries
        loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=loop)

    async def get_download_size(self):
        async with self.session.head(self.url) as response:
            response.raise_for_status()
            return int(response.headers['Content-Length'])

    async def split(self):
        part_len, remain = divmod(self.size, self.num_blocks)
        return [
                ClosedRange(
                    begin=i * part_len,
                    end=(i + 1) * part_len - 1
                ) for i in range(self.num_blocks - 1)
            ] + [
                ClosedRange(
                    begin=(self.num_blocks - 1) * part_len,
                    end=self.size - 1
                )
            ]

    async def download_block(self, id, tried):
        header = {'Range': 'bytes={}-{}'.format(*self.blocks[id])}
        try:
            async with self.session.get(self.url, headers=header) as response:
                response.raise_for_status()
                async for chunk in response.content.iter_chunked(1024):
                    # Be sure that there's no 'await' between next two lines!
                    self.output.seek(self.blocks[id].begin)
                    self.output.write(chunk)
                    self.blocks[id].begin += len(chunk)
                    self.tqdm.update(len(chunk))
            LOGGER.debug('block %d: %s done', id, self.blocks[id])
        except Exception as exc:
            try:
                msg = exc.args[0]
            except IndexError:
                msg = exc.__class__.__name__
            LOGGER.warning(
                'block %d failed: %s, retrying %d/%d',
                msg, tried, self.max_retries
            )
            return await self.download_block(id, tried + 1)

    def close(self):
        self.session.close()
        self.output.close()
        try:
            self.tqdm.close()
        except AttributeError:
            pass

    async def download(self):
        self.size = await self.get_download_size()
        if self.num_blocks > self.size:
            LOGGER.error(
                'Too many blocks(%d > file size %d)!',
                self.num_blocks, self.size
            )
            self.close()
            return

        # pre-allocate file
        os.posix_fallocate(self.output.fileno(), 0, self.size)
        self.blocks = await self.split()
        self.tqdm = tqdm(
            total=self.size, unit='B',
            unit_scale=True, unit_divisor=1024
        )
        await asyncio.wait(
            [self.download_block(i, 0) for i in range(self.num_blocks)]
        )
        self.close()
