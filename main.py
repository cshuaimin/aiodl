import asyncio
import pickle
import argparse
import logging
import os

from urllib.parse import urlsplit
from termcolor import colored
from aget import Download, AgetQuitError

LOGGER = logging.getLogger(__name__)


def main():
    ap = argparse.ArgumentParser(
        description='Download files asynchronously in a single thread!'
    )

    ap.add_argument('url', help='URL to download')
    ap.add_argument(
        '--output', '-o', help='output file'
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
        '--quiet', '-q', action='store_true',
        help='only log errors'
    )
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.INFO,
        format=colored('%(levelname)s', 'cyan') + '\t%(message)s'
    )
    output = args.output or os.path.basename(urlsplit(args.url).path)
    status_file = output + '.aget_st'
    if os.path.exists(status_file):
        LOGGER.info('using status file %s', status_file)
        with open(status_file, 'rb') as f:
            blocks = pickle.load(f)
    else:
        blocks = None
    download = Download(
        url=args.url,
        output_fname=output,
        num_blocks=args.num_blocks,
        blocks=blocks,
        max_retries=args.max_retries,
        quiet=args.quiet
    )

    try:
        asyncio.get_event_loop().run_until_complete(download.download())
    except AgetQuitError:
        LOGGER.error('Quiting...')
    except KeyboardInterrupt:
        LOGGER.info('saving status to %s', status_file)
        with open(status_file, 'wb') as f:
            pickle.dump(download.blocks, f)
    else:
        if blocks is not None:
            LOGGER.info(
                'downloading completed, removing status file %s',
                status_file
            )
            os.remove(status_file)

if __name__ == '__main__':
    main()
