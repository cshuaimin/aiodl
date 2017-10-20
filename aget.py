import asyncio
import aiohttp
import logging
import functools
import os

from tqdm import tqdm
from aiohttp.client_exceptions import ClientError

LOGGER = logging.getLogger(__name__)


class MaxRetryReachedError(Exception):
    'The maximum number of retries has been reached!'


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
    def __init__(self, url, output_fname, num_blocks, blocks, max_retries):
        self.url = url
        self.output_fname = output_fname
        self.num_blocks = num_blocks
        self.max_retries = max_retries
        self.blocks = blocks

    def retry(coro_func):
        @functools.wraps(coro_func)
        async def wrapper(self, *args, **kwargs):
            tried = 0
            while True:
                tried += 1
                try:
                    return await coro_func(self, *args, **kwargs)
                except (ClientError, asyncio.TimeoutError) as exc:
                    msg = str(exc) or exc.__class__.__name__
                    if tried <= self.max_retries:
                        LOGGER.warning(
                            '%s() failed: %s, retrying %d/%d',
                            coro_func.__name__, msg, tried, self.max_retries
                        )
                    else:
                        LOGGER.error(
                            '%s() failed: %s, max retry exceeded!',
                            coro_func.__name__, msg
                        )
                        raise MaxRetryReachedError from exc
        return wrapper

    @retry
    async def get_download_size(self):
        async with self.session.head(self.url) as response:
            response.raise_for_status()
            return int(response.headers['Content-Length'])

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
        LOGGER.debug('block %d: %s done', id, self.blocks[id])
        del self.blocks[id]

    async def download(self):
        with aiohttp.ClientSession() as session:
            self.session = session
            try:
                self.size = await self.get_download_size()
            except MaxRetryReachedError:
                LOGGER.error('quit')
                return
            if self.num_blocks > self.size:
                LOGGER.error(
                    'Too many blocks(%d > file size %d)!',
                    self.num_blocks, self.size
                )
                return

            with tqdm(
                total=self.size, unit='B',
                unit_scale=True, unit_divisor=1024
            ) as t:
                self.tqdm = t
                if self.blocks is None:
                    self.blocks = self.split()
                    with open(self.output_fname, 'wb') as f:
                        # pre-allocate file
                        os.posix_fallocate(f.fileno(), 0, self.size)
                else:
                    t.update(self.size - sum(len(v) for k, v in self.blocks.items()))
                with open(self.output_fname, 'rb+') as f:
                    self.output = f
                    try:
                        await asyncio.gather(*(self.download_block(k)
                                               for k, v in self.blocks.items()
                                               ))
                    except MaxRetryReachedError:
                        LOGGER.error('quit')
