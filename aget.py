import asyncio
import aiohttp
import argparse
import logging
import sys
import os

from urllib.parse import urlsplit
from tqdm import tqdm

logger = logging.getLogger(__name__)


class MyError(Exception):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def save_args_into_exception(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            raise MyError(args, kwargs) from exc
    return wrapper


@save_args_into_exception
async def download_block(session, url, f, start, end, conn_id, bar):
    logger.debug('connection %d: %d -> %d', conn_id, start, end)
    header = {'Range': 'bytes={}-{}'.format(start, end)}
    async with session.get(url, headers=header) as response:
        response.raise_for_status()
        async for chunk in response.content.iter_chunked(1024):
            # Be sure there's no 'await' between next two lines!
            f.seek(start)
            f.write(chunk)
            start += len(chunk)
            bar.update(len(chunk))
    logger.info('connection %d done', conn_id)


async def get_download_size(session, url):
    async with session.head(url) as response:
        return int(response.headers['Content-Length'])


async def main(url, output, num_connections):
    with open(output, 'wb') as f, aiohttp.ClientSession() as session:
        size = await get_download_size(session, url)
        if num_connections > size:
            logger.warn(
                'num_connections(%d) > file size(%d)! Using one.',
                num_connections, size
            )
            num_connections = 1
        # pre-allocate file
        os.posix_fallocate(f.fileno(), 0, size)
        with tqdm(
            desc=output, total=size, unit='B',
            unit_scale=True, unit_divisor=1024
        ) as bar:
            part_len, remain = divmod(size, num_connections)
            tasks = [
                download_block(
                    session, url, f,
                    i * part_len, (i + 1) * part_len - 1, i, bar
                ) for i in range(num_connections - 1)
            ] + [
                download_block(
                    session, url, f, (num_connections - 1) * part_len,
                    size - 1, num_connections - 1, bar
                )
            ]

            while tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                failed = [i for i in results if isinstance(i, MyError)]
                if failed:
                    logger.info('%d connections failed, retrying', len(failed))
                tasks = [download_block(*i.args) for i in failed]


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='async downloader')
    ap.add_argument('url', help='URL to download')
    ap.add_argument('--output', '-o', required=False, help='output file')
    ap.add_argument(
        '--num-connections', '-n', type=int, required=False,
        default=16, help='number of connections'
    )
    ap.add_argument(
        '-v', '--verbose', action='count', dest='level',
        default=2, help='Verbose logging (repeat for more verbose)')
    ap.add_argument(
        '-q', '--quiet', action='store_const', const=0, dest='level',
        default=2, help='Only log errors')
    args = ap.parse_args()
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(args.level, len(levels)-1)])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        main(
            url=args.url,
            output=args.output or os.path.basename(urlsplit(args.url).path),
            num_connections=args.num_connections
        )
    )
