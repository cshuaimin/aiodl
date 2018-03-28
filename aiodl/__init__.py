import asyncio

from fake_useragent import UserAgent

from .aiodl import Download


async def download(url, output=None, num_tasks=16, max_tries=10,
                   fake_user_agent=False, quiet=False, *, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    if fake_user_agent:
        user_agent = UserAgent().random
    else:
        user_agent = None
    d = Download(
        url=url,
        output_fname=output,
        num_tasks=num_tasks,
        max_tries=max_tries,
        user_agent=user_agent,
        quiet=quiet,
        loop=loop
    )
    try:
        return await d.download()
    finally:
        await d.close()
