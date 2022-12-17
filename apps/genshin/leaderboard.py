import uuid
from typing import List

import aiosqlite
import diskcache
import genshin

from apps.genshin.utils import get_current_abyss_season


async def update_user_abyss_leaderboard(
    db: aiosqlite.Connection,
    abyss_data: genshin.models.SpiralAbyss,
    user_data: genshin.models.PartialGenshinUserStats,
    characters: List[genshin.models.Character],
    uid: int,
    user_name: str,
    user_id: int,
    previous: int,
) -> None:
    character = abyss_data.ranks.strongest_strike[0]
    g_c = next((c for c in characters if c.id == character.id), None)
    if g_c is None:
        raise ValueError("Genshin character data not found")
    random_uuid = str(uuid.uuid4())
    current_season = get_current_abyss_season() - previous

    runs = None
    wins = None
    async with db.execute(
        """
            SELECT
                runs, wins, stars_collected
            FROM
                abyss_leaderboard
            WHERE
                uid = ? AND season = ?
        """
    ) as c:
        row = await c.fetchone()
        if row is not None and row[2] == 36:
            runs = row[0]
            wins = row[1]

    async with db.execute(
        """
            INSERT INTO abyss_leaderboard
                (data_uuid, single_strike, floor, stars_collected, uid, user_name, user_id, season, runs, wins, icon_url, level)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT
                (uid, season)
            DO UPDATE SET
                data_uuid = ?, single_strike = ?, floor = ?, stars_collected = ?, user_name = ?, user_id = ?, runs = ?, wins = ?, icon_url = ?, level = ?
            WHERE 
                uid = ? AND season = ?
        """,
        (
            random_uuid,
            character.value,
            abyss_data.max_floor,
            abyss_data.total_stars,
            uid,
            user_name,
            user_id,
            current_season,
            runs or abyss_data.total_battles,
            wins or abyss_data.total_wins,
            abyss_data.ranks.most_played[0].icon,
            user_data.info.level,
            random_uuid,
            character.value,
            abyss_data.max_floor,
            abyss_data.total_stars,
            user_name,
            user_id,
            runs or abyss_data.total_battles,
            wins or abyss_data.total_wins,
            abyss_data.ranks.most_played[0].icon,
            user_data.info.level,
            uid,
            current_season,
        ),
    ) as cursor:
        with diskcache.FanoutCache("data/abyss_leaderboard") as cache:
            cache.set(random_uuid, g_c)

        # character usage rate
        # only take floor 12 data
        floor = [f for f in abyss_data.floors if f.floor == 12]
        if floor:
            used_characters = []
            f = floor[0]
            for c in f.chambers:
                for b in c.battles:
                    for chara in b.characters:
                        used_characters.append(chara.id)
            await cursor.execute(
                """
                    INSERT INTO abyss_character_leaderboard
                        (uid, characters, user_id, season)
                    VALUES
                        (?, ?, ?, ?)
                    ON CONFLICT
                        (uid, season)
                    DO UPDATE SET
                        characters = ?, user_id = ?
                    WHERE
                        uid = ? AND season = ?
                """,
                (
                    uid,
                    str(used_characters),
                    user_id,
                    current_season,
                    str(used_characters),
                    user_id,
                    uid,
                    current_season,
                ),
            )

        # cross compare cache and db
        await cursor.execute("SELECT data_uuid FROM abyss_leaderboard")
        db_uuids = [r[0] for r in await cursor.fetchall()]
        with diskcache.FanoutCache("data/abyss_leaderboard") as cache:
            cache_uuids = list(cache._caches.keys())
            for c_uuid in cache_uuids:
                if c_uuid not in db_uuids:
                    cache.delete(c_uuid)
    await db.commit()
