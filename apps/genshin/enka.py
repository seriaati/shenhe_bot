from typing import Dict, List, Optional, Tuple
import asqlite
import enkanetwork
import pickle
from exceptions import NeverRaised, NoCharacterFound


async def get_enka_data(
    uid: int, lang: str, pool: asqlite.Pool
) -> Tuple[
    enkanetwork.model.EnkaNetworkResponse,
    enkanetwork.model.EnkaNetworkResponse,
    Optional[enkanetwork.model.EnkaNetworkResponse],
]:
    async with enkanetwork.EnkaNetworkAPI(lang=lang) as enka:
        try:
            data = await enka.fetch_user(uid)

            await enka.set_language(enkanetwork.Language.EN)
            en_data = await enka.fetch_user(uid)
        except (
            enkanetwork.exception.VaildateUIDError,
            enkanetwork.exception.UIDNotFounded,
        ) as e:
            raise e
        except Exception as e:
            cache = await get_enka_cache(uid, pool)
            en_cache = await get_enka_cache(uid, pool, en=True)
            if not cache or not en_cache:
                raise e
            else:
                return cache, en_cache, None
        else:
            await update_enka_cache(uid, data, en_data, pool)

            cache = await get_enka_cache(uid, pool)
            en_cache = await get_enka_cache(uid, pool, en=True)

            if not cache or not en_cache:
                raise NeverRaised
            return cache, en_cache, data


async def get_enka_cache(
    uid: int, pool: asqlite.Pool, en: bool = False
) -> Optional[enkanetwork.model.EnkaNetworkResponse]:
    async with pool.acquire() as db:
        col = "en_data" if en else "data"
        async with db.execute(
            f"SELECT {col} FROM enka_cache WHERE uid = ?", (uid,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None or row[0] is None:
                return None
            else:
                return pickle.loads(row[0])


async def save_enka_cache(
    uid: int,
    data: enkanetwork.model.EnkaNetworkResponse,
    pool: asqlite.Pool,
    en: bool = False,
) -> None:
    async with pool.acquire() as db:
        col = "en_data" if en else "data"
        await db.execute(
            f"INSERT INTO enka_cache (uid, {col}) VALUES (?, ?) ON CONFLICT(uid) DO UPDATE SET {col} = ? WHERE uid = ?",
            (
                uid,
                pickle.dumps(data),
                pickle.dumps(data),
                uid,
            ),
        )
        await db.commit()


async def update_enka_cache(
    uid: int,
    current_data: enkanetwork.model.EnkaNetworkResponse,
    current_en_data: enkanetwork.model.EnkaNetworkResponse,
    pool: asqlite.Pool,
) -> None:
    """Update enka cache

    Args:
        uid (int): UID of the player
        current_data (enkanetwork.model.EnkaNetworkResponse): current enka data
        current_en_data (enkanetwork.model.EnkaNetworkResponse): current English enka data
        pool (asqlite.Pool): database pool

    Raises:
        NoCharacterFound: No character is found in the user's character showcase
    """
    if current_data.characters is None or current_en_data.characters is None:
        raise NoCharacterFound

    cache = await get_enka_cache(uid, pool)
    en_cache = await get_enka_cache(uid, pool, en=True)

    if cache is None or en_cache is None:
        await save_enka_cache(uid, current_data, pool)
        await save_enka_cache(uid, current_en_data, pool, en=True)
        return

    data_cache: List[Dict[str, enkanetwork.model.EnkaNetworkResponse]] = [
        {
            "data": current_data,
            "cache": cache,
        },
        {
            "data": current_en_data,
            "cache": en_cache,
        },
    ]

    for index, d_c in enumerate(data_cache):
        c_dict = {}
        d_dict = {}
        new_dict = {}

        if d_c["cache"].characters:
            for c in d_c["cache"].characters:
                c_dict[c.id] = c

        if d_c["data"].characters:
            for d in d_c["data"].characters:
                d_dict[d.id] = d

        new_dict = c_dict | d_dict

        d_c["cache"].characters = list(new_dict.values())
        d_c["cache"].player = d_c["data"].player

        await save_enka_cache(uid, d_c["cache"], pool, index == 1)
