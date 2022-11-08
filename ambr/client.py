import json
import os
import time
from typing import Dict, List, Optional

import aiohttp

from ambr.constants import CITIES, EVENTS_URL, LANGS
from ambr.endpoints import BASE, ENDPOINTS, STATIC_ENDPOINTS
from ambr.models import (
    Artifact,
    ArtifactDetail,
    Character,
    CharacterDetail,
    CharacterUpgrade,
    City,
    Domain,
    Event,
    Material,
    MaterialDetail,
    Monster,
    Weapon,
    WeaponDetail,
    WeaponUpgrade,
)


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
        else:
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
            for endpoint in endpoints:
                data = await self.request_from_endpoint(endpoint, static=True)
                with open(
                    f"ambr/cache/static/{STATIC_ENDPOINTS.get(endpoint)}.json",
                    "w+",
                    encoding="utf-8",
                ) as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            for lang in langs:
                for endpoint in endpoints:
                    data = await self.request_from_endpoint(endpoint, lang)
                    path = f"ambr/cache/{lang}"
                    if not os.path.exists(path):
                        os.makedirs(path)
                    with open(
                        f"ambr/cache/{lang}/{ENDPOINTS.get(endpoint)}.json",
                        "w+",
                        encoding="utf-8",
                    ) as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

    async def get_character_detail(self, id: str) -> Optional[CharacterDetail]:
        """Get the detail of a character.

        Args:
            id (str): id of the character.

        Returns:
            Optional[CharacterDetail]: A CharacterDetail object.
        """
        data = await self.request_from_endpoint("character", id=id)
        result = CharacterDetail(**data["data"])
        return result

    async def get_material_detail(self, id: int) -> Optional[MaterialDetail]:
        """Get a material detail by id.

        Args:
            id (int): id of the material

        Returns:
            Optional[MaterialDetail]: A material detail object.
        """
        data = await self.request_from_endpoint("material", id=id)
        result = MaterialDetail(**data["data"])
        return result

    async def get_weapon_detail(self, id: int) -> Optional[WeaponDetail]:
        """Get a weapon detail by id.

        Args:
            id (int): id of the weapon

        Returns:
            WeaponDetail: A weapon detail object.
        """
        data = await self.request_from_endpoint("weapon", id=id)
        result = WeaponDetail(**data["data"])
        return result

    async def get_artifact_detail(self, id: int) -> Optional[ArtifactDetail]:
        """Get an artifact detail by id.

        Args:
            id (int): id of the artifact

        Returns:
            Optional[ArtifactDetail]: An artifact detail object.
        """
        data = await self.request_from_endpoint("artifact", id=id)
        result = ArtifactDetail(**data["data"])
        return result

    @get_decorator
    async def get_material(
        self, id: Optional[int] = None
    ) -> Optional[List[Material] | Material]:
        """Get a list of all materials or a specific material by id.

        Args:
            id (Optional[int], optional): The id of the material. Defaults to None.

        Returns:
            Optional[List[Material] | Material]: A list of all materials or a specific material.
        """
        result = []
        data = self.get_cache("material")
        if id is not None:
            return Material(**data["data"]["items"][str(id)])
        else:
            for material in data["data"]["items"].values():
                result.append(Material(**material))

            return result

    @get_decorator
    async def get_artifact(
        self, id: Optional[int] = None
    ) -> Optional[List[Artifact] | Artifact]:
        """Get a list of all artifacts or a specific artifact by id.

        Args:
            id (Optional[int], optional): id of the artifact. Defaults to None.

        Returns:
            Optional[List[Artifact] | Artifact]: A list of all artifacts or a specific artifact.
        """
        result = []
        data = self.get_cache("artifact")
        if id is not None:
            return Artifact(**data["data"]["items"][str(id)])
        else:
            for material in data["data"]["items"].values():
                result.append(Artifact(**material))

            return result

    @get_decorator
    async def get_character(
        self,
        id: Optional[str] = None,
        include_beta: bool = True,
        include_traveler: bool = True,
    ) -> Optional[List[Character] | Character]:
        """Get a list of all characters or a specific character by id.

        Args:
            id (Optional[str], optional): id of the character. Defaults to None.
            include_beta (bool, optional): include beta characters. Defaults to True.
            include_traveler (bool, optional): include travelers. Defaults to True.

        Returns:
            Optional[List[Character] | Character]: A list of all characters or a specific character.
        """
        result = []
        data = self.get_cache("character")
        if id is not None:
            return Character(**data["data"]["items"][str(id)])
        else:
            for character_id, character_info in data["data"]["items"].items():
                if "beta" in character_info and not include_beta:
                    continue
                if (
                    "10000005" in character_id or "10000007" in character_id
                ) and not include_traveler:
                    continue
                result.append(Character(**character_info))

            return result

    @get_decorator
    async def get_weapon(
        self, id: Optional[int] = None
    ) -> Optional[List[Weapon] | Weapon]:
        """Get a list of all weapons or a specific weapon by id.

        Args:
            id (Optional[int], optional): id of the weapon. Defaults to None.

        Returns:
            Optional[List[Weapon] | Weapon]: A list of all weapons or a specific weapon.
        """
        result = []
        data = self.get_cache("weapon")
        if id is not None:
            return Weapon(**data["data"]["items"][str(id)])
        else:
            for weapon in data["data"]["items"].values():
                result.append(Weapon(**weapon))
        return result
    
    @get_decorator
    async def get_monster(self, id: Optional[int] = None) -> Optional[List[Monster] | Monster]:
        """Get a list of all monsters or a specific monster by id.

        Args:
            id (Optional[int], optional): id of the monster. Defaults to None.

        Returns:
            Optional[List[Monster] | Monster]: A list of all monsters or a specific monster.
        """
        result = []
        data = self.get_cache("monster")
        if id is not None:
            return Monster(**data["data"]["items"][str(id)])
        else:
            for monster in data["data"]["items"].values():
                result.append(Monster(**monster))
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
    ) -> Optional[List[CharacterUpgrade] | CharacterUpgrade]:
        """Get a list of all character upgrades or a specific character upgrade by character id.

        Args:
            character_id (Optional[str], optional): id of the character. Defaults to None.

        Returns:
            Optional[List[CharacterUpgrade] | CharacterUpgrade]: A list of all character upgrades or a specific character upgrade.
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
            return CharacterUpgrade(**upgrade_info)
        else:
            for upgrade_id, upgrade_info in data["data"]["avatar"].items():
                upgrade_info["item_list"] = [
                    (await self.get_material(id=int(material_id)))
                    for material_id in upgrade_info["items"]
                ]
                upgrade_info["character_id"] = upgrade_id
                result.append(CharacterUpgrade(**upgrade_info))

            return result

    @get_decorator
    async def get_weapon_upgrade(
        self, weapon_id: Optional[int] = None
    ) -> Optional[List[WeaponUpgrade] | WeaponUpgrade]:
        """Get a list of all weapon upgrades or a specific weapon upgrade by weapon id.

        Args:
            weapon_id (Optional[int], optional): id of the weapon. Defaults to None.

        Returns:
            Optional[List[WeaponUpgrade] | WeaponUpgrade]: A list of all weapon upgrades or a specific weapon upgrade.
        """
        result = []
        data = self.get_cache("upgrade", static=True)
        if weapon_id is not None:
            upgrade_info = data["data"]["weapon"][str(weapon_id)]
            upgrade_info["weapon_id"] = weapon_id
            upgrade_info["item_list"] = [
                (await self.get_material(id=int(material_id)))
                for material_id in upgrade_info["items"]
            ]
            result.append(WeaponUpgrade(**upgrade_info))
        else:
            for upgrade_id, upgrade_info in data["data"]["weapon"].items():
                upgrade_info["weapon_id"] = upgrade_id
                upgrade_info["item_list"] = [
                    (await self.get_material(id=int(material_id)))
                    for material_id in upgrade_info["items"]
                ]
                result.append(WeaponUpgrade(**upgrade_info))

        return result

    async def get_domain(self) -> List[Domain]:
        """Get a list of all domains.

        Returns:
            List[Domain]: A list of all domains.
        """
        result = []
        data = self.get_cache("domain")
        for weekday, domain_dict in data["data"].items():
            weekday_int = time.strptime(weekday, "%A").tm_wday
            for _, domain_info in domain_dict.items():
                city_id = domain_info["city"]
                city_lang_dict = CITIES.get(
                    city_id,
                    {
                        "cht": "未知城市",
                        "en": "Unknown City",
                        "jp": "未知の都市",
                        "chs": "未知城市",
                        "fr": "Ville inconnue",
                        "de": "Unbekannte Stadt",
                        "es": "Ciudad desconocida",
                        "pt": "Cidade desconhecida",
                        "ru": "Неизвестный город",
                        "kr": "알 수없는 도시",
                        "vi": "Thành phố không xác định",
                        "id": "Kota tidak diketahui",
                        "th": "เมืองที่ไม่รู้จัก",
                    },
                )
                city = City(id=city_id, name=city_lang_dict[self.lang])
                rewards = []
                for reward in domain_info["reward"]:
                    if len(str(reward)) == 6:
                        material = await self.get_material(id=reward)
                        rewards.append(material)
                domain_info["city"] = city
                domain_info["weekday"] = weekday_int
                domain_info["reward"] = rewards
                result.append(Domain(**domain_info))

        return result

    async def get_events(self) -> List[Event]:
        """Get a list of all events.

        Returns:
            List[Event]: A list of all events.
        """
        result = []
        async with self.session.get(EVENTS_URL) as resp:
            data = await resp.json()
            for event in list(data.values()):
                result.append(Event(**event))
        return result
