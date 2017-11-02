"""An asynchronous downloader -- class implementing downloading logic."""

import asyncio
import aiohttp
import pickle
import urllib.parse
import cgi
import os

from tqdm import tqdm

from .version import __version__
from .utils import (
    print_colored_kv,
    ClosedRange,
    retry,
    connecting
)


class Download:
    def __init__(self, url, output_fname=None, num_tasks=16,
                 max_tries=10, user_agent=None, *, loop=None):
        self.url = url
        self.output_fname = output_fname
        self.num_tasks = num_tasks
        self.max_tries = max_tries
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': user_agent or 'Aiodl/' + __version__},
            loop=loop or asyncio.get_event_loop()
        )

    @retry
    async def get_download_info(self):
        async with self.session.head(
            # Default `allow_redirects` for the head method is set to False,
            # but it's common to download something from a non-direct link,
            # eg. the redirect from HTTP to HTTPS.
            self.url, allow_redirects=True
        ) as response:
            response.raise_for_status()
            # Use redirected URL
            self.url = str(response.url)

            try:
                content_disposition = cgi.parse_header(
                    response.headers['Content-Disposition'])
                filename = content_disposition[1]['filename']
                filename = urllib.parse.unquote_plus(filename)
            except KeyError:
                filename = None
            return (
                filename,
                int(response.headers['Content-Length']),
                response.headers['Content-Type']
            )

    def split(self):
        part_len, remain = divmod(self.size, self.num_tasks)
        blocks = {
                i: ClosedRange(
                    begin=i * part_len,
                    end=(i + 1) * part_len - 1
                ) for i in range(self.num_tasks - 1)
            }
        blocks[self.num_tasks - 1] = ClosedRange(
            begin=(self.num_tasks - 1) * part_len,
            end=self.size - 1
        )
        return blocks

    @retry
    async def download_block(self, id):
        header = {'Range': 'bytes={}-{}'.format(*self.blocks[id])}
        async with self.session.get(self.url, headers=header) as response:
            response.raise_for_status()
            async for chunk in response.content.iter_any():
                # Be sure that there's no 'await' between next two lines!
                self.output.seek(self.blocks[id].begin)
                self.output.write(chunk)
                self.blocks[id].begin += len(chunk)
                self.bar.update(len(chunk))
        del self.blocks[id]


    async def download(self):
        with connecting():
            filename, self.size, file_type = await self.get_download_info()

        if not self.output_fname:
            self.output_fname = filename
        if not self.output_fname:
            parts = urllib.parse.urlparse(self.url)
            self.output_fname = os.path.basename(parts.path)
        if not self.output_fname:
            tqdm.write('Unable to resolve file name from HTTP header and URL.'
                       'Please use the "-o" parameter.')
            return 1
        self.status_file = self.output_fname + '.aiodl'

        if os.path.exists(self.status_file):
            with open(self.status_file, 'rb') as f:
                self.blocks = pickle.load(f)
            downloaded_size = self.size - sum(
                r.size for r in self.blocks.values()
            )
            # 'r+b' -- opens the file for binary random access,
            # without truncates it to 0 byte (which 'w+b' does)
            self.output = open(self.output_fname, 'r+b')
        else:
            if self.num_tasks > self.size:
                tqdm.write(
                    'Too many tasks (%d > file size %d), using 1 task' %
                    (self.num_tasks, self.size)
                )
                self.num_tasks = 1
            self.blocks = self.split()
            downloaded_size = 0
            self.output = open(self.output_fname, 'wb')
            # pre-allocate file
            try:
                os.posix_fallocate(self.output.fileno(), 0, self.size)
            except OSError:
                pass

        print_colored_kv('File', self.output_fname)
        formatted_size = tqdm.format_sizeof(self.size, 'B', 1024)
        if downloaded_size:
            formatted_size += ' (already downloaded {})'.format(
                tqdm.format_sizeof(downloaded_size, 'B', 1024))
        print_colored_kv('Size', formatted_size)
        print_colored_kv('Type', file_type)
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
            if self.blocks:
                tqdm.write('Saving status to %s' % self.status_file)
                with open(self.status_file, 'wb') as f:
                    pickle.dump(self.blocks, f)
            elif os.path.exists(self.status_file):
                os.remove(self.status_file)
        except AttributeError:
            pass
