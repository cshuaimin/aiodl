import argparse
import asyncio

from .__init__ import download


def main():
    ap = argparse.ArgumentParser(
        description='Aiodl -- Yet another command line download accelerator.'
    )

    ap.add_argument('url', metavar='URL', help='URL to download')
    ap.add_argument(
        '--output', '-o', help='Output filename.'
    )
    ap.add_argument('--fake-user-agent', '-u', action='store_true',
                    help='Use a fake User-Agent.')
    ap.add_argument(
        '--num-tasks', '-n', type=int, metavar='N', default=16,
        help='Limit number of asynchronous tasks.'
    )
    ap.add_argument(
        '--max-tries', '-r', type=int, metavar='N', default=10,
        help='Limit retries on network errors.'
    )
    ap.add_argument('--quiet', '-q', action='store_true', default=False,
                    help='Displays or disables the progress bar.')

    args = ap.parse_args()
    try:
        asyncio.get_event_loop().run_until_complete(download(**vars(args)))
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    main()
