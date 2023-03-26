import json
import os
from typing import Dict, List, Optional

import aiohttp

import ambr.models as models

from .constants import CITIES, EVENTS_URL, LANGS, WEEKDAYS, get_city_name
from .endpoints import BASE, ENDPOINTS, STATIC_ENDPOINTS


def get_decorator(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except KeyError:
            return None

    return wrapper


class AmbrTopAPI:
    def __init__(self, session: aiohttp.ClientSession, lang: str = "en"):
        self.session = session
        self.lang = lang
        if self.lang not in LANGS:
            raise ValueError(
                f"Invalid language: {self.lang}, valid values are: {LANGS.keys()}"
            )
        self.cache = self.load_cache()

    def load_cache(self) -> Dict:
        """Load cache from files.

        Returns:
            Dict: Cache.
        """
        cache = {}
        for lang in list(LANGS.keys()):
            if lang not in cache:
                cache[lang] = {}
            for endpoint in list(ENDPOINTS.keys()):
                cache[lang][endpoint] = self.request_from_cache(endpoint)
        for static_endpoint in list(STATIC_ENDPOINTS.keys()):
            cache[static_endpoint] = self.request_from_cache(
                static_endpoint, static=True
            )

        return cache

    def get_cache(self, endpoint: str, static: bool = False) -> Dict:
        """Get the cache of an endpoint.

        Args:
            endpoint (str): The name of the endpoint.
            static (bool, optional): Whether the endpoint is static data or not. Defaults to False.

        Returns:
            Dict: The cache of the endpoint.
        """
        if static:
            return self.cache[endpoint]
        return self.cache[self.lang][endpoint]

    async def request_from_endpoint(
        self,
        endpoint: str,
        lang: Optional[str] = "",
        static: bool = False,
        id: Optional[str | int] = "",
    ) -> Dict:
        """Request data from a specific endpoint.

        Args:
            endpoint (str): Name of the endpoint.
            lang (Optional[str], optional): Language of the endpoint. Defaults to None.
            static (bool, optional): Whether the endpoint is static data or not. Defaults to False.
            id (Optional[str | int], optional): The id of an item. Defaults to None.

        Raises:
            ValueError: If the endpoint is not valid.

        Returns:
            Dict: The data of the endpoint.
        """
        lang = lang or self.lang
        if static:
            endpoint_url = f"{BASE}static/{STATIC_ENDPOINTS.get(endpoint)}"
        else:
            endpoint_url = f"{BASE}{lang}/{ENDPOINTS.get(endpoint)}/{id}"
        async with self.session.get(endpoint_url) as r:
            endpoint_data = await r.json()
        if "code" in endpoint_data:
            raise ValueError(f"Invalid endpoint = {endpoint} | URL = {endpoint_url}")
        return endpoint_data

    def request_from_cache(self, endpoint: str, static: bool = False) -> Dict:
        """Request an endpoint data from cache.

        Args:
            endpoint (str): The name of the endpoint.
            static (bool, optional): Whether the endpoint is static data or not. Defaults to False.

        Returns:
            Dict: Endpoint data.
        """
        if static:
            try:
                with open(
                    f"ambr/cache/static/{STATIC_ENDPOINTS.get(endpoint)}.json",
                    "r",
                    encoding="utf-8",
                ) as f:
                    endpoint_data = json.load(f)
            except FileNotFoundError:
                endpoint_data = {}
        else:
            try:
                with open(
                    f"ambr/cache/{self.lang}/{ENDPOINTS.get(endpoint)}.json",
                    "r",
                    encoding="utf-8",
                ) as f:
                    endpoint_data = json.load(f)
            except FileNotFoundError:
                endpoint_data = {}

        return endpoint_data

    async def update_cache(
        self,
        all_lang: bool = False,
        endpoint: str = "",
        static: bool = False,
    ) -> None:
        """Update the cache of the API by sending requests to the API through an aiohttp session.

        Args:
            all_lang (bool, optional): To update the cache of all languages. Defaults to False.
            endpoint (Optional[str], optional): To update a specific endpoint. Defaults to None.
            static (bool, optional): To update static endpoints. Defaults to False.
        """
        if all_lang:
            langs = list(LANGS.keys())
        else:
            langs = [self.lang]
        if endpoint == "":
            if not static:
                endpoints = list(ENDPOINTS.keys())
            else:
                endpoints = list(STATIC_ENDPOINTS.keys())
        else:
            endpoints = [endpoint]

        if static:
            for e in endpoints:
                data = await self.request_from_endpoint(e, static=True)
                with open(
                    f"ambr/cache/static/{STATIC_ENDPOINTS.get(e)}.json",
                    "w+",
                    encoding="utf-8",
                ) as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            for lang in langs:
                for e in endpoints:
                    data = await self.request_from_endpoint(e, lang)
                    path = f"ambr/cache/{lang}"
                    if not os.path.exists(path):
                        os.makedirs(path)
                    with open(
                        f"ambr/cache/{lang}/{ENDPOINTS.get(e)}.json",
                        "w+",
                        encoding="utf-8",
                    ) as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

    async def get_character_detail(self, id: str) -> Optional[models.CharacterDetail]:
        """Get the detail of a character.

        Args:
            id (str): id of the character.

        Returns:
            Optional[models.CharacterDetail]: A models.CharacterDetail object.
        """
        data = await self.request_from_endpoint("character", id=id)
        result = models.CharacterDetail(**data["data"])
        return result

    async def get_monster_detail(self, id: int) -> Optional[models.MonsterDetail]:
        """Get the detail of a monster.

        Args:
            id (int): id of the monster.

        Returns:
            Optional[models.MonsterDetail]: A models.MonsterDetail object.
        """
        data = await self.request_from_endpoint("monster", id=id)
        result = models.MonsterDetail(**data["data"])
        return result

    async def get_food_detail(self, id: int) -> Optional[models.FoodDetail]:
        """Get the detail of a food.

        Args:
            id (int): id of the food.

        Returns:
            Optional[models.FoodDetail]: A models.FoodDetail object.
        """
        data = await self.request_from_endpoint("food", id=id)
        result = models.FoodDetail(**data["data"])
        return result

    async def get_furniture_detail(self, id: int) -> Optional[models.FurnitureDetail]:
        """Get the detail of a furniture.

        Args:
            id (int): id of the furniture.

        Returns:
            Optional[models.FurnitureDetail]: A models.FurnitureDetail object.
        """
        data = await self.request_from_endpoint("furniture", id=id)
        result = models.FurnitureDetail(**data["data"])
        return result

    async def get_book_detail(self, id: int) -> Optional[models.BookDetail]:
        """Get the detail of a book.

        Args:
            id (int): id of the book.

        Returns:
            Optional[models.BookDetail]: A models.BookDetail object.
        """
        data = await self.request_from_endpoint("book", id=id)
        result = models.BookDetail(**data["data"])
        return result

    async def get_name_card_detail(self, id: int) -> Optional[models.NameCardDetail]:
        """Get the detail of a name card.

        Args:
            id (int): id of the name card.

        Returns:
            Optional[models.NameCardDetail]: A models.NameCardDetail object.
        """
        data = await self.request_from_endpoint("namecard", id=id)
        result = models.NameCardDetail(**data["data"])
        return result

    async def get_material_detail(self, id: int) -> Optional[models.MaterialDetail]:
        """Get a material detail by id.

        Args:
            id (int): id of the material

        Returns:
            Optional[models.MaterialDetail]: A material detail object.
        """
        data = await self.request_from_endpoint("material", id=id)
        result = models.MaterialDetail(**data["data"])
        return result

    async def get_weapon_detail(self, id: int) -> Optional[models.WeaponDetail]:
        """Get a weapon detail by id.

        Args:
            id (int): id of the weapon

        Returns:
            models.WeaponDetail: A weapon detail object.
        """
        data = await self.request_from_endpoint("weapon", id=id)
        result = models.WeaponDetail(**data["data"])
        return result

    async def get_artifact_detail(self, id: int) -> Optional[models.ArtifactDetail]:
        """Get an artifact detail by id.

        Args:
            id (int): id of the artifact

        Returns:
            Optional[models.ArtifactDetail]: An artifact detail object.
        """
        data = await self.request_from_endpoint("artifact", id=id)
        result = models.ArtifactDetail(**data["data"])
        return result

    @get_decorator
    async def get_material(
        self, id: Optional[int] = None
    ) -> Optional[List[models.Material] | models.Material]:
        """Get a list of all materials or a specific material by id.

        Args:
            id (Optional[int], optional): The id of the material. Defaults to None.

        Returns:
            Optional[List[models.Material] | models.Material]: A list of all materials or a specific material.
        """
        result = []
        data = self.get_cache("material")
        if id is not None:
            return models.Material(**data["data"]["items"][str(id)])
        for material in data["data"]["items"].values():
            result.append(models.Material(**material))

        return result

    @get_decorator
    async def get_name_card(
        self, id: Optional[int] = None
    ) -> Optional[List[models.NameCard] | models.NameCard]:
        """Get a list of all name cards or a specific name card by id.

        Args:
            id (Optional[int], optional): The id of the name card. Defaults to None.

        Returns:
            Optional[List[models.NameCard] | models.NameCard]: A list of all name cards or a specific name card.
        """
        result = []
        data = self.get_cache("namecard")
        if id is not None:
            return models.NameCard(**data["data"]["items"][str(id)])
        for name_card in data["data"]["items"].values():
            result.append(models.NameCard(**name_card))

        return result

    @get_decorator
    async def get_artifact(
        self, id: Optional[int] = None
    ) -> Optional[List[models.Artifact] | models.Artifact]:
        """Get a list of all artifacts or a specific artifact by id.

        Args:
            id (Optional[int], optional): id of the artifact. Defaults to None.

        Returns:
            Optional[List[models.Artifact] | models.Artifact]: A list of all artifacts or a specific artifact.
        """
        result = []
        data = self.get_cache("artifact")
        if id is not None:
            return models.Artifact(**data["data"]["items"][str(id)])
        for material in data["data"]["items"].values():
            result.append(models.Artifact(**material))

        return result

    @get_decorator
    async def get_book(
        self, id: Optional[int] = None
    ) -> Optional[List[models.Book] | models.Book]:
        """Get a list of all books or a specific book by id.

        Args:
            id (Optional[int], optional): id of the book. Defaults to None.

        Returns:
            Optional[List[models.Book] | models.Book]: A list of all books or a specific book.
        """
        result = []
        data = self.get_cache("book")
        if id is not None:
            return models.Book(**data["data"]["items"][str(id)])
        for material in data["data"]["items"].values():
            result.append(models.Book(**material))

        return result

    @get_decorator
    async def get_food(
        self, id: Optional[int] = None
    ) -> Optional[List[models.Food] | models.Food]:
        """Get a list of all foods or a specific food by id.

        Args:
            id (Optional[int], optional): id of the food. Defaults to None.

        Returns:
            Optional[List[models.Food] | models.Food]: A list of all foods or a specific food.
        """
        result = []
        data = self.get_cache("food")
        if id is not None:
            return models.Food(**data["data"]["items"][str(id)])
        for material in data["data"]["items"].values():
            result.append(models.Food(**material))

        return result

    @get_decorator
    async def get_funiture(
        self, id: Optional[int] = None
    ) -> Optional[List[models.Furniture] | models.Furniture]:
        """Get a list of all furniture or a specific furniture by id.

        Args:
            id (Optional[int], optional): id of the furniture. Defaults to None.

        Returns:
            Optional[List[models.Furniture] | models.Furniture]: A list of all furniture or a specific furniture.
        """
        result = []
        data = self.get_cache("furniture")
        if id is not None:
            return models.Furniture(**data["data"]["items"][str(id)])
        for material in data["data"]["items"].values():
            result.append(models.Furniture(**material))

        return result

    @get_decorator
    async def get_character(
        self,
        id: Optional[str] = None,
        include_beta: bool = True,
        include_traveler: bool = True,
    ) -> Optional[List[models.Character] | models.Character]:
        """Get a list of all characters or a specific character by id.

        Args:
            id (Optional[str], optional): id of the character. Defaults to None.
            include_beta (bool, optional): include beta characters. Defaults to True.
            include_traveler (bool, optional): include travelers. Defaults to True.

        Returns:
            Optional[List[models.Character] | models.Character]: A list of all characters or a specific character.
        """
        result = []
        data = self.get_cache("character")
        if id is not None:
            return models.Character(**data["data"]["items"][str(id)])
        for character_id, character_info in data["data"]["items"].items():
            if "beta" in character_info and not include_beta:
                continue
            if (
                "10000005" in character_id or "10000007" in character_id
            ) and not include_traveler:
                continue
            result.append(models.Character(**character_info))

        return result

    @get_decorator
    async def get_weapon(
        self, id: Optional[int] = None
    ) -> Optional[List[models.Weapon] | models.Weapon]:
        """Get a list of all weapons or a specific weapon by id.

        Args:
            id (Optional[int], optional): id of the weapon. Defaults to None.

        Returns:
            Optional[List[models.Weapon] | models.Weapon]: A list of all weapons or a specific weapon.
        """
        result = []
        data = self.get_cache("weapon")
        if id is not None:
            return models.Weapon(**data["data"]["items"][str(id)])
        for weapon in data["data"]["items"].values():
            result.append(models.Weapon(**weapon))
        return result

    @get_decorator
    async def get_monster(
        self, id: Optional[int] = None
    ) -> Optional[List[models.Monster] | models.Monster]:
        """Get a list of all monsters or a specific monster by id.

        Args:
            id (Optional[int], optional): id of the monster. Defaults to None.

        Returns:
            Optional[List[models.Monster] | models.Monster]: A list of all monsters or a specific monster.
        """
        result = []
        data = self.get_cache("monster")
        if id is not None:
            return models.Monster(**data["data"]["items"][str(id)])
        for monster in data["data"]["items"].values():
            result.append(models.Monster(**monster))
        return result

    async def get_weapon_types(self) -> Dict[str, str]:
        """Get a dictionary of all weapon types.

        Returns:
            Dict[str, str]: A dictionary of all weapon types.
        """
        data = self.get_cache("weapon")
        return data["data"]["types"]

    @get_decorator
    async def get_character_upgrade(
        self, character_id: Optional[str] = None
    ) -> Optional[List[models.CharacterUpgrade] | models.CharacterUpgrade]:
        """Get a list of all character upgrades or a specific character upgrade by character id.

        Args:
            character_id (Optional[str], optional): id of the character. Defaults to None.

        Returns:
            Optional[List[models.CharacterUpgrade] | models.CharacterUpgrade]: A list of all character upgrades or a specific character upgrade.
        """
        result = []
        data = self.get_cache("upgrade", static=True)
        if character_id is not None:
            upgrade_info = data["data"]["avatar"][character_id]
            upgrade_info["character_id"] = character_id
            upgrade_info["item_list"] = [
                (await self.get_material(id=int(material_id)))
                for material_id in upgrade_info["items"]
            ]
            return models.CharacterUpgrade(**upgrade_info)
        for upgrade_id, upgrade_info in data["data"]["avatar"].items():
            upgrade_info["item_list"] = [
                (await self.get_material(id=int(material_id)))
                for material_id in upgrade_info["items"]
            ]
            upgrade_info["character_id"] = upgrade_id
            result.append(models.CharacterUpgrade(**upgrade_info))

        return result

    @get_decorator
    async def get_weapon_upgrade(
        self, weapon_id: Optional[int] = None
    ) -> Optional[List[models.WeaponUpgrade] | models.WeaponUpgrade]:
        """Get a list of all weapon upgrades or a specific weapon upgrade by weapon id.

        Args:
            weapon_id (Optional[int], optional): id of the weapon. Defaults to None.

        Returns:
            Optional[List[models.WeaponUpgrade] | models.WeaponUpgrade]: A list of all weapon upgrades or a specific weapon upgrade.
        """
        data = self.get_cache("upgrade", static=True)
        if weapon_id is not None:
            upgrade_info = data["data"]["weapon"][str(weapon_id)]
            upgrade_info["weapon_id"] = weapon_id
            upgrade_info["item_list"] = [
                (await self.get_material(id=int(material_id)))
                for material_id in upgrade_info["items"]
            ]
            return models.WeaponUpgrade(**upgrade_info)
        result = []
        for upgrade_id, upgrade_info in data["data"]["weapon"].items():
            upgrade_info["weapon_id"] = upgrade_id
            upgrade_info["item_list"] = [
                (await self.get_material(id=int(material_id)))
                for material_id in upgrade_info["items"]
            ]
            result.append(models.WeaponUpgrade(**upgrade_info))

        return result

    async def get_domains(self) -> List[models.Domain]:
        """Get a list of all domains.

        Returns:
            List[models.Domain]: A list of all domains.
        """
        result = []
        data = self.get_cache("domain")
        for weekday, domain_dict in data["data"].items():
            weekday_int = WEEKDAYS.get(weekday, 0)
            for domain_info in domain_dict.values():
                city_id = domain_info["city"]
                city = models.City(
                    id=city_id,
                    name=get_city_name(city_id, self.lang),
                )
                rewards: List[models.Material] = []
                for reward in domain_info["reward"]:
                    material = await self.get_material(id=reward)
                    if not isinstance(material, models.Material):
                        continue
                    rewards.append(material)

                domain_info["city"] = city
                domain_info["weekday"] = weekday_int
                domain_info["reward"] = rewards
                result.append(models.Domain(**domain_info))

        return result

    async def get_events(self) -> List[models.Event]:
        """Get a list of all events.

        Returns:
            List[models.Event]: A list of all events.
        """
        result = []
        async with self.session.get(EVENTS_URL) as resp:
            data = await resp.json()
            for event in list(data.values()):
                result.append(models.Event(**event))
        return result

    async def get_book_story(self, story_id: str) -> str:
        async with self.session.get(
            f"https://api.ambr.top/v2/{self.lang}/readable/models.Book{story_id}"
        ) as resp:
            story = await resp.json()
        return story["data"]

    async def get_weapon_curve(self, curve_type: str, level: int) -> float:
        """Get the percentage number of weapon curve given a weapon level."""
        data = self.get_cache("weapon_curve", static=True)
        return data["data"][str(level)]["curveInfos"][curve_type]
