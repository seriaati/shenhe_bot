from utils.general import open_json

emoji_map = open_json("data/star_rail/emoji_map.json")


def get_character_emoji(character_id: str) -> str:
    """Get Honkai Star Rail character Discord emoji."""
    return emoji_map.get(character_id, "")
