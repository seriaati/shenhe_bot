import asyncio
import json
import re
import aiohttp
from pyppeteer import launch
import yaml
import utility.enkaToGOOD

async def main(chara_name: str):
    print(f'calculating damage for {chara_name}')
    talent_to_calculate = ['Normal Atk.', 'Charged Atk.', 'Plunging Atk.', 'Ele. Skill', 'Ele. Burst']
    browser = await launch({"headless": True, "args": ["--start-maximized"]})
    page = await browser.newPage()
    await page.setViewport({"width": 1440, "height": 900})
    await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
    await page.waitForSelector('div.MuiCardContent-root')
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedError.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1312m7x')
    async with aiohttp.ClientSession() as cs:
        async with cs.get(f'https://enka.shinshin.moe/u/901211014/__data.json') as r:
            enka_data = await r.json()
    result = await utility.enkaToGOOD.convert(enka_data)
    json_object = json.dumps(result)
    await page.focus('textarea.MuiBox-root')
    await page.keyboard.sendCharacter(str(json_object))
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1p356oi')
    await page.click('button#dropdownbtn')
    await page.waitForSelector('ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a')
    await page.click('li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(n+2)')
    await page.goto(f"https://frzyc.github.io/genshin-optimizer/#/characters/{chara_name}/equip")
    await page.waitForSelector('span.css-t3oe3b')
    labels = await page.querySelectorAll('h6.MuiTypography-root.MuiTypography-subtitle2.css-1tv3e07') # Ele. Skill
    label_vals = []
    for l in labels:
        val = await (await l.getProperty("textContent")).jsonValue()
        label_vals.append(val)
    result = {}
    normal_attack_name = '<普通攻擊名稱>'
    dmg_type = ['avgHit', 'hit', 'critHit']
    for dmg in range(0, 3):
        await page.click(f'button[value="{dmg_type[dmg]}"]') #Avg. DMG
        for t in talent_to_calculate:
            card_index = label_vals.index(t)
            talent_name = await page.querySelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > div.MuiCardHeader-root.css-faujvq:nth-child(1) > div.MuiCardHeader-content.css-11qjisw:nth-child(2) > span.MuiTypography-root.MuiTypography-subtitle1.MuiCardHeader-title.css-slco8z > span')
            talent_name = await (await talent_name.getProperty("textContent")).jsonValue()
            print(talent_name)
            if talent_to_calculate.index(t) == 0:
                normal_attack_name = talent_name
                talent_name = f'普攻'
            elif talent_to_calculate.index(t) == 1:
                talent_name = f'重擊'
            elif talent_to_calculate.index(t) == 2:
                talent_name = f'下落攻擊'
            if dmg == 0:
                result[talent_name] = {}
            talent_rows = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > ul.MuiList-root.MuiList-padding.css-1jrq055 > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.MuiBox-root.css-1n74xce')
            for row in talent_rows:
                row = await (await row.getProperty("textContent")).jsonValue()
                split_row = re.split('([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?', row)
                talent_label = split_row[0]
                talent_damage = split_row[1]
                if dmg == 0:
                    result[talent_name][talent_label] = []
                result[talent_name][talent_label].append(talent_damage)
    await page.close()
    await browser.close()
    print(result)
    print(normal_attack_name)

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
asyncio.run(main('Shenhe'))
print('finished.')
