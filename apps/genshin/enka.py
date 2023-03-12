from typing import Dict, List, Optional, Tuple

import asyncpg
import enkanetwork
import srsly
import yaml

from exceptions import NoCharacterFound
from utility.utils import log


async def get_enka_data(
    uid: int, lang: str, pool: asyncpg.Pool
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
        except enkanetwork.exception.VaildateUIDError as e:
            raise e
        except Exception as e:
            cache = await get_enka_cache(uid, pool)
            en_cache = await get_enka_cache(uid, pool, en=True)
            if not cache or not en_cache:
                raise e
            return cache, en_cache, None
        else:
            await update_enka_cache(uid, data, en_data, pool)

            cache = await get_enka_cache(uid, pool)
            en_cache = await get_enka_cache(uid, pool, en=True)

            if not (cache and en_cache):
                raise AssertionError
            return cache, en_cache, data


async def get_enka_cache(
    uid: int, pool: asyncpg.Pool, en: bool = False
) -> Optional[enkanetwork.model.EnkaNetworkResponse]:
    cache = await pool.fetchval(
        f"""
        SELECT
            {'en_data' if en else 'data'}
        FROM
            enka_cache
        WHERE uid = $1
        """,
        uid,
    )
    if cache:
        return srsly.pickle_loads(cache)
    return None


async def save_enka_cache(
    uid: int,
    data: enkanetwork.model.EnkaNetworkResponse,
    pool: asyncpg.Pool,
    en: bool = False,
) -> None:
    col = "en_data" if en else "data"
    await pool.execute(
        f"""
        INSERT INTO
            enka_cache (uid, {col})
        VALUES
            ($1, $2)
        ON CONFLICT 
            (uid)
        DO UPDATE SET
            {col} = $2
        """,
        uid,
        srsly.pickle_loads(data),
    )


async def update_enka_cache(
    uid: int,
    current_data: enkanetwork.model.EnkaNetworkResponse,
    current_en_data: enkanetwork.model.EnkaNetworkResponse,
    pool: asyncpg.Pool,
) -> None:
    """Update enka cache

    Args:
        uid (int): UID of the player
        current_data (enkanetwork.model.EnkaNetworkResponse): current enka data
        current_en_data (enkanetwork.model.EnkaNetworkResponse): current English enka data
        pool (asyncpg.Pool): database pool

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


async def yaml_to_pickle(pool: asyncpg.Pool) -> None:
    await pool.execute("ALTER TABLE enka_cache ADD COLUMN IF NOT EXISTS new_data TEXT")
    await pool.execute(
        "ALTER TABLE enka_cache ADD COLUMN IF NOT EXISTS new_en_data TEXT"
    )
    rows = await pool.fetch("SELECT * FROM enka_cache")
    for row in rows:
        data = yaml.load(row["data"], Loader=yaml.Loader)
        en_data = yaml.load(row["en_data"], Loader=yaml.Loader)
        await pool.execute(
            """
            UPDATE
                enka_cache
            SET
                new_data = $1,
                new_en_data = $2
            WHERE
                uid = $3
            """,
            srsly.pickle_dumps(data),
            srsly.pickle_dumps(en_data),
            row["uid"],
        )
        log.info(f"Updated {row['uid']}")
    await pool.execute("ALTER TABLE enka_cache DROP COLUMN data")
    await pool.execute("ALTER TABLE enka_cache DROP COLUMN en_data")
    await pool.execute("ALTER TABLE enka_cache RENAME COLUMN new_data TO data")
    await pool.execute("ALTER TABLE enka_cache RENAME COLUMN new_en_data TO en_data")
