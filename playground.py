import asyncio
import json
from pyppeteer import launch
import yaml
from utility.enkaToGOOD import convert


async def browser():
    chara_name = 'Yelan'
    talent_to_calculate = 'Ele. Burst'
    browser = await launch({"headless": True, "args": ["--start-maximized"]})
    page = await browser.newPage()
    await page.setViewport({"width": 1440, "height": 900})
    await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
    await page.waitForSelector('div.MuiCardContent-root')
    result = await convert(901211014)
    json_object = json.dumps(result) 
    await page.focus('textarea.MuiBox-root')
    await page.keyboard.sendCharacter(str(json_object))
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1p356oi')
    await page.click('button#dropdownbtn')
    await page.waitForSelector('ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a')
    await page.click('li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(n+2)')
    await page.waitFor(1000)
    await page.goto(f"https://frzyc.github.io/genshin-optimizer/#/characters/{chara_name}/equip")
    await page.waitForSelector('span.css-t3oe3b')
    labels = await page.querySelectorAll('h6.MuiTypography-root.MuiTypography-subtitle2.css-1tv3e07')
    label_vals = []
    for l in labels:
        val = await (await l.getProperty("textContent")).jsonValue()
        label_vals.append(val)
    index = label_vals.index(talent_to_calculate)
    talent_name = await page.querySelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({index})>div.MuiCardHeader-root.css-faujvq>div.MuiCardHeader-content.css-11qjisw')
    print(await (await talent_name.getProperty("textContent")).jsonValue())
    talent_labels = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({index})>div.MuiCardContent-root.css-nph2fg>div.MuiBox-root.css-1tvhq2w>p.MuiTypography-root.MuiTypography-body1:nth-child(1)')
    talent_numbers = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({index})>div.MuiCardContent-root.css-nph2fg>div.MuiBox-root.css-1tvhq2w>p.MuiTypography-root.MuiTypography-body1:nth-child(2)')
    for i in range(0, len(talent_labels)):
        print(await (await talent_labels[i].getProperty("textContent")).jsonValue())
        print(await (await talent_numbers[i].getProperty("textContent")).jsonValue())

async def data():
    with open('GenshinData/EN_simple_textMap.yaml', 'r', encoding='utf-8') as f:
        en = yaml.full_load(f)
    with open('GenshinData/TW_simple_textMap.yaml', 'r', encoding='utf-8') as f:
        tw = yaml.full_load(f)
    with open('GenshinData/EN_full_textMap.json', 'r', encoding='utf-8') as f:
        full_en = json.load(f)
    with open('GenshinData/TW_full_textMap.json', 'r', encoding='utf-8') as f:
        full_tw = json.load(f)
    with open('GenshinData/art_set_excel.json', 'r', encoding='utf-8') as f:
        rel = json.load(f)
    with open('GenshinData/affix_excel.json', 'r', encoding='utf-8') as f:
        affix = json.load(f)
    
    for set in rel:
        id = set['setId']
        print(id)
        for a in affix:
            if set['EquipAffixId'] == a['id']:
                en[id] = full_en.get(str(a['nameTextMapHash']))
                print(en[id])
                tw[id] = full_tw.get(str(a['nameTextMapHash']))
                print(tw[id])
                break
    
    with open('GenshinData/EN_simple_textMap.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(en, f)
    with open('GenshinData/TW_simple_textMap.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(tw, f)

print('starting...')
asyncio.run(browser())
print('finished.')
