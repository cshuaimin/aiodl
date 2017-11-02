import asyncio
import argparse
import sys

from fake_useragent import UserAgent

from .aiodl import Download
from .utils import AiodlQuitError


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

    args = ap.parse_args()
    if args.fake_user_agent:
        user_agent = UserAgent().random
    else:
        user_agent = None
    loop = asyncio.get_event_loop()
    d = Download(
        url=args.url,
        output_fname=args.output,
        num_tasks=args.num_tasks,
        max_tries=args.max_tries,
        user_agent=user_agent,
        loop=loop
    )
    try:
        return loop.run_until_complete(d.download())
    except (KeyboardInterrupt, AiodlQuitError):
        pass
    finally:
        d.close()
        # next two lines are required for actual aiohttp resource cleanup
        loop.stop()
        loop.run_forever()


if __name__ == '__main__':
    sys.exit(main())
