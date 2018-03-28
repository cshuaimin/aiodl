from fake_useragent import UserAgent

from .aiodl import Download


async def download(url, output=None, num_tasks=16,
                   max_tries=10, fake_user_agent=False, *, loop=None):

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
        loop=loop
    )
    try:
        return await d.download()
    finally:
        await d.close()
        # next two lines are required for actual aiohttp resource cleanup
        loop.stop()
        loop.run_forever()
