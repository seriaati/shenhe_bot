import asyncio
from typing import Dict

from pyppeteer import launch
from pyppeteer.browser import Browser

from apps.text_map import GENSHIN_OPTIMIZER_LANGS


async def launch_browsers() -> Dict[str, Browser]:
    result = {}
    for key, value in GENSHIN_OPTIMIZER_LANGS.items():
        browser = await launch({"headless": True, "args": ["--no-sandbox"]})
        page = await browser.newPage()
        await page.setViewport({"width": 1440, "height": 900})
        await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
        lang_dropdown = "button#dropdownbtn.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.css-z7p9wm"
        await page.waitForSelector(lang_dropdown)
        if key != "en-US":
            await page.click(lang_dropdown)
            await asyncio.sleep(0.5)
            await page.click(
                f"div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.css-16nqea3 > div > ul.MuiList-root.MuiList-padding.css-1925rlh > li.MuiButtonBase-root.MuiMenuItem-root.MuiMenuItem-gutters.css-szd4wn:nth-child({value})"
            )
        await page.close()
        result[key] = browser
    return result


def get_browser(browsers: Dict[str, Browser], locale: str) -> Browser:
    result = browsers.get(locale)
    if result is None:
        return browsers["en-US"]
    return result


async def launch_debug_browser() -> Browser:
    browser = await launch({"headless": True, "args": ["--no-sandbox"]})
    return browser
