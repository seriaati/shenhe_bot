import getpass
import uuid

owner = getpass.getuser()
import sys

sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import global_vars
import yaml

global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form

with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', encoding = 'utf-8') as file:
    bank = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', encoding = 'utf-8') as file:
    shop = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/log.yaml', encoding = 'utf-8') as file:
    logs = yaml.full_load(file)

class FlowShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def shop(self, ctx):
        if ctx.invoked_subcommand is None:
            itemStr = ""
            count = 1
            for item in shop:
                itemStr = itemStr + f"{count}. {item['name']} - {item['flow']} flow ({item['current']}/{item['max']})\n||{item['uuid']}||\n"
                count += 1
            embed = global_vars.defaultEmbed("🛒 flow商店", itemStr)
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)

    @shop.command()
    @commands.has_role("小雪團隊")
    async def newitem(self, ctx):
        form = Form(ctx, '新增商品', cleanup=True)
        form.add_question('商品名稱?', 'name')
        form.add_question('flow幣價格?', 'flow')
        form.add_question('最大購買次數?', 'max')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        id = uuid.uuid1()
        newItem = {'name': result.name, 'flow': int(result.flow), 'current': 0, 'max': int(result.max), 'uuid': str(id)}
        shop.append(newItem)
        with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
            yaml.dump(shop, file)
        await ctx.send(f"商品{result.name}新增成功")

    @shop.command()
    @commands.has_role("小雪團隊")
    async def removeitem(self, ctx, *, arg=''):
        for item in shop:
            if item['uuid'] == arg:
                shop.remove(item)
                with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
                    yaml.dump(shop, file)
                await ctx.send("商品刪除成功")
                break

    @shop.command()
    async def buy(self, ctx):
        itemStr = ""
        count = 1
        for item in shop:
            itemStr = itemStr + f"{count}. {item['name']} - {item['flow']} flow ({item['current']}/{item['max']})\n"
            count += 1
        form = Form(ctx, '要購買什麼商品?(輸入數字)', cleanup=True)
        form.add_question(f'{itemStr}', 'number')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        pos = int(result.number) - 1
        found = False
        for user in users:
            if user['discordID'] == ctx.author.id:
                found = True
                itemPrice = int(shop[pos]['flow'])
                if user['flow'] < itemPrice:
                    await ctx.send(f"{ctx.author.mention} 你的flow幣不足夠購買這項商品")
                    return
                if shop[pos]['current'] >= shop[pos]['max']:
                    await ctx.send(f"{ctx.author.mention} 這個商品已經售罄了")
                    return
                else:
                    shop[pos]['current'] += 1
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(shop, file)
                    newLog = {'item': shop[pos]['name'], 'flow': int(shop[pos]['flow']), 'buyerID': ctx.author.id, 'itemUUID': shop[pos]['uuid']}
                    logs.append(newLog)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/log.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(logs, file)
                    itemPrice = int(shop[pos]['flow'])
                    user['flow'] -= itemPrice
                    bank['flow'] += itemPrice
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(bank, file)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(users, file)
                    await ctx.send(f"商品 {shop[pos]['name']} 購買成功, 詳情請查看私訊")
                    await ctx.author.send(f"您已在flow商城購買了 {shop[pos]['name']} 商品, 請將下方的收據截圖並寄給小雪或律律來兌換商品")
                    embed = global_vars.defaultEmbed("📜 購買證明",f"購買人: {ctx.author.mention}\n購買人ID: {ctx.author.id}\n商品: {shop[pos]['name']}\nUUID: {shop[pos]['uuid']}\n價格: {shop[pos]['flow']}")
                    global_vars.setFooter(embed)
                    await ctx.author.send(embed=embed)
                    break
        if found == False:
            if not ctx.author.bot:
                discordID = ctx.author.id
                user = self.bot.get_user(discordID)
                flowCog = self.bot.get_cog('FlowCog')
                await flowCog.register(user, discordID)
                await ctx.send("你本來沒有帳號, 現在申鶴幫你做了一個, 再打一次`!shop buy`試試看")
            else:
                return

    @shop.command()
    @commands.has_role("小雪團隊")
    async def log(self, ctx):
        for log in logs:
            user = self.bot.get_user(int(log['buyerID']))
            embed = global_vars.defaultEmbed("購買紀錄",f"商品: {log['item']}\n價格: {log['flow']}\n購買人: {user.mention}\n購買人ID: {log['buyerID']}\n商品UUID: {log['itemUUID']}")
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)

    @shop.command()
    @commands.has_role("小雪團隊")
    async def clear(self, ctx, uuid):
        if uuid == "all":
            for item in shop:
                item['current'] = 0
                with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
                    yaml.dump(shop, file)
            await ctx.send(f"已將所有商品的購買次數清零")
            return
        for item in shop:
            if item['uuid'] == uuid:
                item['current'] = 0
                with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
                    yaml.dump(shop, file)
                await ctx.send(f"已將 {item['name']} 的購買次數設為0")
                break

def setup(bot):
    bot.add_cog(FlowShopCog(bot))
