import asyncio
from typing import Dict

from pyppeteer import launch
from pyppeteer.browser import Browser

from apps.text_map.convert_locale import to_go_dict


async def launch_browsers() -> Dict[str, Browser]:
    result = {}
    for key, value in to_go_dict.items():
        browser = await launch({"headless": True, "args": ["--no-sandbox"]})
        page = await browser.newPage()
        await page.setViewport({"width": 1440, "height": 900})
        await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
        await page.waitForSelector(
            "div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-17asib0 > div.MuiCardContent-root.css-nph2fg:nth-child(3) > div.MuiBox-root.css-10egq61 > div.MuiBox-root.css-0:nth-child(2) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-qqlytg:nth-child(2) > span.MuiButton-root.MuiButton-contained.MuiButton-containedInfo.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-1garcay"
        )
        if key != "en-US":
            await page.click(
                "div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu:nth-child(1) > div.MuiCardContent-root.css-nph2fg:nth-child(3) > button#dropdownbtn.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-z7p9wm"
            )
            await asyncio.sleep(0.5)
            await page.click(
                f"div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child({value})"
            )
        await page.close()
        result[key] = browser
    return result


def get_browser(browsers: Dict[str, Browser], locale: str) -> Browser:
    result = browsers.get(locale)
    if result is None:
        return browsers.get("en-US")
    else:
        return result
