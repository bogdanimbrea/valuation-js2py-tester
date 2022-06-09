import asyncio
import aiohttp
import json
import os


async def gather_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def get_async(url, session):
    # use GET instead of POST
    async with session.get(url) as response:
        text = await response.text()
        print(text)
        return json.loads(text)


async def main(urls):
    conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=conn)
    conc_req = len(urls)
    responses = await gather_with_concurrency(conc_req, *[get_async(url, session) for url in urls])
    await session.close()
    print(responses)
    return responses

income_url = "https://financialmodelingprep.com/api/v3/income-statement/INTC/?apikey=" + os.environ.get('FMP_KEY')
profile_url = "https://financialmodelingprep.com/api/v3/profile/INTC?apikey=" + os.environ.get('FMP_KEY')
quote_url = "https://financialmodelingprep.com/api/v3/quote/INTC?apikey=" + os.environ.get('FMP_KEY')
urls = [income_url, profile_url]
responses = asyncio.get_event_loop().run_until_complete(main(urls))
print("Done")
