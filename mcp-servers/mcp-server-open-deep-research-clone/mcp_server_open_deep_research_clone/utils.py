import aiohttp


async def fetch_url(image_url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            response.raise_for_status()
            return await response.read()
