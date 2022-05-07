import re
import discord
import genshin
import yaml
from utility.character_name import character_names


global warningColor, purpleColor, footerAuthor, footerImage, timeOutErrorMsg, embedNoAccount, embedNoGroup, groups, whyRegister
warningColor = 0xfc5165
purpleColor = 0xa68bd3
footerAuthor = "輸入!help來獲得幫助"
footerImage = "https://i.imgur.com/DWYpYrd.jpg"
timeOutErrorMsg = "已取消當前操作, 請在30秒內回答問題"
embedNoAccount = discord.Embed(
    title="😢 該帳號不存在", description="請使用`!register`來註冊帳號, 如有疑問請@小雪", color=warningColor)
whyRegister = "• `!abyss`炫耀你的深淵傷害(或被嘲笑)\n• `!check`查看目前的派遣、樹脂、塵歌壺等狀況\n• `!char`炫耀你擁有的角色\n• `!stats`證明你是大佬\n• `!diary`看看這個月要不要課\n• `!area`炫耀探索度(或被嘲笑)\n• `!today`今天的肝還在嗎\n• 自動領取hoyolab網頁登入獎勵\n• 樹脂提醒功能(詳情請打`!dm`)"


def defaultEmbed(title:str, message:str):
    return discord.Embed(title=title, description=message, color=purpleColor)

def errEmbed(title:str, message:str):
    return discord.Embed(title=title, description=message, color=warningColor)

def log(is_system:bool, is_error:bool, log_type:str, log_msg:str):
    system = "SYSTEM"
    if not is_system:
        system = "USER"
    if not is_error:
        result = f"[{system}][{log_type}] {log_msg}"
    else:
        result = f"[{system}][ERROR][{log_type}] {log_msg}"
    return result
    
def getCharacterName(character: genshin.models.BaseCharacter) -> str:
    chinese_name = character_names.get(character.id)
    return chinese_name if chinese_name != None else character.name

def trimCookie(cookie: str) -> str:
    try:
        new_cookie = ' '.join([
            re.search('ltoken=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('ltuid=[0-9]{3,}', cookie).group(),
            re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('account_id=[0-9]{3,}', cookie).group()
        ])
    except:
        new_cookie = None
    return new_cookie

weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}
def getWeekdayName(n: int) -> str:
    return weekday_dict.get(n)

def openFile(file_name:str) -> dict:
    with open(f'data/{file_name}.yaml', 'r', encoding='utf-8') as file:
        result =  yaml.unsafe_load(file)
    if result is None:
        result = {}
    return result

def saveFile(data:dict, file_name:str):
    with open(f'data/{file_name}.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f)

async def can_dm_user(user: discord.User) -> bool:
    ch = user.dm_channel
    embed = errEmbed('你沒有開啟私訊功能!','請右鍵「緣神有你」 > 隱私設定 > 打開「允許來自伺服器成員的私人訊息」 > 完成')
    embed.set_image(url='https://images-ext-2.discordapp.net/external/yEgI-QTBf4czF65w225am3NbrDeoXDaq6-nLB92NQb8/%3Fraw%3Dtrue/https/github.com/MuMapleTW/mybot/blob/master/image/opendm.png')
    if ch is None:
        ch = await user.create_dm()
    try:
        await ch.send()
    except discord.Forbidden:
        return False, embed
    except discord.HTTPException:
        return True, None