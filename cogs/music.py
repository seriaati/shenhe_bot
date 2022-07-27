from typing import Any
import aiosqlite
import wavelink
from discord.ext import commands
from discord import ButtonStyle, Interaction, Member, SelectOption, app_commands
from discord.ui import View, button, Button, Select
from dotenv import load_dotenv
from debug import DefaultView
from utility.utils import defaultEmbed, divide_chunks, errEmbed
from wavelink.ext import spotify
import datetime
import asyncio
import re
import os
from utility.paginators.GeneralPaginator import GeneralPaginator
load_dotenv()


class MusicCog(commands.GroupCog, name='music'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # if not self.bot.debug_toggle:
        bot.loop.create_task(self.connect_nodes())
        super().__init__()

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host='127.0.0.1',
            port=2333,
            password=os.getenv('lavalink'),
            spotify_client=spotify.SpotifyClient(client_id='5f86059662e84a53b79454457f923fe0', client_secret='30812d67a6ab40419ca7d4d228a956ba'))

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if not player.queue.is_empty:
            await player.play(player.queue.get())
        try:
            await self.bot.wait_for("wavelink_track_start", timeout=180)
        except asyncio.TimeoutError:
            await player.disconnect()
            
    class ChooseSongView(DefaultView):
        def __init__(self, options: list[SelectOption], author: Member):
            super().__init__(timeout=None)
            self.author = author
            self.uri = None
            self.add_item(MusicCog.ChooseSongSelect(options))
            
        async def interaction_check(self, i: Interaction) -> bool:
            if i.user.id != self.author.id:
                await i.response.send_message(embed=errEmbed(message='指令: `/music play`').set_author(name='你不是這個指令的發起者', icon_url=i.user.avatar), ephemeral=True)
            return i.user.id == self.author.id
    
    class ChooseSongSelect(Select):
        def __init__(self, options: list[SelectOption]):
            super().__init__(placeholder='選擇想播放的歌曲', options=options)
            
        async def callback(self, i: Interaction) -> Any:
            await i.response.defer()
            await i.message.delete()
            self.view.uri = self.values[0]
            self.view.stop()

    @app_commands.command(name="play播放", description="播放音樂")
    @app_commands.rename(search='關鍵詞或連結')
    async def music_play(self, i: Interaction, search: str):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            vc: wavelink.Player = await i.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if i.guild.voice_client.channel != i.user.voice.channel:
            if vc.is_playing():
                return await i.response.send_message(embed=errEmbed(message='你跟目前申鶴所在的語音台不同,\n且申鶴目前正在為那邊的使用者播歌\n請等待至對方播放完畢').set_author(name='錯誤', icon_url=i.user.avatar), ephemeral=True)
            await vc.disconnect()
            vc: wavelink.Player = await i.user.voice.channel.connect(cls=wavelink.Player)
        await i.response.defer()
        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if (re.match(regex, search) is not None):  # search is a url
            if decoded := spotify.decode_url(search):
                if decoded["type"] is spotify.SpotifySearchType.unusable:
                    return await i.followup.send(embed=errEmbed().set_author(name='無效的 spotify 連結', icon_url=i.user.avatar), ephemeral=True)
                elif decoded["type"] in (
                    spotify.SpotifySearchType.playlist,
                    spotify.SpotifySearchType.album,
                ):
                    async for partial in spotify.SpotifyTrack.iterator(query=decoded["id"], partial_tracks=True, type=decoded["type"]):
                        vc.queue.put(partial)
                    await vc.play(vc.queue[0])
                    return await i.followup.send(embed=defaultEmbed().set_author(name='已將播放清單新增至待播清單', icon_url=i.user.avatar))
                else:
                    emoji = '<:spotify:985539937053061190>'
                    track = await spotify.SpotifyTrack.search(
                        query=decoded["id"], return_first=True
                    )
            elif 'youtu.be' in search or 'youtube' in search:
                emoji = '<:yt:985540703323058196>'
                if 'list' in search:
                    try:
                        playlist: wavelink.YouTubePlaylist = await wavelink.NodePool.get_node().get_playlist(wavelink.YouTubePlaylist, search)
                    except Exception as e:
                        return await i.followup.send(embed=errEmbed(message=f"```py\n{e}\n```").set_author(name='無效的播放清單', icon_url=i.user.avatar))
                    for track in playlist.tracks:
                        vc.queue.put(track)
                    await vc.play(vc.queue[0])
                    embed = defaultEmbed(f'{emoji} {playlist.name}')
                    embed.set_author(name='已將播放清單中的歌曲新增至待播清單', icon_url=i.user.avatar)
                    embed.set_image(url=vc.queue[0].thumb)
                    return await i.followup.send(embed=embed)
                else:
                    try:
                        track = await wavelink.YouTubeTrack.search(query=search, return_first=True)
                    except Exception as e:
                        return await i.followup.send(embed=errEmbed(message=f"```py\n{e}\n```").set_author(name='無效的歌曲', icon_url=i.user.avatar), ephemeral=True)
        else:
            emoji = '<:yt:985540703323058196>'
            tracks = await wavelink.YouTubeTrack.search(search)
            options = []
            for track in tracks[:25]:
                options.append(SelectOption(label=track.title, description=track.author, value=track.uri))
            view = MusicCog.ChooseSongView(options, i.user)
            embed = defaultEmbed().set_author(name=f'歌曲搜尋: {search}', icon_url=i.user.avatar)
            await i.followup.send(embed=embed, view=view)
            await view.wait()
            track = await wavelink.YouTubeTrack.search(query=view.uri, return_first=True)
        try:
            await vc.play(track)
        except AttributeError:
            return await i.followup.send(embed=errEmbed().set_author(name='無效的歌曲', icon_url=i.user.avatar), ephemeral=True)
        embed = defaultEmbed(f'{emoji} {track.title}').set_author(name='已將歌曲新增至待播清單', icon_url=i.user.avatar)
        embed.add_field(
            name='歌曲資訊',
            value=
            f'<:CLOCK:985902088691277904> {datetime.timedelta(seconds=track.length)}\n'
            f'<:MIC:985902267418955776> {track.author}\n'
            f'<:LINK:985902086262759484> {track.uri}')
        embed.set_image(url=track.thumbnail)
        await i.followup.send(embed=embed)

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
                return await i.response.send_message(embed=errEmbed().set_author(name='你不在語音台中', icon_url=i.user.avatar), ephemeral=True)
            c = await self.db.cursor()
            await c.execute('SELECT * FROM music WHERE user_id = ? AND channel_id = ?', (i.user.id, self.vc.channel.id))
            result = (await c.fetchone())
            if result is None:
                await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, self.vc.channel.id, i.message.id))
                await self.db.commit()
            else:
                return await i.response.send_message(embed=errEmbed().set_author(name='你投過票囉', icon_url=i.user.avatar), ephemeral=True)
            await c.execute('SELECT COUNT (user_id) FROM music WHERE channel_id = ?', (self.vc.channel.id,))
            count = (await c.fetchone())[0]
            if count == self.requirement:
                await c.execute('DELETE FROM music WHERE channel_id = ?', (self.vc.channel.id,))
                await self.db.commit()
                return self.stop()
            await i.response.edit_message(embed=defaultEmbed(self.action, f'贊成人數: {count}/{self.requirement}'))

    @app_commands.command(name='stop停止', description='停止播放器並清除待播清單')
    async def music_stop(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client

        async def action(one_person: bool, i: Interaction):
            await vc.stop()
            vc.queue.clear()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('播放器已停止'))
            else:
                await i.edit_original_message(embed=defaultEmbed('播放器已停止'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True, i)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed(message=f'[連結]({url})').set_author(name='投票已存在', icon_url=i.user.avatar), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要停止播放器嗎?')
            await i.response.send_message(embed=defaultEmbed('要停止播放器嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False, i)

    @app_commands.command(name='pause暫停', description='暫停播放器')
    async def music_pause(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if vc.is_paused():
            return await i.response.send_message(embed=errEmbed().set_author(name='播放器已經被暫停了', icon_url=i.user.avatar), ephemeral=True)

        async def action(one_person: bool):
            await vc.pause()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('播放器已暫停'))
            else:
                await i.edit_original_message(embed=defaultEmbed('播放器已暫停'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed(message=f'[連結]({url})').set_author(name='投票已存在', icon_url=i.user.avatar), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要暫停播放器嗎?')
            await i.response.send_message(embed=defaultEmbed('要暫停播放器嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

    @app_commands.command(name='resume繼續', description='取消暫停')
    async def music_resume(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if not vc.is_paused():
            return await i.response.send_message(embed=errEmbed().set_author(name='目前的音樂沒有被暫停', icon_url=i.user.avatar), ephemeral=True)

        async def action(one_person: bool):
            await vc.resume()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('播放器已繼續'))
            else:
                await i.edit_original_message(embed=defaultEmbed('播放器已繼續'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed(message=f'[連結]({url})').set_author(name='投票已存在', icon_url=i.user.avatar), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要取消播放器暫停嗎?')
            await i.response.send_message(embed=defaultEmbed('要取消播放器暫停嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

    @app_commands.command(name='disconnect斷線', description='讓申鶴悄悄的離開目前所在的語音台')
    @app_commands.checks.has_role('小雪團隊')
    async def music_disconnect(self, i: Interaction):
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
        vc: wavelink.Player = i.guild.voice_client
        if not vc.is_connected():
            return await i.response.send_message(embed=errEmbed().set_author(name='申鶴沒有在任何一個語音台中', icon_url=i.user.avatar), ephemeral=True)
        await vc.disconnect()
        await i.response.send_message(embed=defaultEmbed('申鶴已離開'))

    @app_commands.command(name='player播放狀態', description='查看目前播放狀態')
    async def music_player(self, i: Interaction):
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
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

    @app_commands.command(name='queue待播清單', description='查看目前待播清單')
    async def music_queue(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
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
                if isinstance(track, wavelink.PartialTrack):
                    value += f'{count}. {track.title}\n'
                else:
                    value += f'{count}. {track.info["title"]}\n'
                count += 1
            embeds.append(defaultEmbed('待播清單', value))
        await GeneralPaginator(i, embeds).start(embeded=True)

    @app_commands.command(name='skip跳過', description='跳過目前正在播放的歌曲')
    async def music_skip(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if vc.queue.is_empty:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='後面沒有歌了', icon_url=i.user.avatar), ephemeral=True)

        async def action(one_person: bool):
            await vc.stop()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('跳過成功', f'正在播放: {vc.queue[0]}'))
            else:
                await i.edit_original_message(embed=defaultEmbed('跳過成功', f'正在播放: {vc.queue[0]}'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed(message=f'[連結]({url})').set_author(name='投票已存在', icon_url=i.user.avatar), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要跳過這一首歌嗎?')
            await i.response.send_message(embed=defaultEmbed('要跳過這一首歌嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

    @app_commands.command(name='clear清除', description='清除目前的待播清單')
    async def music_clear(self, i: Interaction):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if vc.queue.is_empty:
            return await i.response.send_message(embed=errEmbed().set_author(name='待播清單已經沒有歌了', icon_url=i.user.avatar), ephemeral=True)

        async def action(one_person: bool):
            vc.queue.clear()
            if one_person:
                await i.response.send_message(embed=defaultEmbed('待播清單清除成功'))
            else:
                await i.edit_original_message(embed=defaultEmbed('待播清單清除成功'), view=None)
        if len(vc.channel.members)-1 <= 2:
            await action(True)
        else:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT msg_id FROM music WHERE channel_id = ?', (vc.channel.id,))
            result = await c.fetchone()
            if result is not None:
                url = i.channel.get_partial_message(result[0]).jump_url
                return await i.response.send_message(embed=errEmbed(message=f'[連結]({url})').set_author(name='投票已存在', icon_url=i.user.avatar), ephemeral=True)
            view = MusicCog.VoteView(self.bot.db, round(
                (len(vc.channel.members)-1)/2), vc, '要清除待播清單嗎?')
            await i.response.send_message(embed=defaultEmbed('要清除待播清單嗎?', f'贊成人數: 1/{round((len(vc.channel.members)-1)/2)}'), view=view)
            msg = await i.original_message()
            await c.execute('INSERT INTO music (user_id, channel_id, msg_id) VALUES (?, ?, ?)', (i.user.id, vc.channel.id, msg.id))
            await view.wait()
            await action(False)

    @app_commands.command(name='seek跳前', description='往前跳一段距離')
    @app_commands.rename(position='秒數')
    @app_commands.describe(position='要跳過的秒數')
    async def music_seek(self, i: Interaction, position: int):
        if i.user.voice is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='請在語音台中使用此指令', icon_url=i.user.avatar), ephemeral=True)
        if not i.guild.voice_client:
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='播放器不存在', icon_url=i.user.avatar), ephemeral=True)
        else:
            vc: wavelink.Player = i.guild.voice_client
        if not vc.is_playing():
            return await i.response.send_message(embed=errEmbed(message='輸入 `/play` 來播放歌曲').set_author(name='沒有任何歌正在播放', icon_url=i.user.avatar), ephemeral=True)
        await vc.seek(position*1000)
        await i.response.send_message(embed=defaultEmbed(f'已往前 {position} 秒'))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCog(bot))
