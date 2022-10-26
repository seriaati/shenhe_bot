import json
import os
import time
from typing import Dict, List, Optional

import aiohttp

from ambr.constants import CITIES, LANGS
from ambr.endpoints import BASE, ENDPOINTS, STATIC_ENDPOINTS
from ambr.models import (Artifact, ArtifactDetail, Character, CharacterUpgrade,
                         City, Domain, Material, MaterialDetail, Weapon,
                         WeaponDetail, WeaponUpgrade)


class AmbrTopAPI:
    def __init__(self, session: aiohttp.ClientSession, lang: str = "en"):
        self.session = session
        self.lang = lang
        if self.lang not in LANGS:
            raise ValueError(
                f"Invalid language: {self.lang}, valid values are: {LANGS.keys()}"
            )
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        cache = {}
        for lang in list(LANGS.keys()):
            if lang not in cache:
                cache[lang] = {}
            for endpoint in list(ENDPOINTS.keys()):
                cache[lang][endpoint] = self._request_from_cache(endpoint)
        for static_endpoint in list(STATIC_ENDPOINTS.keys()):
            cache[static_endpoint] = self._request_from_cache(
                static_endpoint, static=True
            )

        return cache

    async def _get_cache(self, endpoint: str, static: bool = False) -> Dict:
        if static:
            return self.cache[endpoint]
        else:
            return self.cache[self.lang][endpoint]

    async def _request_from_endpoint(
        self, endpoint: str, lang: str = None, static: bool = False, id: str = ""
    ) -> Dict:
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

    def _request_from_cache(self, endpoint: str, static: bool = False) -> Dict:
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

    async def _update_cache(
        self, all_lang: bool = False, endpoint: str = None, static: bool = False
    ) -> None:
        if all_lang:
            langs = list(LANGS.keys())
        else:
            langs = [self.lang]
        if endpoint is None:
            if not static:
                endpoints = list(ENDPOINTS.keys())
            else:
                endpoints = list(STATIC_ENDPOINTS.keys())
        else:
            endpoints = [endpoint]

        if static:
            for endpoint in endpoints:
                data = await self._request_from_endpoint(endpoint, static=True)
                with open(
                    f"ambr/cache/static/{STATIC_ENDPOINTS.get(endpoint)}.json",
                    "w+",
                    encoding="utf-8",
                ) as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            for lang in langs:
                for endpoint in endpoints:
                    data = await self._request_from_endpoint(endpoint, lang)
                    path = f"ambr/cache/{lang}"
                    if not os.path.exists(path):
                        os.makedirs(path)
                    with open(
                        f"ambr/cache/{lang}/{ENDPOINTS.get(endpoint)}.json",
                        "w+",
                        encoding="utf-8",
                    ) as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

    async def get_material(
        self, id: Optional[int] = None
    ) -> List[Material]:
        result = []
        data = await self._get_cache("material")
        if id is not None:
            result.append(Material(**data["data"]["items"][str(id)]))
        else:
            for material in data["data"].values():
                result.append(Material(**material))

        return result

    async def get_material_detail(self, id: int) -> MaterialDetail:
        data = await self._request_from_endpoint("material", id=id)
        result = MaterialDetail(**data["data"])
        return result

    async def get_weapon_detail(self, id: int) -> WeaponDetail:
        data = await self._request_from_endpoint("weapon", id=id)
        result = WeaponDetail(**data["data"])
        return result

    async def get_artifact_detail(self, id: int) -> ArtifactDetail:
        data = await self._request_from_endpoint("artifact", id=id)
        result = ArtifactDetail(**data["data"])
        return result

    async def get_artifact(
        self, id: Optional[int] = None
    ) -> List[Artifact]:
        result = []
        data = await self._get_cache("artifact")
        if id is not None:
            result.append(Material(**data["data"]["items"][str(id)]))
        else:
            for material in data["data"].values():
                result.append(Material(**material))
                
        return result

    async def get_character(
        self,
        id: Optional[str] = None,
        include_beta: bool = True,
        include_traveler: bool = True,
    ) -> List[Character]:
        result = []
        data = await self._get_cache("character")
        if id is not None:
            result.append(Character(**data["data"]["items"][str(id)]))
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

    async def get_weapon_types(self) -> Dict[str, str]:
        data = await self._get_cache("weapon")
        return data["data"]["types"]

    async def get_weapon(self, id: Optional[int] = None) -> List[Weapon]:
        result = []
        data = await self._get_cache("weapon")
        if id is not None:
            result.append(Character(**data["data"]["items"][str(id)]))
        else:
            for weapon in data["data"].values():
                result.append(Weapon(**weapon))

        return result

    async def get_character_upgrade(
        self, character_id: Optional[str] = None
    ) -> List[CharacterUpgrade]:
        result = []
        data = await self._get_cache("upgrade", static=True)
        if character_id is not None:
            upgrade_info = data["data"]["avatar"][str(character_id)]
            upgrade_info["character_id"] = character_id
            upgrade_info["item_list"] = [
                (await self.get_material(id=int(material_id)))[0]
                for material_id in upgrade_info["items"]
            ]
            result.append(CharacterUpgrade(**upgrade_info))
        else:
            for upgrade_id, upgrade_info in data["data"]["avatar"].items():
                upgrade_info["item_list"] = [
                    (await self.get_material(id=int(material_id)))[0]
                    for material_id in upgrade_info["items"]
                ]
                upgrade_info["character_id"] = upgrade_id
                result.append(CharacterUpgrade(**upgrade_info))

        return result

    async def get_weapon_upgrade(
        self, weapon_id: Optional[int] = None
    ) -> List[WeaponUpgrade]:
        result = []
        data = await self._get_cache("upgrade", static=True)
        if weapon_id is not None:
            upgrade_info = data["data"]["weapon"][str(weapon_id)]
            upgrade_info["weapon_id"] = weapon_id
            upgrade_info["item_list"] = [
                (await self.get_material(id=int(material_id)))[0]
                for material_id in upgrade_info["items"]
            ]
            result.append(CharacterUpgrade(**upgrade_info))
        else:
            for upgrade_id, upgrade_info in data["data"]["weapon"].items():
                upgrade_info["weapon_id"] = upgrade_id
                upgrade_info["item_list"] = [
                    (await self.get_material(id=int(material_id)))[0]
                    for material_id in upgrade_info["items"]
                ]
                result.append(CharacterUpgrade(**upgrade_info))

        return result

    async def get_domain(self) -> List[Domain]:
        result = []
        data = await self._get_cache("domain")
        for weekday, domain_dict in data["data"].items():
            weekday_int = time.strptime(weekday, "%A").tm_wday
            for _, domain_info in domain_dict.items():
                city_id = domain_info["city"]
                city = City(id=city_id, name=CITIES.get(city_id)[self.lang])
                rewards = []
                for reward in domain_info["reward"]:
                    if len(str(reward)) == 6:
                        material = await self.get_material(id=reward)
                        rewards.append(material[0])
                domain_info["city"] = city
                domain_info["weekday"] = weekday_int
                domain_info["reward"] = rewards
                result.append(Domain(**domain_info))

        return result
