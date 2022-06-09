import asyncio
import json
from pyppeteer import launch
import yaml
from utility.enkaToGOOD import convert

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
asyncio.run(data())
print('finished.')
