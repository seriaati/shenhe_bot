import discord
from classes import User
def Global():
    global warningColor, purpleColor, footerAuthor, footerImage, timeOutErrorMsg, embedNoAccount, embedNoGroup, users, groups, finds
    warningColor = 0xfc5165
    purpleColor = 0xa68bd3
    footerAuthor = "輸入!help獲得幫助, 如有錯誤, 請回報小雪#5334"
    footerImage = "https://i.imgur.com/DWYpYrd.jpg"
    timeOutErrorMsg = "已取消當前操作, 請在30秒內回答問題"
    embedNoAccount = discord.Embed(title = "😢 該帳號不存在", description="請使用`!register`來註冊帳號, 如有疑問請@小雪", color=warningColor)
    embedNoGroup = discord.Embed(title = "😢 該小組不存在", description="有可能是打錯字了", color = warningColor)
    groups = []
    users = []
    finds = []
    users.append(User(410036441129943050, 901211014, 7368957, "X5VJAbNxdKpMp96s7VGpyIBhSnEJr556d5fFMcT5", "小雪", True, 0))
    users.append(User(507536968121319424, 901445842, 131056669, "7Bzu3KHdYeCDUgWkq1B6YGBcTcV4LXduDFrAL5xn", "eve", True, 0))
    users.append(User(272394461646946304, 901971416, 152761310, "9k3VzBSlHcVfrwrTmGRvmen6PoYAXEDMzBJmKZxS", "tedd", True, 0))
    users.append(User(427346531260301312, 900625278, 82289934, "2TsjIflHb4HIjQMhgby8m4PCLj0Ao7cezEK3CSkC", "ceye", False, 0))
    users.append(User(795329121018183731, 900236198, 27426924, "aD7G6wZx0xOzdMHFFe3on5nD0zNic2DWa8SE9yId", "末野小朋友", True, 0))
    users.append(User(685130936723308624, 900074976, 14609636, "OXR68dPwh0kmIAomgmYMfULeRWvnZK8Ko4FrYYzC", "吐司", True, 0))
    users.append(User(713302663340621924, 902315596, 163977582, "Xg8x05mtLx8m8EouzkKFfuzyYiRpAvsFIpA6Fhrs", "飛機仔", True, 0))
    users.append(User(459189783420207104, 900197166, 11935094, "M7LEG1mMa1EshW5Y9AfgVVWkzKIAfQDuvXE9Cip6", "兔兔", True, 0))
    users.append(User(224441463897849856, 900139600, 19173017, "Myd5h21q0qII9IUQHq5t76aPeWON50LxcuHnejxx", "小flow子", True, 0))
    users.append(User(665092644883398671, 900176548, 19882799, "yTrTsFcg0QF7gylrMXa2e9V8RGcly7HZrsBfYtxJ", "律律龜", True, 0))
    users.append(User(923943597047414834, 902320264, 164115027, "lVwpqYjNoCgA34wCdSOLyxsqWUnQvItzI7L9ePm1", "月野", True, 0))
    users.append(User(891242744989769799, 902423706, 167178342, "Z0D6tKwLIoKIAfk8WBvaatPji9awJfquTQdMSGx0", "楓", False, 0))
    users.append(User(940541341560082433, 903172817, 178853932, "iceApzoLxcrtg9Xfz3tv4m95p1nbSWB9nunprVCa", "小羽", True, 0))
    users.append(User(941324684350357544, 902517150, 45128474, "SEhFSxn40QjOz1P4LOW09tdGQ1p1fDfPBEzfOJgW", "火鳥", True, 0))
    users.append(User(591402468307501200, 901855594, 101672714, "h1e9bkoQXQVHCA8wGOa0gXvcsDhBZ51ZTHMRXR00", "Regator47", True, 0))

def setFooter(embed):
    Global()
    embed.set_footer(text=footerAuthor,icon_url=footerImage)

def defaultEmbed(title, message):
    Global()
    return discord.Embed(title = title, description = message, color = purpleColor)