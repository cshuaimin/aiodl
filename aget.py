import asyncio
import aiohttp
import logging
import functools
import os

from tqdm import tqdm
from aiohttp.client_exceptions import ClientError, ClientResponseError

LOGGER = logging.getLogger(__name__)


class AgetQuitError(Exception):
    'Something caused aget to quit.'


# Copied from tqdm.tqdm.format_sizeof() :)
def format_size(num):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 999.95:
            if abs(num) < 99.95:
                if abs(num) < 9.995:
                    return '{0:1.2f}'.format(num) + unit + 'B'
                return '{0:2.1f}'.format(num) + unit + 'B'
            return '{0:3.0f}'.format(num) + unit + 'B'
        num /= 1024
    return '{0:3.1f}Y'.format(num) + 'B'


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
    def __init__(self, url, output_fname,
                 num_blocks, blocks, max_retries, quiet):
        self.url = url
        self.output_fname = output_fname
        self.num_blocks = num_blocks
        self.max_retries = max_retries
        self.blocks = blocks
        self.quiet = quiet

    def retry(coro_func):
        @functools.wraps(coro_func)
        async def wrapper(self, *args, **kwargs):
            tried = 0
            while True:
                tried += 1
                try:
                    return await coro_func(self, *args, **kwargs)
                except ClientResponseError as exc:
                    msg = exc.args[0].replace(", message='", ' ')[:-1]
                    LOGGER.error(msg)
                    # won't retry
                    raise AgetQuitError from exc
                except (ClientError, asyncio.TimeoutError) as exc:
                    msg = str(exc) or exc.__class__.__name__
                    if tried <= self.max_retries:
                        sec = tried * 2
                        LOGGER.warning(
                            '%s() failed: %s, retry in %d seconds (%d/%d)',
                            coro_func.__name__, msg, sec,
                            tried, self.max_retries
                        )
                        await asyncio.sleep(sec)
                    else:
                        LOGGER.error(
                            '%s() failed: %s, max retry exceeded!',
                            coro_func.__name__, msg
                        )
                        raise AgetQuitError from exc
        return wrapper

    @retry
    async def get_download_size(self):
        async with self.session.head(self.url) as response:
            response.raise_for_status()
            size = int(response.headers['Content-Length'])
            LOGGER.info(
                'Length: %s [%s]',
                format_size(size), response.headers['Content-Type']
            )
            return size

    def split(self):
        part_len, remain = divmod(self.size, self.num_blocks)
        blocks = {
                i: ClosedRange(
                    begin=i * part_len,
                    end=(i + 1) * part_len - 1
                ) for i in range(self.num_blocks - 1)
            }
        blocks[self.num_blocks - 1] = ClosedRange(
            begin=(self.num_blocks - 1) * part_len,
            end=self.size - 1
        )
        return blocks

    @retry
    async def download_block(self, id):
        header = {'Range': 'bytes={}-{}'.format(*self.blocks[id])}
        async with self.session.get(self.url, headers=header) as response:
            response.raise_for_status()
            async for chunk in response.content.iter_chunked(1024):
                # Be sure that there's no 'await' between next two lines!
                self.output.seek(self.blocks[id].begin)
                self.output.write(chunk)
                self.blocks[id].begin += len(chunk)
                self.tqdm.update(len(chunk))
        del self.blocks[id]

    async def download(self):
        with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'}) as session:
            
            self.session = session
            self.size = await self.get_download_size()
            if self.num_blocks > self.size:
                LOGGER.warning(
                    'Too many blocks(%d > file size %d), use 1 block',
                    self.num_blocks, self.size
                )
                self.num_blocks = 1

            LOGGER.info("Saving to: '%s'", self.output_fname)
            with tqdm(
                disable=self.quiet,
                total=self.size, unit='B',
                unit_scale=True, unit_divisor=1024
            ) as t:
                self.tqdm = t
                if self.blocks is None:
                    self.blocks = self.split()
                    # pre-allocate file
                    with open(self.output_fname, 'wb') as f:
                        os.posix_fallocate(f.fileno(), 0, self.size)
                else:
                    t.update(
                        self.size - sum(len(v) for k, v in self.blocks.items())
                    )
                with open(self.output_fname, 'rb+') as f:
                    self.output = f
                    await asyncio.gather(*(self.download_block(k)
                                           for k, v in self.blocks.items()
                                           ))
