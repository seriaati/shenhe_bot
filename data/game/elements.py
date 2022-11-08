elements = {
    'Wind': '<:WIND_ADD_HURT:982138235239137290>',
    'Ice': '<:ICE_ADD_HURT:982138229140635648>',
    'Electric': '<:ELEC_ADD_HURT:982138220248711178>',
    'Rock': '<:ROCK_ADD_HURT:982138232391237632>',
    'Water': '<:WATER_ADD_HURT:982138233813098556>',
    'Fire': '<:FIRE_ADD_HURT:982138221569900585>',
    'Grass': '<:GRASS_ADD_HURT:982138222891110432>'
}

element_emojis = {
    'Anemo': '<:WIND_ADD_HURT:982138235239137290>',
    'Cryo': '<:ICE_ADD_HURT:982138229140635648>',
    'Electro': '<:ELEC_ADD_HURT:982138220248711178>',
    'Geo': '<:ROCK_ADD_HURT:982138232391237632>',
    'Hydro': '<:WATER_ADD_HURT:982138233813098556>',
    'Pyro': '<:FIRE_ADD_HURT:982138221569900585>',
    'Dendro': '<:GRASS_ADD_HURT:982138222891110432>'
}

convert_elements = {
    'Wind': 'Anemo',
    'Ice': 'Cryo',
    'Electric': 'Electro',
    'Rock': 'Geo',
    'Water': 'Hydro',
    'Fire': 'Pyro',
    'Grass': 'Dendro'
}

colors = {
    "Pyro": "#EF9A9A",
    "Hydro": "#91B9F4",
    "Geo": "#CFC09A",
    "Electro": "#B39DDB",
    "Anemo": "#80CBC4",
    "Cryo": "#C5EDFF",
    "Dendro": "#C5E1A5",
}

def get_element_emoji(element: str) -> str:
    return element_emojis.get(element, "")

def convert_element(element: str) -> str:
    return convert_elements.get(element, "Unknown")

def get_element_color(element: str) -> str:
    return colors.get(element, "#e5e5e5")