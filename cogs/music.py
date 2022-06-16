import aiosqlite
import wavelink
from discord.ext import commands
from discord import ButtonStyle, Interaction, app_commands
from discord.ui import View, button, Button
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
        if not self.bot.debug_toggle:
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
        try:
            await self.bot.wait_for("wavelink_track_start", timeout=180)
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
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
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
                    await i.edit_original_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 正在加載播放清單', '時長取決於播放清單長度'))
                    async for partial in spotify.SpotifyTrack.iterator(query=search, partial_tracks=False):
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
                is_spotify = True
                emoji = '<:spotify:985539937053061190>'
                try:
                    track: spotify.SpotifyTrack = await spotify.SpotifyTrack.search(query=search, return_first=True)
                except wavelink.ext.spotify.SpotifyRequestError:
                    return await i.edit_original_message(embed=errEmbed('<a:error_animated:982579472060547092> 該連結找不到對應 spotify 歌曲'))
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
            if is_playlist:
                verb = '已新增'
            else:
                verb = '(已新增至待播放清單)'
                vc.queue.put(track)
        else:
            await vc.play(track)
        if vc.is_paused():
            await vc.resume()
        if is_playlist and not is_spotify:
            title = f'{emoji} {verb}播放清單: {playlist.name}'
        elif is_playlist and is_spotify:
            title = f'{emoji} {verb}以{track.title}為首的播放清單'
        else:
            title = f'{emoji} {track.title}'
        embed = defaultEmbed(
            f'{title}',
            f'{verb}\n'
            f'<:CLOCK:985902088691277904> {datetime.timedelta(seconds=track.length)}\n'
            f'<:MIC:985902267418955776> {track.author}\n'
            f'<:LINK:985902086262759484> {track.uri}')
        embed.set_image(url=track.thumb)
        await i.edit_original_message(embed=embed)

    class VoteView(View):
        def __init__(self, db: aiosqlite.Connection, requirement: int, vc: wavelink.Player, action: str):
            super().__init__(timeout=None)
            self.db = db
            self.requirement = requirement
            self.vc = vc
            self.action = action

        @button(label='贊成', style=ButtonStyle.green)
        async def callback(self, i: Interaction, button: Button):
            vc_role = i.guild.get_role(980774103344640000)
            if vc_role not in i.user.roles:
                return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 你沒有在語音台中'), ephemeral=True)
            c = await self.db.cursor()
            await c.execute('SELECT * FROM music WHERE user_id = ? AND channel_id = ?', (i.user.id, self.vc.channel.id))
            result = (await c.fetchone())
            if result is None:
                await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, self.vc.channel.id, i.message.id))
                await self.db.commit()
            else:
                return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 你投過票囉'), ephemeral=True)
            await c.execute('SELECT COUNT (user_id) FROM music WHERE channel_id = ?', (self.vc.channel.id,))
            count = (await c.fetchone())[0]
            if count == self.requirement:
                await c.execute('DELETE FROM music WHERE channel_id = ?', (self.vc.channel.id,))
                await self.db.commit()
                return self.stop()
            await i.response.edit_message(embed=defaultEmbed(self.action, f'贊成人數: {count}/{self.requirement}'))

    @app_commands.command(name='stop', description='停止播放器並清除待播放清單')
    async def music_stop(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if not vc.is_playing():
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 現在沒有正在播放的歌曲', '輸入 `/play` 來播放歌曲'), ephemeral=True)
        async def action(one_person: bool):
            await vc.stop()
            vc.queue.clear()
            if one_person:
                await i.response.edit_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已停止'))
            else:
                await i.edit_original_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已停止'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 此投票已經創建過', f'[連結]({url})'), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要停止播放器嗎?')
            await i.response.send_message(embed=defaultEmbed('要停止播放器嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

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
        async def action(one_person: bool):
            await vc.pause()
            if one_person:
                await i.response.edit_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已暫停'))
            else:
                await i.edit_original_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已暫停'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 此投票已經創建過', f'[連結]({url})'), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要暫停播放器嗎?')
            await i.response.send_message(embed=defaultEmbed('要暫停播放器嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

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
        async def action(one_person: bool):
            await vc.resume()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已繼續'))
            else:
                await i.edit_original_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 播放器已繼續'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 此投票已經創建過', f'[連結]({url})'), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要取消播放器暫停嗎?')
            await i.response.send_message(embed=defaultEmbed('要取消播放器暫停嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

    @app_commands.command(name='disconnect', description='讓申鶴悄悄的離開目前所在的語音台')
    @app_commands.checks.has_role('小雪團隊')
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
            f'<:CLOCK:985902088691277904> {datetime.timedelta(seconds=int(vc.position))}/{datetime.timedelta(seconds=track.length)}\n'
            f"<:MIC:985902267418955776> {track.info['author']}\n"
            f"<:LINK:985902086262759484> {track.info['uri']}"
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
        async def action(one_person: bool):
            await vc.stop()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 跳過成功', f'正在播放: {vc.queue[0]}'))
            else:
                await i.edit_original_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 跳過成功', f'正在播放: {vc.queue[0]}'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 此投票已經創建過', f'[連結]({url})'), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要跳過這一首歌嗎?')
            await i.response.send_message(embed=defaultEmbed('要跳過這一首歌嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

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
        async def action(one_person: bool):
            vc.queue.clear()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 待播放清單清除成功'))
            else:
                await i.edit_original_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 待播放清單清除成功'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 此投票已經創建過', f'[連結]({url})'), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要清除待播放清單嗎?')
            await i.response.send_message(embed=defaultEmbed('要清除待播放清單嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

    @app_commands.command(name='seek', description='往前跳一段距離')
    @app_commands.rename(position='秒數')
    @app_commands.describe(position='要跳過的秒數')
    async def music_seek(self, i: Interaction, position: int):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 人呢!', '請在語音台中使用此指令'), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 錯誤', '播放器不存在\n輸入 `/play` 來播放歌曲'), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if not vc.is_playing():
            return await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 沒有任何歌正在播放', '輸入 `/play` 播放歌曲'), ephemeral=True)
        await vc.seek(position*1000)
        await i.response.send_message(embed=defaultEmbed(f'<a:check_animated:982579879239352370> 已往前 {position} 秒'))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCog(bot))
