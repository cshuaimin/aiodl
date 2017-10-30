import asyncio
import argparse
import logging
import urllib
import os

from termcolor import colored

from .aiodl import Download, AiodlQuitError

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
        '--num-blocks', '-n', type=int, metavar='N', default=16,
        help='number of blocks'
    )
    ap.add_argument(
        '--max-tries', '-r', type=int, metavar='N', default=10,
        help='limit retries on network errors'
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
    if args.output:
        output = args.output
    else:
        parts = urllib.parse.urlparse(args.url)
        output = os.path.basename(parts.path)
    if not output:
        LOGGER.error('The file name can not be parsed from the URL. '
                     'Please use the "-o" parameter.')
        exit(1)

    d = Download(
        url=args.url,
        output_fname=output,
        num_blocks=args.num_blocks,
        max_tries=args.max_tries,
    )
    try:
        asyncio.get_event_loop().run_until_complete(d.download())
    except (KeyboardInterrupt, AiodlQuitError):
        pass
    finally:
        d.close()


if __name__ == '__main__':
    main()
