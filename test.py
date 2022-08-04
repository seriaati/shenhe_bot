import asyncio
from enkanetwork import EnkaNetworkAPI
from pyppeteer import launch

from apps.genshin.damage_calculator import DamageCalculator

async def main():
    client = EnkaNetworkAPI()
    data = await client.fetch_user(901211014)
    browser=await launch({'headless': False, 'autoClose': False, "args": ['--proxy-server="direct://"', '--proxy-bypass-list=*', '--no-sandbox', '--start-maximized']})
    calculator = DamageCalculator(data, browser, '10000002', 'zh-TW', 'critHit', None, 'vaporize', 'pyro', ['10000030'])
    await calculator.run()
    
loop = asyncio.get_event_loop()
loop.run_until_complete(main())