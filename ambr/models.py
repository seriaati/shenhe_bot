from typing import Dict, List, Optional

from data.game.elements import convert_elements
from pydantic import BaseModel, Field, validator

from utility.utils import format_number, parse_HTML


class City(BaseModel):
    id: int
    name: str


class Weapon(BaseModel):
    id: int
    rarity: int = Field(alias="rank")
    type: str
    name: str
    icon: str
    beta: bool = False
    default_icon: bool = False

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png"
        return icon_url

    @validator("default_icon", pre=True, allow_reuse=True)
    def check_default_icon(cls, v, values):
        defaults = [
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Sword_Blunt.png",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Claymore_Aniki.png",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Pole_Gewalt.png",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Catalyst_Apprentice.png",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Bow_Hunters.png",
        ]
        if values["icon"] in defaults:
            return True


class Character(BaseModel):
    id: str
    name: str
    rairty: int = Field(alias="rank")
    element: str
    weapon_type: str = Field(alias="weaponType")
    icon: str
    beta: bool = False

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png"
        return icon_url

    @validator("element", allow_reuse=True)
    def get_element_name(cls, v):
        element_name = convert_elements.get(v)
        return element_name


class Material(BaseModel):
    id: int
    name: str
    type: str
    recipe: bool
    map_mark: bool = Field(alias="mapMark")
    icon: str
    rarity: int = Field(alias="rank")
    beta: bool = False

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v, values):
        if values["type"] == "custom":
            return "https://i.imgur.com/ByIyBa7.png"
        else:
            icon_url = f"https://api.ambr.top/assets/UI/{v}.png"
            return icon_url


class Domain(BaseModel):
    id: int
    name: str
    rewards: List[Material] = Field(alias="reward")
    city: City
    weekday: int


class CharacterUpgrade(BaseModel):
    character_id: str
    items: List[Material] = Field(alias="item_list")
    beta: bool = False


class WeaponUpgrade(BaseModel):
    weapon_id: int
    items: List[Material] = Field(alias="item_list")
    beta: bool = False


class MaterialSource(BaseModel):
    name: str
    type: str
    days: List[str] = []


class MaterialDetail(BaseModel):
    name: str
    description: str
    type: str
    map_mark: bool = Field(alias="mapMark")
    sources: List = Field(alias="source")
    icon: str
    rarity: int = Field(alias="rank")

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return v.replace("\\n", "\n")

    @validator("sources", allow_reuse=True)
    def get_sources(cls, v):
        result = []
        for source in v:
            result.append(MaterialSource(**source))
        return result

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png"
        return icon_url


class WeaponEffect(BaseModel):
    name: str
    descriptions: List[str] = Field(alias="upgrade")

    @validator("descriptions", pre=True, allow_reuse=True)
    def parse_description(cls, v):
        result = []
        for _ in list(v.values()):
            result.append(format_number(parse_HTML(_)))
        return result


class WeaponStat(BaseModel):
    prop_id: Optional[str] = Field(alias="propType", default=None)
    initial_value: int = Field(alias="initValue")


class WeaponUpgradeDetail(BaseModel):
    awaken_cost: List[int] = Field(alias="awakenCost")
    stats: List[WeaponStat] = Field(alias="prop")
    upgrade_info: List = Field(alias="promote")

    @validator("stats", pre=True, allow_reuse=True)
    def get_stats(cls, v):
        result = []
        for stat in v:
            result.append(WeaponStat(**stat))
        return result


class WeaponDetail(BaseModel):
    name: str
    description: str
    type: str
    icon: str
    rarity: int = Field(alias="rank")
    effect: Optional[WeaponEffect] = Field(alias="affix")
    upgrade: WeaponUpgradeDetail

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return v.replace("\\n", "\n")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png"
        return icon_url

    @validator("effect", pre=True, allow_reuse=True)
    def parse_effect(cls, v):
        if v is None:
            return None
        else:
            v = list(v.values())[0]
            return WeaponEffect(**v)

    @validator("upgrade", pre=True, allow_reuse=True)
    def get_upgrade(cls, v):
        return WeaponUpgradeDetail(**v)


class Artifact(BaseModel):
    id: int
    name: str
    rarity_list: List[int] = Field(alias="levelList")
    effects: Dict[str, str] = Field(alias="affixList")
    icon: str

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/reliquary/{v}.png"
        return icon_url


class ArtifactEffect(BaseModel):
    two_piece: str
    four_piece: str

    @validator("two_piece", allow_reuse=True)
    def parse_two_piece(cls, v):
        return format_number(v)

    @validator("four_piece", allow_reuse=True)
    def parse_two_piece(cls, v):
        return format_number(v)


class ArtifactDetail(BaseModel):
    id: int
    name: str
    icon: str
    rarities: List[int] = Field(alias="levelList")
    effects: ArtifactEffect = Field(alias="affixList")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/reliquary/{v}.png"
        return icon_url

    @validator("effects", pre=True, allow_reuse=True)
    def parse_effects(cls, v):
        li = list(v.values())
        return ArtifactEffect(two_piece=li[0], four_piece=li[1])
