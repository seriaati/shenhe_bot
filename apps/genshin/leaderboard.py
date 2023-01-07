from typing import List

import aiosqlite
import genshin

from apps.genshin.utils import get_current_abyss_season


async def update_user_abyss_leaderboard(
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
    current_season = get_current_abyss_season() - previous

    runs = None
    wins = None
    async with aiosqlite.connect("shenhe.db") as db:
        async with db.execute(
            """
                SELECT
                    runs, wins, stars_collected
                FROM
                    abyss_leaderboard
                WHERE
                    uid = ? AND season = ?
            """,
            (uid, current_season),
        ) as c:
            row = await c.fetchone()
            if row is not None and row[2] == 36:
                runs = row[0]
                wins = row[1]

        async with db.execute(
            """
                INSERT INTO abyss_leaderboard
                    (single_strike, floor, stars_collected, uid, user_name, user_id, season, runs, wins, icon_url, level, const, refine, c_level, c_icon)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT
                    (uid, season)
                DO UPDATE SET
                    single_strike = ?, floor = ?, stars_collected = ?, user_name = ?, user_id = ?, runs = ?, wins = ?, icon_url = ?, level = ?, const = ?, refine = ?, c_level = ?, c_icon = ?
                WHERE 
                    uid = ? AND season = ?
            """,
            (
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
                g_c.constellation,
                g_c.weapon.refinement,
                g_c.level,
                g_c.icon,
                character.value,
                abyss_data.max_floor,
                abyss_data.total_stars,
                user_name,
                user_id,
                runs or abyss_data.total_battles,
                wins or abyss_data.total_wins,
                abyss_data.ranks.most_played[0].icon,
                user_data.info.level,
                g_c.constellation,
                g_c.weapon.refinement,
                g_c.level,
                g_c.icon,
                uid,
                current_season,
            ),
        ) as cursor:
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
        await db.commit()
