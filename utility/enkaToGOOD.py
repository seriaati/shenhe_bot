import utility.utils
async def convert(enka_data):
    good_dict = {
        'format': 'GOOD',
        'version': 1,
        'source': '申鶴 • 忘玄',
        'weapons': [],
        'artifacts': [],
        'characters': []
    }
    weapon_id = 0
    art_id = 0
    for chara in enka_data['avatarInfoList']:
        id = chara['avatarId']
        chara_key = (utility.utils.get_name.getName(id, True)).replace(' ', '') or chara_key
        level = chara['propMap']['4001']['val']
        constellation = 0 if 'talentIdList' not in chara else len(
            chara['talentIdList'])
        ascention = chara['propMap']['1002']['val']
        talents = chara['skillLevelMap']
        if id == 10000002:  # 神里綾華
            talent = {
                'auto': int(talents['10024']),
                'skill': int(talents['10018']),
                'burst': int(talents['10019'])
            }
        elif id == 10000041:  # 莫娜
            talent = {
                'auto': int(talents['10411']),
                'skill': int(talents['10412']),
                'burst': int(talents['10415'])
            }
        else:
            talent = {
                'auto': int(list(talents.values())[0]),
                'skill': int(list(talents.values())[1]),
                'burst': int(list(talents.values())[2]),
            }
        good_dict['characters'].append(
            {
                'key': chara_key,
                'level': int(level),
                'constellation': int(constellation),
                'ascention': int(ascention),
                'talent': talent
            }
        )
        for e in chara['equipList']:
            if 'weapon' in e:
                weapon_id += 1
                key = (utility.utils.get_name.getNameTextHash(e['flat']['nameTextMapHash'], True)).replace("'", '').title().replace(' ','')
                level = e['weapon']['level']
                ascension = e['weapon']['promoteLevel'] if 'promoteLevel' in e['weapon'] else 0
                refinement = list(e['weapon']['affixMap'].values())[0]+1
                location = chara_key
                good_dict['weapons'].append(
                    {
                        'key': key,
                        'level': level,
                        'ascension': ascension,
                        'refinement': refinement,
                        'location': location,
                        'id': weapon_id
                    }
                )
            else:
                art_id += 1
                artifact_pos = {
                    'EQUIP_BRACER': 'flower',
                    'EQUIP_NECKLACE': 'plume',
                    'EQUIP_SHOES': 'sands',
                    'EQUIP_RING': 'goblet',
                    'EQUIP_DRESS': 'circlet'
                }
                stats = {
                    'FIGHT_PROP_HP': 'hp',
                    'FIGHT_PROP_HP_PERCENT': 'hp_',
                    'FIGHT_PROP_ATTACK': 'atk',
                    'FIGHT_PROP_ATTACK_PERCENT': 'atk_',
                    'FIGHT_PROP_DEFENSE': 'def',
                    'FIGHT_PROP_DEFENSE_PERCENT': 'def_',
                    'FIGHT_PROP_CHARGE_EFFICIENCY': 'enerRech_',
                    'FIGHT_PROP_ELEMENT_MASTERY': 'eleMas',
                    'FIGHT_PROP_CRITICAL': 'critRate_',
                    'FIGHT_PROP_CRITICAL_HURT': 'critDMG_',
                    'FIGHT_PROP_HEAL_ADD': 'heal_',
                    'FIGHT_PROP_FIRE_ADD_HURT': 'pyro_dmg_',
                    'FIGHT_PROP_ELEC_ADD_HURT': 'electro_dmg_',
                    'FIGHT_PROP_ICE_ADD_HURT': 'cryo_dmg_',
                    'FIGHT_PROP_WATER_ADD_HURT': 'hydro_dmg_',
                    'FIGHT_PROP_WIND_ADD_HURT': 'anemo_dmg_',
                    'FIGHT_PROP_ROCK_ADD_HURT': 'geo_dmg_',
                    'FIGHT_PROP_GRASS_ADD_HURT': 'dendro_dmg_',
                    'FIGHT_PROP_PHYSICAL_ADD_HURT': 'physical_dmg_'
                }
                setKey = (utility.utils.get_name.getNameTextHash(e['flat']['setNameTextMapHash'], True).replace("'", '').title().replace(' ', '')) or e['flat']['setNameTextMapHash']
                slotKey = artifact_pos.get(e['flat']['equipType'])
                rarity = e['flat']['rankLevel']
                mainStatKey = stats.get(
                    e['flat']['reliquaryMainstat']['mainPropId'])
                level = e['reliquary']['level']-1
                substats = []
                for sub_stat in e['flat']['reliquarySubstats']:
                    substats.append({
                        'key': stats.get(sub_stat['appendPropId']),
                        'value': sub_stat['statValue']
                    })
                good_dict['artifacts'].append(
                    {
                        'setKey': setKey,
                        'slotKey': slotKey,
                        'rarity': rarity,
                        'mainStatKey': mainStatKey,
                        'level': level,
                        'substats': substats,
                        'location': chara_key,
                        'lock': True,
                        'id': art_id
                    }
                )
    return good_dict
