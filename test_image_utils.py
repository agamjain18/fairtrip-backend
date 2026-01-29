
import asyncio
from utils.image_utils import get_famous_spot_image

async def test_image():
    destinations = ["Paris", "Tokyo", "Agra", "New York", "London"]
    for dest in destinations:
        url = await get_famous_spot_image(dest)
        print(f"Destination: {dest} -> Image Link: {url}")

if __name__ == "__main__":
    asyncio.run(test_image())
