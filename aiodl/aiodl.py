"""An asynchronous downloader -- class implementing downloading logic."""

import asyncio
import aiohttp
import functools
import shelve
import os

from tqdm import tqdm

from .color import print_colored_kv
from .__version__ import __version__

class AiodlQuitError(Exception):
    'Something caused aiodl to quit.'


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
    def __init__(self, url, output_fname, num_blocks, max_tries):
        self.url = url
        self.output_fname = output_fname
        self.num_blocks = num_blocks
        self.max_tries = max_tries
        self.status_file = output_fname + '.aiodl'
        loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': 'Aiodl/' + __version__},
            loop=loop
        )

    def retry(coro_func):
        @functools.wraps(coro_func)
        async def wrapper(self, *args, **kwargs):
            tried = 0
            while True:
                tried += 1
                try:
                    return await coro_func(self, *args, **kwargs)
                except aiohttp.ClientError as exc:
                    try:
                        msg = '%d %s' % (exc.code, exc.message)
                        # For 4xx client errors, it's no use to try again :)
                        if 400 <= exc.code < 500:
                            tqdm.write(msg)
                            raise AiodlQuitError from exc
                    except AttributeError:
                        msg = str(exc) or msg.__class__.__name__
                    if tried <= self.max_tries:
                        sec = tried / 2
                        tqdm.write(
                            '%s() failed: %s, retry in %.1f seconds (%d/%d)' %
                            (coro_func.__name__, msg,
                             sec, tried, self.max_tries)
                        )
                        await asyncio.sleep(sec)
                    else:
                        tqdm.write(
                            '%s() failed after %d tries: %s ' %
                            (coro_func.__name__, self.max_tries, msg)
                        )
                        raise AiodlQuitError from exc
                except asyncio.TimeoutError:
                    # Usually server has a fixed TCP timeout to clean dead
                    # connections, so you can see a lot of timeouts appear
                    # at the same time. I don't think this is an error,
                    # So retry it without checking the max retries.
                    tqdm.write(
                        '%s() timeout, retry in 1 second' % coro_func.__name__)
                    await asyncio.sleep(1)
        return wrapper

    @retry
    async def get_download_info(self):
        async with self.session.head(
            # Default `allow_errorirects` for the head method is set to False,
            # but it's common to download something from a non-direct link,
            # eg. the errorirect from HTTP to HTTPS.
            self.url, allow_redirects=True
        ) as response:
            response.raise_for_status()
            # Use redirected URL
            self.url = str(response.url)

            return (
                int(response.headers['Content-Length']),
                response.headers['Content-Type']
            )

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
            async for chunk in response.content.iter_chunked(1024 * 1024):
                # Be sure that there's no 'await' between next two lines!
                self.output.seek(self.blocks[id].begin)
                self.output.write(chunk)
                self.blocks[id].begin += len(chunk)
                self.bar.update(len(chunk))
        del self.blocks[id]

    async def download(self):
        tqdm.write('')
        if os.path.exists(self.status_file):
            with shelve.open(self.status_file) as db:
                self.size = db['size']
                self.blocks = db['blocks']
                self.content_type = db['type']
            downloaded_size = self.size - sum(
                len(r) for r in self.blocks.values()
            )
            # 'r+b' -- opens the file for binary random access,
            # without truncates it to 0 byte (which 'w+b' does)
            self.output = open(self.output_fname, 'r+b')
        else:
            self.size, self.content_type = await self.get_download_info()
            if self.num_blocks > self.size:
                tqdm.write(
                    'Too many blocks (%d > file size %d), using 1 block' %
                    (self.num_blocks, self.size)
                )
                self.num_blocks = 1
            self.blocks = self.split()
            downloaded_size = 0
            self.output = open(self.output_fname, 'wb')
            # pre-allocate file
            os.posix_fallocate(self.output.fileno(), 0, self.size)

        print_colored_kv('File', self.output_fname)
        formatted_size = tqdm.format_sizeof(self.size)
        if downloaded_size:
            formatted_size += ' (already downloaded {})'.format(
                tqdm.format_sizeof(downloaded_size))
        print_colored_kv('Size', formatted_size)
        print_colored_kv('Type', self.content_type)
        tqdm.write('')

        self.bar = tqdm(
            initial=downloaded_size,
            dynamic_ncols=True,  # Suitable for window resizing
            total=self.size,
            unit='B', unit_scale=True, unit_divisor=1024
        )

        await asyncio.gather(
            *(self.download_block(id) for id in self.blocks)
        )

    def close(self):
        self.session.close()
        try:
            self.output.close()
            self.bar.close()
        except AttributeError:
            pass

        # if self has 'blocks', and blocks is not empty
        if getattr(self, 'blocks', None):
            tqdm.write('Saving status to %s' % self.status_file)
            with shelve.open(self.status_file) as db:
                db['size'] = self.size
                db['blocks'] = self.blocks
                db['type'] = self.content_type
        elif os.path.exists(self.status_file):
            #  tqdm.write(
            #      'downloading completed, removing status file %s' %
            #      self.status_file
            #  )
            os.remove(self.status_file)
