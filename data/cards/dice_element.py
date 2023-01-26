dice_element = {
    "GCG_COST_ENERGY": "Energy",
    "GCG_COST_DICE_VOID": "Black",
    "GCG_COST_DICE_SAME": "Omni",
    "GCG_COST_DICE_CRYO": "Cryo",
    "GCG_COST_DICE_HYDRO": "Hydro",
    "GCG_COST_DICE_PYRO": "Pyro",
    "GCG_COST_DICE_ELECTRO": "Electro",
    "GCG_COST_DICE_ANEMO": "Anemo",
    "GCG_COST_DICE_GEO": "Geo",
    "GCG_COST_DICE_DENDRO": "Dendro",
}

dice_emoji = {
    "GCG_COST_ENERGY": "<:UI_Gcg_DiceL_Energy:1054218252668108820>",
    "GCG_COST_DICE_VOID": "<:UI_Gcg_DiceL_Diff_Glow:1054218256870805565>",
    "GCG_COST_DICE_SAME": "<:UI_Gcg_DiceL_Any_Glow:1054218258737278976>",
    "GCG_COST_DICE_CRYO": "<:UI_Gcg_DiceL_Ice_Glow:1054218246619930644>",
    "GCG_COST_DICE_HYDRO": "<:UI_Gcg_DiceL_Water_Glow:1054218240487850115>",
    "GCG_COST_DICE_PYRO": "<:UI_Gcg_DiceL_Fire_Glow:1054218250747117689>",
    "GCG_COST_DICE_ELECTRO": "<:UI_Gcg_DiceL_Electric_Glow:1054218254903681098>",
    "GCG_COST_DICE_ANEMO": "<:UI_Gcg_DiceL_Wind_Glow:1054218238566879336>",
    "GCG_COST_DICE_GEO": "<:UI_Gcg_DiceL_Rock_Glow:1054218244656992286>",
    "GCG_COST_DICE_DENDRO": "<:UI_Gcg_DiceL_Grass_Glow:1054218248477999135>",
}


def get_dice_element(element: str) -> str:
    return dice_element.get(element, "Unknown")


def get_dice_emoji(element: str) -> str:
    return dice_emoji.get(element, "<:UI_Gcg_DiceL_Any_Glow:1054218258737278976>")
