from random import random
import time
import requests
import asyncio


async def do_something_async():
    await asyncio.sleep(random() * 5)
    print("async task done!")
    pass

async def async_main():
    tasks = []
    for i in range(10):
        tasks.append(do_something_async())
    await asyncio.gather(*tasks)


asyncio.run(async_main())

