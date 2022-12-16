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

def get_dice_element(element: str) -> str:
    return dice_element.get(element, "Unknown")