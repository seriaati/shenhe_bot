from typing import List

import asyncpg
import genshin
from discord import utils

from utils import get_current_abyss_season


async def update_user_abyss_leaderboard(
    abyss_data: genshin.models.SpiralAbyss,
    user_data: genshin.models.PartialGenshinUserStats,
    characters: List[genshin.models.Character],
    uid: int,
    user_name: str,
    user_id: int,
    previous: int,
    pool: asyncpg.Pool,
) -> None:
    character = abyss_data.ranks.strongest_strike[0]
    g_c = utils.get(characters, id=character.id)
    if not g_c:
        raise AssertionError

    current_season = get_current_abyss_season() - previous

    runs = None
    wins = None
    row = await pool.fetchrow(
        """
        SELECT runs, wins, stars_collected
        FROM abyss_leaderboard
        WHERE uid = $1 AND season = $2
        """,
        uid,
        current_season,
    )
    if row and row["stars_collected"] == 36:
        runs = row["runs"]
        wins = row["wins"]

    await pool.execute(
        """
        INSERT INTO abyss_leaderboard
            (single_strike, floor, stars_collected, uid,
            user_name, user_id, season, runs, wins, icon_url,
            level, const, refine, c_level, c_icon)
        VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8,
            $9, $10, $11, $12, $13, $14, $15)
        ON CONFLICT
            (uid, season)
        DO UPDATE SET
            single_strike = $1, floor = $2,
            stars_collected = $3, user_name = $5,
            user_id = $6, runs = $8, wins = $9,
            icon_url = $10, level = $11, const = $12,
            refine = $13, c_level = $14, c_icon = $15
        """,
        character.value,
        abyss_data.max_floor,
        abyss_data.total_stars,
        uid,
        user_name,
        user_id,
        current_season,
        runs or abyss_data.total_battles,
        wins or int(abyss_data.total_wins),
        abyss_data.ranks.most_played[0].icon,
        user_data.info.level,
        g_c.constellation,
        g_c.weapon.refinement,
        g_c.level,
        g_c.icon,
    )

    # character usage rate (only take floor 12 data)
    floor = utils.get(abyss_data.floors, floor=12)
    if floor:
        used_characters: List[int] = []
        for c in floor.chambers:
            for b in c.battles:
                for chara in b.characters:
                    used_characters.append(chara.id)
        await pool.execute(
            """
            INSERT INTO abyss_character_leaderboard
                (uid, characters, user_id, season)
            VALUES
                ($1, $2, $3, $4)
            ON CONFLICT
                (uid, season)
            DO UPDATE SET
                characters = $2, user_id = $3
            """,
            uid,
            used_characters,
            user_id,
            current_season,
        )
