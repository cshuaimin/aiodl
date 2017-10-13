import asyncio
import argparse
import logging
import os

from urllib.parse import urlsplit
from aget import Download

LOGGER = logging.getLogger(__name__)

def main():
    ap = argparse.ArgumentParser(
        description='Download files asynchronously in a single thread!'
    )

    ap.add_argument('url', help='URL to download')
    ap.add_argument(
        '--output', '-o', type=argparse.FileType('wb'), help='output file'
    )
    ap.add_argument(
        '--num-blocks', '-n', type=int, default=16,
        help='number of blocks'
    )
    ap.add_argument(
        '--max-retries', '-r', type=int, default=8,
        help='number of retries'
    )
    ap.add_argument(
        '--verbose', '-v', action='count', dest='level', default=2,
        help='verbose logging (repeat for more verbose)')
    ap.add_argument(
        '--quiet', '-q', action='store_const', const=0, dest='level',
        default=2, help='only log errors')

    args = ap.parse_args()
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(args.level, len(levels)-1)])

    output = args.output or open(
        os.path.basename(urlsplit(args.url).path),
        'wb'
    )
    LOGGER.info('saving to %s ...', output.name)
    download = Download(
        url=args.url,
        output=output,
        num_blocks=args.num_blocks,
        max_retries=args.max_retries
    )

    asyncio.get_event_loop().run_until_complete(download.download())

if __name__ == '__main__':
    main()
