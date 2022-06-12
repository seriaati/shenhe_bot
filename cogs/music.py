import wavelink
from discord.ext import commands
from discord import Interaction, app_commands
from utility.config import config
from utility.utils import defaultEmbed, divide_chunks, errEmbed
from wavelink.ext import spotify
import datetime
import asyncio
import re
from utility.GeneralPaginator import GeneralPaginator


class MusicCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host='127.0.0.1',
            port=2333,
            password=config.lavalink,
            spotify_client=spotify.SpotifyClient(client_id='5f86059662e84a53b79454457f923fe0', client_secret='30812d67a6ab40419ca7d4d228a956ba'))

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if not player.queue.is_empty:
            await player.play(player.queue.get())

        def check(player: wavelink.Player, track: wavelink.Track):
            return player.guild == player.guild
        try:
            await self.bot.wait_for("wavelink_track_start", check=check, timeout=180)
        except asyncio.TimeoutError:
            await player.disconnect()

    @app_commands.command(name="play", description="播放音樂")
    @app_commands.rename(search='關鍵詞或連結')
    async def music_play(self, i: Interaction, search: str):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            vc: wavelink.Player = await i.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = i.guild.voice_client
        await i.response.send_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 搜尋中'))
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            # domain...
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        is_url = (re.match(regex, search) is not None)
        is_playlist = False
        is_spotify = False
        if is_url:
            if 'list' in search and 'spotify' not in search:
                emoji = '<:yt:985540703323058196>'
                is_playlist = True
                playlist: wavelink.YouTubePlaylist = await wavelink.NodePool.get_node().get_playlist(wavelink.YouTubePlaylist, search)
                track: wavelink.YouTubeTrack = playlist.tracks[
                    0] if playlist.selected_track is None else playlist.tracks[playlist.selected_track]
                playlist.tracks.remove(track)
                for t in playlist.tracks:
                    vc.queue.put(t)
            elif 'playlist' in search and 'spotify' in search:
                emoji = '<:spotify:985539937053061190>'
                is_playlist = True 
                is_spotify = True
                first = True
                try:
                    async for partial in spotify.SpotifyTrack.iterator(query=search, partial_tracks=True):
                        if first:
                            track = partial
                            first = False
                        vc.queue.put(partial)
                except wavelink.ext.spotify.SpotifyRequestError:
                    return await i.edit_original_message(embed=errEmbed('<a:error_animated:982579472060547092> 該連結找不到對應 spotify 播放清單'))
            elif 'youtu.be' in search or 'youtube' in search:
                emoji = '<:yt:985540703323058196>'
                track: wavelink.YouTubeTrack = await wavelink.NodePool.get_node().get_tracks(wavelink.YouTubeTrack, search)
            elif 'spotify' in search:
                emoji = '<:spotify:985539937053061190>'
                track: spotify.SpotifyTrack = await spotify.SpotifyTrack.search(query=search, return_first=True)
            if not is_playlist and not is_spotify:
                try:
                    track = track[0]
                except IndexError:
                    return await i.edit_original_message(embed=errEmbed('<a:error_animated:982579472060547092> 該連結找不到對應歌曲'))
        else:
            emoji = '<:yt:985540703323058196>'
            track: wavelink.YouTubeTrack = await wavelink.YouTubeTrack.search(search, return_first=True)
        verb = ''
        if vc.is_playing():
            if is_playlist and not is_spotify:
                verb = '已新增'
            else:
                verb = '(已新增至待播放清單)'
                vc.queue.put(track)
        else:
            await vc.play(track)
        if is_playlist and not is_spotify:
            embed = defaultEmbed(f'{emoji} {verb}播放清單: {playlist.name}')
            embed.set_image(url=track.thumb)
        elif is_spotify:
            embed = defaultEmbed(f'{emoji} {track.title}')
        else:
            embed = defaultEmbed(
                f'{emoji} {track.title}',
                f'{verb}\n'
                f'🕒 {datetime.timedelta(seconds=track.length)}\n'
                f'✏️ {track.author}\n'
                f'🔗 {track.uri}')
            embed.set_image(url=track.thumb)
        await i.edit_original_message(embed=embed)

    @app_commands.command(name='stop', description='停止播放器並清除待播放清單')
    async def music_stop(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        await vc.stop()
        vc.queue.clear()
        await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已停止'))

    @app_commands.command(name='pause', description='暫停播放器')
    async def music_pause(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if vc.is_paused():
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器已經被暫停了'), ephemeral=True)
        await vc.pause()
        await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已暫停'))

    @app_commands.command(name='resume', description='取消暫停')
    async def music_resume(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if not vc.is_paused():
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 無法繼續', '目前的音樂沒有被暫停'))
        await vc.resume()
        await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已繼續'))

    @app_commands.command(name='disconnect', description='讓申鶴悄悄的離開目前所在的語音台')
    async def music_disconnect(self, i: Interaction):
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        vc: wavelink.Player = i.guild.voice_client
        if not vc.is_connected():
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '申鶴沒有在任何一個語音台中'), ephemeral=True)
        await vc.disconnect()
        await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 申鶴已離開'))

    @app_commands.command(name='player', description='查看目前播放狀況')
    async def music_player(self, i: Interaction):
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        vc: wavelink.Player = i.guild.voice_client
        if not vc.is_playing():
            return await i.response.send_message(embed=defaultEmbed('播放器是空的', '輸入 `/play` 來播放歌曲'))
        track: wavelink.abc.Playable = vc.track
        embed = defaultEmbed(
            track.info['title'],
            f'🕒 {datetime.timedelta(seconds=int(vc.position))}/{datetime.timedelta(seconds=track.length)}\n'
            f"✏️ {track.info['author']}\n"
            f"🔗 {track.info['uri']}"
        )
        embed.set_image(url=track.thumb)
        await i.response.send_message(embed=embed)

    @app_commands.command(name='queue', description='查看目前待播放清單')
    async def music_queue(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if vc.queue.is_empty:
            return await i.response.send_message(embed=defaultEmbed('空空的播放清單', '輸入 `/play` 來新增歌曲'))
        divided_queues = list(divide_chunks(list(vc.queue), 10))
        embeds = []
        count = 1
        for queue in divided_queues:
            value = ''
            for track in queue:
                if type(track) == wavelink.PartialTrack:
                    value += f'{count}. spotify 歌曲目前不支援 queue 顯示\n'
                else:
                    value += f'{count}. {track.info["title"]}\n'
                count += 1
            embeds.append(defaultEmbed('待播放清單', value))
        await GeneralPaginator(i, embeds).start(embeded=True)

    @app_commands.command(name='skip', description='跳過目前正在播放的歌曲')
    async def music_skip(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if vc.queue.is_empty:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 後面沒有歌了', '輸入 `/play` 來新增歌曲'), ephemeral=True)
        next_track = vc.queue.get()
        await vc.play(next_track)
        await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 跳過成功', f'正在播放: {next_track}'))

    @app_commands.command(name='clear', description='清除目前的待播放清單')
    async def music_clear(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if vc.queue.is_empty:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '待播放清單已經沒有歌了'), ephemeral=True)
        vc.queue.clear()
        await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 待播放清單清除成功'))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCog(bot))
