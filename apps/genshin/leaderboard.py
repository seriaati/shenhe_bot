import uuid
from typing import List

import aiosqlite
import diskcache
import genshin


async def update_user_abyss_leaderboard(
    db: aiosqlite.Connection,
    abyss_data: genshin.models.SpiralAbyss,
    characters: List[genshin.models.Character],
    uid: int,
    user_name: str,
    user_id: int,
) -> None:
    character = abyss_data.ranks.strongest_strike[0]
    g_c = next((c for c in characters if c.id == character.id), None)
    if g_c is None:
        raise ValueError("Character not found")
    async with db.execute(
        "SELECT data_uuid FROM abyss_leaderboard WHERE uid = ?",
        (uid,),
    ) as cursor:  # is the user already in the leaderboard?
        result = await cursor.fetchone()
        if result is not None:
            with diskcache.FanoutCache(
                "data/abyss_leaderboard"
            ) as cache:  # delete the user's old character data
                cache.delete(result[0])

        random_uuid = str(uuid.uuid4())
        await cursor.execute(
            "INSERT INTO abyss_leaderboard (data_uuid, single_strike, floor, stars_collected, uid, user_name, user_id) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (uid) DO UPDATE SET data_uuid = ?, single_strike = ?, floor = ?, stars_collected = ?, user_name = ?, user_id = ? WHERE uid = ?",
            (
                random_uuid,
                character.value,
                abyss_data.max_floor,
                abyss_data.total_stars,
                uid,
                user_name,
                user_id,
                random_uuid,
                character.value,
                abyss_data.max_floor,
                abyss_data.total_stars,
                user_name,
                user_id,
                uid,
            ),
        )
        with diskcache.FanoutCache("data/abyss_leaderboard") as cache:
            cache.set(random_uuid, g_c)
        floor = [f for f in abyss_data.floors if f.floor == 12]
        if floor:
            used_characters = []
            f = floor[0]
            for c in f.chambers:
                for b in c.battles:
                    for chara in b.characters:
                        used_characters.append(chara.id)
            await cursor.execute(
                "INSERT INTO abyss_character_leaderboard (uid, characters, user_id) VALUES (?, ?, ?) ON CONFLICT (uid) DO UPDATE SET characters = ?, user_id = ? WHERE uid = ?",
                (
                    uid,
                    str(used_characters),
                    user_id,
                    str(used_characters),
                    user_id,
                    uid,
                ),
            )
    await db.commit()
