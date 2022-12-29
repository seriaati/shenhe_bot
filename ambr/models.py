from enum import Enum, IntEnum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator

from data.game.elements import convert_element, convert_elements
from utility.utils import format_number, parse_HTML


class City(BaseModel):
    id: int
    name: str


class PartialMaterial(BaseModel):
    id: str


class Event(BaseModel):
    id: int
    name: Dict[str, str]
    full_name: Dict[str, str] = Field(alias="nameFull")
    description: Dict[str, str]
    banner: Dict[str, str]
    end_time: str = Field(alias="endAt")


class Weapon(BaseModel):
    id: int
    rarity: int = Field(alias="rank")
    type: str
    name: str
    icon: str
    beta: bool = False
    default_icon: bool = False

    @validator("name", allow_reuse=True)
    def parse_name(cls, v):
        return v if v != "" else "Unknown"

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("default_icon", pre=True, allow_reuse=True)
    def check_default_icon(cls, v, values):
        defaults = [
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Sword_Blunt.png?a",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Claymore_Aniki.png?a",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Pole_Gewalt.png?a",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Catalyst_Apprentice.png?a",
            "https://api.ambr.top/assets/UI/UI_EquipIcon_Bow_Hunters.png?a",
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
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("element", allow_reuse=True)
    def get_element_name(cls, v):
        element_name = convert_elements.get(v)
        return element_name


class Material(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    icon: str
    recipe: bool = False
    rarity: int = Field(alias="rank", default=0)
    beta: bool = False

    @validator("icon", pre=True, allow_reuse=True)
    def get_icon_url(cls, v, values):
        if "type" in values and values["type"] == "custom":
            return v
        else:
            icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
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
    sources: Optional[List[MaterialSource]] = Field(alias="source", default=None)
    icon: str
    rarity: int = Field(alias="rank")

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return v.replace("\\n", "\n")

    @validator("sources", allow_reuse=True, pre=True)
    def parse_sources(cls, v):
        if v is None or not v:
            return None
        sources = []
        for source in v:
            source["name"] = parse_HTML(source["name"])
            sources.append(MaterialSource(**source))
        return sources

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
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


class WeaponAscension(BaseModel):
    new_max_level: int = Field(alias="unlockMaxLevel")
    ascension_level: int = Field(alias="promoteLevel")
    cost_items: Optional[List[Tuple[PartialMaterial, int]]] = Field(
        alias="costItems", default=None
    )
    required_player_level: Optional[int] = Field(
        alias="requiredPlayerLevel", default=None
    )
    mora_cost: Optional[int] = Field(alias="coinCost", default=None)

    @validator("cost_items", pre=True, allow_reuse=True)
    def get_cost_items(cls, v):
        result = []
        for key, value in v.items():
            result.append((PartialMaterial(id=key), value))
        return result


class WeaponUpgradeDetail(BaseModel):
    stats: List[WeaponStat] = Field(alias="prop")
    ascensions: List[WeaponAscension] = Field(alias="promote")

    @validator("stats", pre=True, allow_reuse=True)
    def get_stats(cls, v):
        result = []
        for stat in v:
            result.append(WeaponStat(**stat))
        return result

    @validator("ascensions", pre=True, allow_reuse=True)
    def get_ascensions(cls, v):
        result = []
        for ascension in v:
            result.append(WeaponAscension(**ascension))
        return result


class Artifact(BaseModel):
    id: int
    name: str
    rarity_list: List[int] = Field(alias="levelList")
    effects: Dict[str, str] = Field(alias="affixList")
    icon: str

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/reliquary/{v}.png?a"
        return icon_url


class ArtifactEffect(BaseModel):
    two_piece: str
    four_piece: str

    @validator("two_piece", allow_reuse=True)
    def parse_two_piece(cls, v):
        return format_number(v)

    @validator("four_piece", allow_reuse=True)
    def parse_four_piece(cls, v):
        return format_number(v)


class ArtifactDetail(BaseModel):
    id: int
    name: str
    icon: str
    rarities: List[int] = Field(alias="levelList")
    effects: ArtifactEffect = Field(alias="affixList")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/reliquary/{v}.png?a"
        return icon_url

    @validator("effects", pre=True, allow_reuse=True)
    def parse_effects(cls, v):
        li = list(v.values())
        return ArtifactEffect(two_piece=li[0], four_piece=li[1])


class CharacterInfo(BaseModel):
    title: str
    description: str = Field(alias="detail")
    constellation: str
    native: str
    cv: Dict[str, str]


class WeaponDetail(BaseModel):
    name: str
    description: str
    type: str
    icon: str
    rarity: int = Field(alias="rank")
    effect: Optional[WeaponEffect] = Field(alias="affix")
    upgrade: WeaponUpgradeDetail
    ascension_materials: List[PartialMaterial] = Field(alias="ascension")

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return v.replace("\\n", "\n")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
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

    @validator("ascension_materials", pre=True, allow_reuse=True)
    def get_ascension_materials(cls, v):
        result = []
        for key, _ in v.items():
            result.append(PartialMaterial(id=key))
        return result


class CharacterAscension(BaseModel):
    new_max_level: int = Field(alias="unlockMaxLevel")
    ascension_level: int = Field(alias="promoteLevel")
    cost_items: Optional[List[Tuple[PartialMaterial, int]]] = Field(
        alias="costItems", default=None
    )
    required_player_level: Optional[int] = Field(
        alias="requiredPlayerLevel", default=None
    )
    mora_cost: Optional[int] = Field(alias="coinCost", default=None)

    @validator("cost_items", pre=True, allow_reuse=True)
    def get_cost_items(cls, v):
        result = []
        for key, value in v.items():
            result.append((PartialMaterial(id=key), value))
        return result


class CharacterUpgradeDetail(BaseModel):
    ascensions: List[CharacterAscension] = Field(alias="promote")

    @validator("ascensions", pre=True, allow_reuse=True)
    def get_ascensions(cls, v):
        result = []
        for ascension in v:
            result.append(CharacterAscension(**ascension))
        return result


class CharacterNameCard(BaseModel):
    id: int | str
    name: str
    description: str
    icon: str

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return v.replace("\\n", "\n")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        v = v.replace("Icon", "Pic")
        icon_url = f"https://api.ambr.top/assets/UI/namecard/{v}_P.png?a"
        return icon_url


class CharacterOtherDetail(BaseModel):
    name_card: CharacterNameCard = Field(alias="nameCard")


class CharacterTalentUpgrade(BaseModel):
    level: int
    cost_items: Optional[List[Tuple[PartialMaterial, int]]] = Field(
        alias="costItems", default=None
    )
    mora_cost: Optional[int] = Field(alias="coinCost", default=None)

    @validator("cost_items", pre=True, allow_reuse=True)
    def get_cost_items(cls, v):
        if v is None:
            return None
        result = []
        for key, value in v.items():
            result.append((PartialMaterial(id=key), value))
        return result


class CharacterTalentType(IntEnum):
    NORMAL_ATTACK = 0
    ELEMENTAL_SKILL = 0
    ELEMENTAL_BURST = 1
    PASSIVE = 2


class CharacterTalent(BaseModel):
    type: CharacterTalentType
    name: str
    description: str
    icon: str
    upgrades: Optional[List[CharacterTalentUpgrade]] = Field(
        alias="promote", default=None
    )

    @validator("type", pre=True, allow_reuse=True)
    def get_type(cls, v):
        return CharacterTalentType(v)

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return parse_HTML(v)

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("upgrades", pre=True, allow_reuse=True)
    def get_upgrades(cls, v):
        if v is None:
            return None
        result = []
        for _, value in v.items():
            result.append(CharacterTalentUpgrade(**value))
        return result


class CharacterConstellation(BaseModel):
    name: str
    description: str
    icon: str

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return parse_HTML(v)

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url


class CharacterDetail(BaseModel):
    id: str
    rarity: int = Field(alias="rank")
    name: str
    element: str
    weapon_type: str = Field(alias="weaponType")
    icon: str
    birthday: str
    info: CharacterInfo = Field(alias="fetter")
    upgrade: CharacterUpgradeDetail
    other: Optional[CharacterOtherDetail] = None
    talents: List[CharacterTalent] = Field(alias="talent")
    constellations: List[CharacterConstellation] = Field(alias="constellation")
    ascension_materials: List[PartialMaterial] = Field(alias="ascension")

    @validator("element", allow_reuse=True)
    def parse_element(cls, v):
        return convert_element(v)

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("birthday", allow_reuse=True, pre=True)
    def parse_birthday(cls, v):
        return f"{v[0]}/{v[1]}"

    @validator("info", pre=True, allow_reuse=True)
    def parse_info(cls, v):
        return CharacterInfo(**v)

    @validator("upgrade", pre=True, allow_reuse=True)
    def parse_upgrade(cls, v):
        return CharacterUpgradeDetail(**v)

    @validator("other", pre=True, allow_reuse=True)
    def parse_other(cls, v):
        if v is None:
            return None
        return CharacterOtherDetail(**v)

    @validator("talents", pre=True, allow_reuse=True)
    def parse_talents(cls, v):
        result = []
        for _, value in v.items():
            result.append(CharacterTalent(**value))
        return result

    @validator("constellations", pre=True, allow_reuse=True)
    def parse_constellations(cls, v):
        result = []
        for _, value in v.items():
            result.append(CharacterConstellation(**value))
        return result

    @validator("ascension_materials", pre=True, allow_reuse=True)
    def parse_ascension(cls, v):
        result = []
        for key, _ in v.items():
            result.append(PartialMaterial(id=key))
        return result


class Monster(BaseModel):
    id: int
    name: str
    type: str
    icon: str

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/monster/{v}.png?a"
        return icon_url


class MonsterDrop(BaseModel):
    id: str
    rarity: int = Field(alias="rank")
    icon: str
    count: Optional[float] = None

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("count", pre=True, allow_reuse=True)
    def get_count(cls, v):
        if v is None:
            return None
        return float(v)


class MonsterData(BaseModel):
    id: int
    drops: Optional[List[MonsterDrop]] = Field(alias="reward", default=None)

    @validator("drops", pre=True, allow_reuse=True)
    def parse_drops(cls, v):
        if v is None:
            return None
        result = []
        for _, value in v.items():
            value["id"] = _
            result.append(MonsterDrop(**value))
        return result


class MonsterDetail(BaseModel):
    id: int
    name: str
    type: str
    description: str
    icon: str
    data: MonsterData = Field(alias="entries")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/monster/{v}.png?a"
        return icon_url

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return parse_HTML(v)

    @validator("data", pre=True, allow_reuse=True)
    def parse_data(cls, v):
        return MonsterData(**list(v.values())[0])


class Food(BaseModel):
    id: int
    name: str
    type: str
    icon: str
    rarity: int = Field(alias="rank")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url


class FoodEffect(BaseModel):
    effect: str
    
    @validator("effect", allow_reuse=True)
    def parse_effect(cls, v):
        return parse_HTML(v)


class FoodInputMaterial(BaseModel):
    icon: str
    id: str
    count: int


class FoodRecipe(BaseModel):
    effect_icon: str = Field(alias="effectIcon")
    effects: List[FoodEffect] = Field(alias="effect")
    input: Optional[List[FoodInputMaterial]] = None

    @validator("effect_icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("effects", pre=True, allow_reuse=True)
    def parse_effects(cls, v):
        result = []
        for _, value in v.items():
            result.append(FoodEffect(effect=value))
        return result

    @validator("input", pre=True, allow_reuse=True)
    def parse_input(cls, v):
        if v is None:
            return None
        result = []
        for _, value in v.items():
            value["id"] = _
            result.append(FoodInputMaterial(**value))
        return result


class FoodSource(BaseModel):
    name: str
    type: str


class FoodDetail(BaseModel):
    name: str
    description: str
    type: str
    recipe: Optional[FoodRecipe] = None
    icon: str
    sources: Optional[List[FoodSource]]
    rarity: int = Field(alias="rank")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return parse_HTML(v)

    @validator("recipe", pre=True, allow_reuse=True)
    def parse_recipe(cls, v):
        if v is None:
            return None
        return FoodRecipe(**v)

    @validator("sources", pre=True, allow_reuse=True)
    def parse_sources(cls, v):
        if v is None:
            return None
        result = []
        for _, value in v.items():
            result.append(FoodSource(**value))
        return result


class Furniture(BaseModel):
    id: int
    name: str
    cost: Optional[int] = None
    comfort: int
    rarity: int = Field(alias="rank")
    icon: str
    categories = List[str]
    types: List[str]

    class Config:
        arbitrary_types_allowed = True

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/furniture/{v}.png?a"
        return icon_url


class FurnitureInputMaterial(BaseModel):
    id: str
    icon: str
    count: int

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url


class FurnitureRecipe(BaseModel):
    exp: int
    time: int
    input: Optional[List[FurnitureInputMaterial]] = None

    @validator("input", pre=True, allow_reuse=True)
    def parse_input(cls, v):
        if v is None:
            return None
        result = []
        for _, value in v.items():
            value["id"] = _
            result.append(FurnitureInputMaterial(**value))
        return result


class FurnitureDetail(BaseModel):
    id: int
    name: str
    cost: Optional[int] = None
    comfort: int
    rarity: int = Field(alias="rank")
    categories: List[str]
    types: List[str]
    description: str
    recipe: Optional[FurnitureRecipe] = None
    icon: str

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return parse_HTML(v)

    @validator("recipe", pre=True, allow_reuse=True)
    def parse_recipe(cls, v):
        if v is None:
            return None
        return FurnitureRecipe(**v)

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/furniture/{v}.png?a"
        return icon_url


class NameCard(BaseModel):
    id: int
    name: str
    icon: str
    rarity: int = Field(alias="rank")
    type: str

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/namecard/{v}.png?a"
        return icon_url


class NameCardDetail(BaseModel):
    id: int
    name: str
    rarity: int = Field(alias="rank")
    type: str
    description: str
    icon: str
    source: str

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/namecard/{v}.png?a"
        return icon_url

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return parse_HTML(v)


class Book(BaseModel):
    id: int
    name: str
    icon: str
    rarity: int = Field(alias="rank")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url


class BookVolume(BaseModel):
    id: int
    name: str
    description: str
    story_id: str = Field(alias="storyId")

    @validator("description", allow_reuse=True)
    def parse_description(cls, v):
        return parse_HTML(v)


class BookDetail(BaseModel):
    id: int
    name: str
    rarity: int = Field(alias="rank")
    icon: str
    volumes: List[BookVolume] = Field(alias="volume")

    @validator("icon", allow_reuse=True)
    def get_icon_url(cls, v):
        icon_url = f"https://api.ambr.top/assets/UI/{v}.png?a"
        return icon_url

    @validator("volumes", pre=True, allow_reuse=True)
    def parse_volumes(cls, v):
        result = []
        for volume in v:
            result.append(BookVolume(**volume))
        return result
