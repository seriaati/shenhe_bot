dice_element = {
    "1": "Energy",
    "10": "Black",
    "3": "Omni",
    "11": "Cryo",
    "12": "Hydro",
    "13": "Pyro",
    "14": "Electro",
    "17": "Anemo",
    "15": "Geo",
    "16": "Dendro",
}

dice_emoji = {
    "1": "<:UI_Gcg_DiceL_Energy:1054218252668108820>",
    "3": "<:UI_Gcg_DiceL_Any_Glow:1054218258737278976>",
    "10": "<:UI_Gcg_DiceL_Diff_Glow:1054218256870805565>",
    "11": "<:UI_Gcg_DiceL_Ice_Glow:1054218246619930644>",
    "12": "<:UI_Gcg_DiceL_Water_Glow:1054218240487850115>",
    "13": "<:UI_Gcg_DiceL_Fire_Glow:1054218250747117689>",
    "14": "<:UI_Gcg_DiceL_Electric_Glow:1054218254903681098>",
    "17": "<:UI_Gcg_DiceL_Wind_Glow:1054218238566879336>",
    "15": "<:UI_Gcg_DiceL_Rock_Glow:1054218244656992286>",
    "16": "<:UI_Gcg_DiceL_Grass_Glow:1054218248477999135>",
}


def get_dice_element(element: str) -> str:
    return dice_element.get(element, "Unknown")


def get_dice_emoji(element: str) -> str:
    return dice_emoji.get(element, "<:UI_Gcg_DiceL_Any_Glow:1054218258737278976>")
