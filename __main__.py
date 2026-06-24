import logging

from src.app import App

import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)

async def main():
    app: App = App()
    await app.launch()
    
    
asyncio.run(main())
    
    
