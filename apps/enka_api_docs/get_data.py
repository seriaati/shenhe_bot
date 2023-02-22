import json
from typing import Any, Dict, List, Optional
import aiofiles

async def get_character_skill_order(character_id: str) -> List[int]:
    """Get the talent order of a character from Enka API's character.json file."""
    async with aiofiles.open("API-docs/store/characters.json") as f:
        characters: Dict[str, Any] = json.loads(await f.read())
    
    character: Optional[Dict[str, Any]] = characters.get(character_id)
    if character and "SkillOrder" in character:
        return character.get("SkillOrder")
    else:
        return []