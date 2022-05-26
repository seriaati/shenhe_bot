import asyncio
import random
import time
from random import randint

from discord import (ButtonStyle, Interaction, Member, Message, SelectOption,
                     Thread, app_commands)
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Button, Select, View, button
from utility.FlowApp import flow_app
from utility.GeneralPaginator import GeneralPaginator
from utility.utils import ayaakaaEmbed, defaultEmbed, log, openFile, saveFile

global debug_toggle
debug_toggle = False


class FishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    global fish_list, fish_flow_list, fish_image_list
    fish_flow_list = ['1', '2', '2', '2', '2', '5', '5', '7', '10', '20']
    fish_list = ['虱目魚', '鮭魚', '鱈魚', '鮪魚', '鰻魚',
                 '龍蝦', '螃蟹', '心海', '大白鯊', '達達利鴨']
    fish_image_list = [
        'https://www.ocean-treasure.com/wp-content/uploads/2021/06/Milkfish.jpg',
        'https://cdn-fgbal.nitrocdn.com/KhVbtyNBpSvxGKkBoxbcDIRslLpQdgCA/assets/static/optimized/wp-content/uploads/2021/08/1daf341ee1fca75bef8327e080fa5b21.Salmon-Fillet-1-1-1536x1536.jpg',
        'https://seafoodfriday.hk/wp-content/uploads/2021/08/Cod-Fillet-1.jpg',
        'https://cdn-fgbal.nitrocdn.com/KhVbtyNBpSvxGKkBoxbcDIRslLpQdgCA/assets/static/optimized/wp-content/uploads/2021/08/327f113f6c4342a982213da7e1dfd5d8.Tuna-Fillet-1.jpg',
        'https://www.boilingtime.com/img/0630/f.jpg',
        'https://seafoodfriday.hk/wp-content/uploads/2021/08/Red-Lobster-1-1536x1536.jpg',
        'https://www.freshexpressonline.com/media/catalog/product/cache/cce444513434d709cad419cac6756dc1/8/0/804001004.jpg',
        'https://assets2.rockpapershotgun.com/genshin-impact-sangonomiya-kokomi.jpg/BROK/thumbnail/1200x1200/quality/100/genshin-impact-sangonomiya-kokomi.jpg',
        'https://static01.nyt.com/images/2020/08/12/multimedia/00xp-shark/00xp-shark-mediumSquareAt3X.jpg',
        'https://c.tenor.com/blHN79J-floAAAAd/ducktaglia-duck.gif'
    ]

    def generate_fish_embed(self, index: int):  # 製造摸魚embed
        if index >= 0 and index <= 4 or index == 7:
            result = ayaakaaEmbed(
                fish_list[index],
                f'是可愛的**{fish_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_list[index]}**有機率獲得 {fish_flow_list[index]} flow幣'
            )
            # e.g. 是可愛的鮭魚！要摸摸看嗎?
            #     摸鮭魚有機率獲得 2 flow幣
        else:
            result = ayaakaaEmbed(
                fish_list[index],
                f'是野生的**{fish_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_list[index]}**有機率獲得或損失 {fish_flow_list[index]} flow幣'
            )
            # e.g. 是野生的達達利鴨！要摸摸看嗎?
            #     摸達達利鴨有機率獲得或損失 20 flow幣
        result.set_image(url=fish_image_list[index])
        return result

    class TouchFishButton(Button):  # 摸魚按鈕
        def __init__(self, index: int):
            super().__init__(style=ButtonStyle.blurple,
                             label=f'撫摸可愛的{fish_list[index]}')
            self.index = index

        async def callback(self, interaction: Interaction):
            self.view.stop()
            self.disabled = True
            await interaction.response.edit_message(view=self.view)

            await interaction.channel.send(f'{interaction.user.mention} 摸到**{fish_list[self.index]}**了！')
            # e.g. @綾霞 摸到虱目魚了！

            value = randint(1, 100)  # Picks a random number from 1 - 100

            # 摸虱目魚有機率獲得 1 flow幣

            if self.index == 0:  # [0] 虱目魚
                if value <= 60:  # 60% Chance of increasing flow amount by 1
                    flow_app.transaction(interaction.user.id, 1)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 1 flow幣!', ephemeral=True)
                    # e.g. 摸虱目魚摸到 1 flow幣!
                else:
                    await interaction.followup.send(f'單純的摸魚而已, 沒有摸到flow幣 qwq', ephemeral=True)

            # 摸鮭魚, 鱈魚, 鮪魚 或 鰻魚有機率獲得 2 flow幣
            # [1] 鮭魚, [2] 鱈魚, [3] 鮪魚, [4] 鰻魚
            elif self.index >= 1 and self.index <= 4:
                if value <= 30:  # 30% Chance of increasing flow amount by 2
                    flow_app.transaction(interaction.user.id, 2)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 2 flow幣!', ephemeral=True)
                    # e.g. 摸鮭魚摸到 2 flow幣!
                else:
                    await interaction.followup.send('單純的摸魚而已, 沒有摸到flow幣 qwq', ephemeral=True)

            # 摸龍蝦 或 螃蟹有機率獲得或損失 5 flow幣
            # [5] 龍蝦, [6] 螃蟹,
            elif self.index >= 5 and self.index <= 6:
                if value <= 50:  # 50% Chance of increasing flow amount by 5
                    flow_app.transaction(interaction.user.id, 5)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 5 flow幣!', ephemeral=True)
                    # e.g. 摸龍蝦摸到 5 flow幣!
                else:  # 50% Chance of decreasing flow amount by 5
                    flow_app.transaction(interaction.user.id, -5)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**鉗到了，損失了 5 flow幣 qwq', ephemeral=True)
                    # e.g. 被龍蝦鉗到了，損失了 5 flow幣 qwq

            # 摸心海有機率獲得或損失 7 flow幣
            # [7] 心海
            elif self.index == 7:
                if value <= 50:  # 50% Chance of increasing flow amount by 7
                    flow_app.transaction(interaction.user.id, 7)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 7 flow幣!', ephemeral=True)
                    # e.g. 摸心海摸到 7 flow幣!
                else:  # 50% Chance of decreasing flow amount by 7
                    flow_app.transaction(interaction.user.id, -7)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**打飛了，損失了 7 flow幣 qwq', ephemeral=True)
                    # e.g. 被心海打飛了，損失了 7 flow幣 qwq

            # 摸大白鯊有機率獲得或損失 10 flow幣
            elif self.index == 8:  # [8] 大白鯊
                if value <= 50:  # 50% Chance of increasing flow amount by 10
                    flow_app.transaction(interaction.user.id, 10)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 10 flow幣!', ephemeral=True)
                    # e.g. 摸大白鯊 摸到 10 flow幣!
                else:  # 50% Chance of decreasing flow amount by 10
                    flow_app.transaction(interaction.user.id, -10)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**咬到了，損失了 10 flow幣 qwq', ephemeral=True)
                    # e.g. 被大白鯊咬到了，損失了 10 flow幣 qwq

            # 摸達達利鴨有機率獲得或損失 20 flow幣
            elif self.index == 9:  # [9] 達達利鴨
                if value <= 50:  # 50% Chance of increasing flow amount by 20
                    flow_app.transaction(interaction.user.id, 20)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 20 flow幣!', ephemeral=True)
                    # e.g. 摸達達利鴨摸到 30 flow幣!
                else:  # 50% Chance of decreasing flow amount by 20
                    flow_app.transaction(interaction.user.id, -20)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**偷襲，損失了 20 flow幣 qwq', ephemeral=True)
                    # e.g. 被達達利鴨偷襲，損失了 30 flow幣 qwq

    class TouchFish(View):  # 摸魚view
        def __init__(self, index: str):
            super().__init__(timeout=None)
            self.add_item(FishCog.TouchFishButton(index))

    def get_fish_choices():  # 取得所有魚種
        choices = []
        for fish in fish_list:
            choices.append(Choice(name=fish, value=fish_list.index(fish)))
        return choices

    @commands.Cog.listener()
    async def on_message(self, message):  # 機率放魚
        if message.author == self.bot.user:
            return
        random_number = randint(1, 100) if not debug_toggle else 1
        if random_number == 1 and not isinstance(message.channel, Thread):
            index = randint(0, len(fish_list)-1)
            touch_fish_view = FishCog.TouchFish(index)
            await message.channel.send(embed=self.generate_fish_embed(index), view=touch_fish_view)

   # /fish
    # @app_commands.command(name='fish', description='緊急放出一條魚讓人摸')
    # @app_commands.rename(fish_type='魚種')
    # @app_commands.describe(fish_type='選擇要放出的魚種')
    # @app_commands.choices(fish_type=get_fish_choices())
    # @app_commands.checks.has_role('小雪團隊')
    # async def release_fish(self, i: Interaction, fish_type: int):
    #     await self.bot.log.send(log(False, False, 'Release Fish', i.user.id))
    #     touch_fish_view = FishCog.TouchFish(fish_type)
    #     await i.response.send_message(embed=self.generate_fish_embed(fish_type), view=touch_fish_view)

    # @release_fish.error
    # async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
    #     if isinstance(e, app_commands.errors.MissingRole):
    #         await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    def generate_fishing_embed(fishing: bool, area: str):
        areas = openFile('fish/areas')
        image_url = ''
        if not fishing:
            image_url = areas[area]
        else:
            image_url = 'https://c.tenor.com/q_v2D9_1p1kAAAAC/fishing-genshin.gif'
        t = time.strftime("%I:%M %p")
        embed = defaultEmbed(f'{t} ({area})')
        embed.set_image(url=image_url)
        return embed

    def random_fish(self, item_dic, total_weight):
        score = random.randint(1, total_weight)
        range_max = 0
        for item_key, weight in item_dic.items():
            range_max += weight
            if score <= range_max:
                return item_key

    def get_fish(self, item_dic, times):
        total_weight = 0
        for value in item_dic.values():
            total_weight += value
        results = []
        for i in range(times):
            results.append(self.random_fish(self, item_dic, total_weight))
        return results

    class FishingView(View):
        def __init__(self, author: Member, area: str, rod: str):
            super().__init__(timeout=None)
            self.author = author
            self.area = area
            self.rod = rod
            areas = openFile('fish/areas')
            self.areas = areas
            inventory = openFile('fish/inventory')
            rods = inventory[author.id]['釣竿']
            self.add_item(FishCog.RodSelect(rods, self.area))
            self.add_item(FishCog.RodDisplayButton(rod))

        async def interaction_check(self, interaction: Interaction) -> bool:
            return interaction.user.id == self.author.id

        @button(label='釣魚', style=ButtonStyle.blurple)
        async def get_fish(self, i: Interaction, button: Button):
            fish_dict = openFile('fish/fish_weight')
            button.disabled = True
            self.open_area_select.disabled = True
            await i.response.edit_message(embed=FishCog.generate_fishing_embed(True, self.area), view=self)
            await asyncio.sleep(2.0)
            fish_exp = openFile('fish/fish_exp')
            pull_fish = FishCog.get_fish(FishCog, fish_dict[self.area], 1)[0]
            put_fish_view = FishCog.PutFishView(pull_fish)
            FishCog.create_user_stats(i.user.id)
            user_stats = openFile('fish/user_stats')
            if self.rod == '冰霜釣竿' and self.area == '寒冰雪山':
                pull_fish_exp = int(fish_exp[pull_fish])*1.1
            else:
                pull_fish_exp = int(fish_exp[pull_fish])
            user_stats[i.user.id]['exp'] += pull_fish_exp
            await i.followup.send(embed=defaultEmbed(f'釣到了 {pull_fish}', f'獲得**{round(pull_fish_exp, 1)}**點經驗值'), view=put_fish_view, ephemeral=True)
            fish_rarity = 0
            all_fish = openFile('fish/all_fish')
            for rarity_int, fishes in all_fish.items():
                for fish in fishes:
                    if pull_fish == fish:
                        fish_rarity = rarity_int
                        break
                else:
                    continue
                break
            user_stats[i.user.id][str(fish_rarity)] += 1
            saveFile(user_stats, 'fish/user_stats')
            button.disabled = False
            self.open_area_select.disabled = False
            await i.edit_original_message(embed=FishCog.generate_fishing_embed(False, self.area), view=self)

        @button(label='開船', style=ButtonStyle.blurple)
        async def open_area_select(self, i: Interaction, button: Button):
            view = FishCog.AreaSelectView(self.areas, self.rod, i.message)
            await i.response.send_message(view=view, ephemeral=True)

    def create_fish_pond(user_id: int):
        fish_pond = openFile('fish/user_fish_pond')
        if user_id not in fish_pond:
            fish_pond[user_id] = {}
            saveFile(fish_pond, 'fish/user_fish_pond')
        return fish_pond

    def create_fish(user_id: int, fish: str, function: str):
        if function == 'pond':
            fish_pond = openFile('fish/user_fish_pond')
            if fish not in fish_pond[user_id]:
                fish_pond[user_id][fish] = 0
                saveFile(fish_pond, 'fish/user_fish_pond')
            return fish_pond
        elif function == 'inventory':
            inventory = openFile('fish/inventory')
            if fish not in inventory[user_id]['魚']:
                inventory[user_id]['魚'][fish] = 0
                saveFile(inventory, 'fish/inventory')
            return inventory

    class PutFishView(View):
        def __init__(self, fish: str):
            self.fish = fish
            super().__init__(timeout=None)

        @button(label='放進魚塘', style=ButtonStyle.blurple)
        async def put_to_pond(self, i: Interaction, button: Button):
            fish_pond = FishCog.create_fish_pond(i.user.id)
            fish_pond = FishCog.create_fish(i.user.id, self.fish, 'pond')
            fish_pond[i.user.id][self.fish] += 1
            saveFile(fish_pond, 'fish/user_fish_pond')
            await i.response.send_message(embed=defaultEmbed(f'{self.fish} 已放入魚塘', '輸入`/fish pond`即可查看'), ephemeral=True)

        @button(label='收進背包', style=ButtonStyle.blurple)
        async def put_to_inventory(self, i: Interaction, button: Button):
            inventory = FishCog.create_inventory(i.user.id)
            inventory = FishCog.create_fish(i.user.id, self.fish, 'inventory')
            inventory[i.user.id]['魚'][self.fish] += 1
            saveFile(inventory, 'fish/inventory')
            await i.response.send_message(embed=defaultEmbed(f'{self.fish} 已放入背包', '輸入`/fish bag`即可查看'), ephemeral=True)

    class RodDisplayButton(Button):
        def __init__(self, rod: str):
            super().__init__(label=f'正在使用 {rod}', disabled=True)

    class AreaSelectView(View):
        def __init__(self, area_dict: dict, rod: str, original_message: Message):
            self.area_dict = area_dict
            self.rod = rod
            self.original_message = original_message
            super().__init__(timeout=None)
            self.add_item(FishCog.AreaSelect(
                self.area_dict, self.rod, self.original_message))

    class AreaSelect(Select):
        def __init__(self, area_dict: dict, rod: str, original_message: Message):
            self.rod = rod
            options = []
            self.original_message = original_message
            for area_name, value in area_dict.items():
                options.append(SelectOption(label=area_name, value=area_name))
            super().__init__(placeholder='要前往的區域', options=options)

        async def callback(self, i: Interaction):
            await self.original_message.edit(embed=FishCog.generate_fishing_embed(False, self.values[0]), view=FishCog.FishingView(i.user, self.values[0], self.rod))
            await i.response.send_message(f'✈️ 已成功抵達 {self.values[0]}', ephemeral=True)

    class RodSelect(Select):
        def __init__(self, rod_dict: dict, area: str):
            all_items = openFile('fish/all_items')
            self.area = area
            options = []
            for rod, count in rod_dict.items():
                options.append(SelectOption(
                    label=rod, description=all_items['釣竿'][rod]['effect'], value=rod))
            super().__init__(placeholder='選擇要使用的釣竿', options=options)

        async def callback(self, i: Interaction):
            await i.response.edit_message(embed=FishCog.generate_fishing_embed(False, self.area), view=FishCog.FishingView(i.user, self.area, self.values[0]))

    @app_commands.command(name='fishing', description='釣魚')
    async def fishing(self, i: Interaction):
        inventory = FishCog.create_inventory(i.user.id)
        areas = openFile('fish/areas')
        rods = inventory[i.user.id]['釣竿']
        view = FishCog.FishingView(i.user, list(areas.keys())[
                                   0], list(rods.keys())[0])
        await i.response.send_message(embed=FishCog.generate_fishing_embed(False, (list(areas.keys())[0])), view=view)

    fish = app_commands.Group(name="fish", description="flow魚系統")

    def create_inventory(user_id: int):
        inventory = openFile('fish/inventory')
        if user_id not in inventory:
            inventory[user_id] = {}
            inventory[user_id]['釣竿'] = {'雲杉釣竿': 1}
            inventory[user_id]['魚'] = {}
            saveFile(inventory, 'fish/inventory')
        return inventory

    @fish.command(name='bag', description='查看背包')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他人的背包')
    async def fish_bag(self, i: Interaction, member: Member = None):
        member = member or i.user
        inventory = FishCog.create_inventory(member.id)
        embed = defaultEmbed('背包')
        for category, items in inventory[member.id].items():
            item_str = ''
            for item, count in items.items():
                item_str += f'• {item} x{count}\n'
            embed.add_field(name=category, value=item_str, inline=False)
        embed.set_author(name=member, icon_url=member.avatar)
        await i.response.send_message(embed=embed)

    def generate_item_embeds(category_name: str):
        all_items = openFile('fish/all_items')
        embeds = []
        for category, items in all_items.items():
            if category == category_name:
                for item, value in items.items():
                    embed = defaultEmbed(item, f'「{value["desc"]}」')
                    embed.add_field(name='效果', value=value["effect"])
                    embeds.append(embed)
        return embeds

    class ItemCategoryView(View):
        def __init__(self, items_dict: dict):
            super().__init__(timeout=None)
            self.add_item(FishCog.ItemCategorySelect(items_dict))

    class ItemCategorySelect(Select):
        def __init__(self, items_dict: dict):
            options = []
            for category, items in items_dict.items():
                options.append(SelectOption(label=category, value=category))
            super().__init__(placeholder='選擇要查看的物品分類', options=options)

        async def callback(self, i: Interaction):
            await GeneralPaginator(i, FishCog.generate_item_embeds(self.values[0])).start(embeded=True)

    @fish.command(name='items', description='查看所有可以取得的物品')
    async def fish_items(self, i: Interaction):
        all_items = openFile('fish/all_items')
        view = FishCog.ItemCategoryView(all_items)
        await i.response.send_message(view=view)

    def generate_fish_detail_embed(rarity_input: int):
        all_fish = openFile('fish/all_fish')
        fish_exp = openFile('fish/fish_exp')
        fish_str = ''
        for rarity, fish in all_fish.items():
            if int(rarity) == int(rarity_input):
                for f in fish:
                    fish_str += f'• {f} ({fish_exp[f]}exp.)\n'
        embed = defaultEmbed(f'{rarity_input}★魚', fish_str)
        return embed

    class FishRarityView(View):
        def __init__(self, fish_dict: dict):
            super().__init__(timeout=None)
            self.add_item(FishCog.FishRaritySelect(fish_dict))

    class FishRaritySelect(Select):
        def __init__(self, fish_dict: dict):
            options = []
            for rarity, fish in fish_dict.items():
                options.append(SelectOption(
                    label=f'{rarity}★魚 ({len(fish)})', value=rarity))
            super().__init__(placeholder='選擇要查看的稀有度', options=options)

        async def callback(self, i: Interaction):
            await i.response.edit_message(embed=FishCog.generate_fish_detail_embed(self.values[0]))

    @fish.command(name='all', description='查看魚類圖鑑')
    async def fish_all(self, i: Interaction):
        all_fish = openFile('fish/all_fish')
        view = FishCog.FishRarityView(all_fish)
        await i.response.send_message(view=view)

    def create_user_stats(user_id: int):
        user_stats = openFile('fish/user_stats')
        if user_id not in user_stats:
            user_stats[user_id] = {
                'exp': 0,
                '1': 0,
                '2': 0,
                '3': 0,
                '4': 0,
                '5': 0
            }
        saveFile(user_stats, 'fish/user_stats')
        return user_stats

    def calculate_level(exp: int):
        level = 0
        level_max_exp = 10
        while exp >= level_max_exp:
            exp -= level_max_exp
            level += 1
            level_max_exp *= 1.2
        return level, exp, level_max_exp

    @fish.command(name='stats', description='查看釣魚數據')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他人的釣魚數據')
    async def fish_stats(self, i: Interaction, member: Member = None):
        member = member or i.user
        user_stats = FishCog.create_user_stats(member.id)
        user_level, remaining_exp, level_max_exp = FishCog.calculate_level(
            int(user_stats[member.id]["exp"]))
        fish_rarity_str = ''
        for rarity in range(1, 6):
            fish_rarity_str += f'{rarity}★: {user_stats[member.id][f"{rarity}"]}\n'
        embed = defaultEmbed(
            '釣魚數據',
            f'目前等級: {user_level} ({int(remaining_exp)}/{int(level_max_exp)})\n{fish_rarity_str}'
        )
        embed.set_author(name=member, icon_url=member.avatar)
        await i.response.send_message(embed=embed)

    @fish.command(name='pond', description='查看魚塘')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他人的魚塘')
    async def fish_pond(self, i: Interaction, member: Member = None):
        member = member or i.user
        fish_pond = FishCog.create_fish_pond(member.id)
        fish_str = ''
        for fish, fish_count in fish_pond[member.id].items():
            fish_str += f'• {fish} x{fish_count}\n'
        embed = defaultEmbed(f'{member}的魚塘')
        embed.set_image(url='https://i.imgur.com/5UGJ70T.gif')
        await i.response.send_message(embed=embed)
        embed = defaultEmbed('魚塘裡的魚', fish_str)
        await i.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FishCog(bot))
