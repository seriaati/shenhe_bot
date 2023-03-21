from pathlib import Path

from hoyolabrssfeeds import FeedConfigLoader, Game, GameFeed


async def create_feed(lang: str):
    loader = FeedConfigLoader(Path(f"apps/hoyolab_rss_feeds/configs/{lang}.toml"))
    genshin_config = await loader.get_feed_config(Game.GENSHIN)
    genshin_feed = GameFeed.from_config(genshin_config)
    await genshin_feed.create_feed()
