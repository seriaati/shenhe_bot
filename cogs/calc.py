from typing import Any

import aiosqlite
from debug import DefaultView
from discord import (ButtonStyle, Interaction, Member, SelectOption,
                     app_commands)
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput
from utility.apps.GenshinApp import GenshinApp
from utility.utils import (defaultEmbed, errEmbed, getCharacter, getClient,
                           getConsumable, getWeapon)


class CalcCog(commands.GroupCog, name='calc'):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.genshin_app = GenshinApp(bot.db, bot)
        
    class CalcultorElementButtonView(DefaultView):
        def __init__(self, author: Member, chara_list: list, item_type: str):
            super().__init__(timeout=None)
            self.author = author
            for i in range(0, 6):
                self.add_item(CalcCog.CalcultorElementButton(
                    i, chara_list, item_type))

        async def interaction_check(self, i: Interaction) -> bool:
            return i.user.id == self.author.id

    class CalcultorElementButton(Button):
        def __init__(self, index: int, chara_list: list, item_type: str):
            self.element_name_list = ['Anemo', 'Cryo',
                                      'Electro', 'Geo', 'Hydro', 'Pyro']
            element_emojis = ['<:WIND_ADD_HURT:982138235239137290>', '<:ICE_ADD_HURT:982138229140635648>', '<:ELEC_ADD_HURT:982138220248711178>',
                              '<:ROCK_ADD_HURT:982138232391237632>', '<:WATER_ADD_HURT:982138233813098556>', '<:FIRE_ADD_HURT:982138221569900585>']
            self.index = index
            self.chara_list = chara_list
            self.item_type = item_type
            super().__init__(
                emoji=element_emojis[index], style=ButtonStyle.gray, row=index % 2)

        async def callback(self, i: Interaction):
            element_chara_list = []
            for chara in self.chara_list:
                if chara[2] == self.element_name_list[self.index]:
                    element_chara_list.append(chara)
            self.view.element_chara_list = element_chara_list
            self.view.item_type = self.item_type
            await i.response.defer()
            self.view.stop()

    class CalculatorItems(DefaultView):
        def __init__(self, author: Member, item_list: list, item_type: str):
            super().__init__(timeout=None)
            self.author = author
            self.add_item(CalcCog.CalculatorItemSelect(
                item_list, item_type))

        async def interaction_check(self, i: Interaction) -> bool:
            return self.author.id == i.user.id

    class CalculatorItemSelect(Select):
        def __init__(self, items, item_type):
            options = []
            for item in items:
                options.append(SelectOption(
                    label=item[0], value=item[1], emoji=getCharacter(name=item[0])['emoji']))
            super().__init__(placeholder=f'選擇{item_type}',
                             min_values=1, max_values=1, options=options)

        async def callback(self, i: Interaction):
            modal = CalcCog.LevelModal()
            await i.response.send_modal(modal)
            await modal.wait()
            self.view.target = int(modal.chara.value)
            self.view.a = int(modal.attack.value)
            self.view.e = int(modal.skill.value)
            self.view.q = int(modal.burst.value)
            self.view.value = self.values[0]
            self.view.stop()

    class LevelModal(Modal):
        chara = TextInput(
            label='角色目標等級',
            placeholder='例如: 90',
        )

        attack = TextInput(
            label='普攻目標等級',
            placeholder='例如: 10',
        )

        skill = TextInput(
            label='元素戰技(E)目標等級',
            placeholder='例如: 8',
        )

        burst = TextInput(
            label='元素爆發(Q)目標等級',
            placeholder='例如: 9',
        )

        def __init__(self) -> None:
            super().__init__(title='計算資料輸入', timeout=None)

        async def on_submit(self, interaction: Interaction) -> None:
            await interaction.response.defer()

    def check_level_validity(self, target: int, a: int, e: int, q: int):
        if target > 90:
            return False, errEmbed('原神目前的最大等級是90唷')
        if a > 10 or e > 10 or q > 10:
            return False, errEmbed('天賦的最高等級是10唷', '有命座請自行減3')
        if target <= 0:
            return False, errEmbed('原神角色最少至少要1等唷')
        if a <= 0 or e <= 0 or q <= 0:
            return False, errEmbed('天賦至少要1等唷')
        else:
            return True, None

    class AddMaterialsView(DefaultView):
        def __init__(self, db: aiosqlite.Connection, disabled: bool, author: Member, materials):
            super().__init__(timeout=None)
            self.add_item(CalcCog.AddTodoButton(disabled, db, materials))
            self.author = author

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != self.author.id:
                await interaction.response.send_message(embed=errEmbed('這不是你的計算視窗', '輸入 `/calc` 來計算'), ephemeral=True)
            return interaction.user.id == self.author.id

    class AddTodoButton(Button):
        def __init__(self, disabled: bool, db: aiosqlite.Connection, materials):
            super().__init__(style=ButtonStyle.blurple, label='新增到代辦清單', disabled=disabled)
            self.db = db
            self.materials = materials

        async def callback(self, i: Interaction) -> Any:
            c = await self.db.cursor()
            await c.execute('SELECT COUNT(item) FROM todo WHERE user_id = ?', (i.user.id,))
            count = (await c.fetchone())[0]
            if count >= 125:
                return await i.response.send_message(embed=errEmbed(message='請輸入 `/todo` 並使用「刪除素材」按鈕').set_author(name='代辦清單可存素材數量已達最大值 (125)', icon_url=i.user.avatar))
            for item_data in self.materials:
                await c.execute('SELECT count FROM todo WHERE user_id = ? AND item = ?', (i.user.id, item_data[0]))
                count = await c.fetchone()
                if count is None:
                    await c.execute('INSERT INTO todo (user_id, item, count) VALUES (?, ?, ?)', (i.user.id, item_data[0], item_data[1]))
                else:
                    count = count[0]
                    await c.execute('UPDATE todo SET count = ? WHERE user_id = ? AND item = ?', (count+int(item_data[1]), i.user.id, item_data[0]))
            await self.db.commit()
            await i.response.send_message(embed=defaultEmbed(message='使用`/todo`指令來查看你的代辦事項').set_author(name='代辦事項新增成功', icon_url=i.user.avatar), ephemeral=True)

    @app_commands.command(name='notown所有角色', description='計算一個自己不擁有的角色所需的素材')
    async def calc_notown(self, i: Interaction):
        client = getClient()
        charas = await client.get_calculator_characters()
        chara_list = []
        for chara in charas:
            chara_list.append([chara.name, chara.id, chara.element])
        button_view = CalcCog.CalcultorElementButtonView(
            i.user, chara_list, '角色')
        embed = defaultEmbed().set_author(name='選擇角色的元素', icon_url=i.user.avatar)
        await i.response.send_message(embed=embed, view=button_view)
        await button_view.wait()
        select_view = CalcCog.CalculatorItems(
            i.user, button_view.element_chara_list, button_view.item_type)
        embed = defaultEmbed().set_author(name='選擇角色', icon_url=i.user.avatar)
        await i.edit_original_message(embed=embed, view=select_view)
        await select_view.wait()
        valid, error_msg = self.check_level_validity(
            select_view.target, select_view.a, select_view.e, select_view.q)
        if not valid:
            await i.followup.send(embed=error_msg, ephemeral=True)
            return
        chara_name = ''
        for chara in chara_list:
            if int(select_view.value) == int(chara[1]):
                chara_name = chara[0]
        character = await client.get_calculator_characters(query=chara_name)
        character = character[0]
        embed = defaultEmbed()
        embed.set_author(name='計算結果', icon_url=i.user.avatar)
        embed.set_thumbnail(url=character.icon)
        embed.add_field(
            name='計算內容',
            value=f'角色等級 1 ▸ {select_view.target}\n'
            f'普攻等級 1 ▸ {select_view.a}\n'
            f'元素戰技(E)等級 1 ▸ {select_view.e}\n'
            f'元素爆發(Q)等級 1 ▸ {select_view.q}',
            inline=False
        )
        talents = await client.get_character_talents(select_view.value)
        builder = client.calculator()
        builder.set_character(select_view.value, current=1,
                              target=select_view.target)
        builder.add_talent(talents[0].group_id,
                           current=1, target=select_view.a)
        builder.add_talent(talents[1].group_id,
                           current=1, target=select_view.e)
        builder.add_talent(talents[2].group_id,
                           current=1, target=select_view.q)
        cost = await builder.calculate()
        materials = []
        value = ''
        for consumable in cost.character:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='角色所需素材', value=value, inline=False)
        value = ''
        for consumable in cost.talents:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='天賦所需素材', value=value, inline=False)
        disabled = True if len(materials) == 0 else False
        view = CalcCog.AddMaterialsView(
            self.bot.db, disabled, i.user, materials)
        await i.edit_original_message(embed=embed, view=view)

    @app_commands.command(name='character擁有角色', description='個別計算一個自己擁有的角色所需的素材 (需註冊)')
    async def calc_character(self, i: Interaction):
        exists = await self.genshin_app.userDataExists(i.user.id)
        if not exists:
            return await i.response.send_message(embed=errEmbed(message='請先使用 `/register` 指令註冊帳號').set_author(name='找不到使用者資料!', icon_url=i.user.avatar))
        client, uid, user = await self.genshin_app.getUserCookie(i.user.id)
        try:
            charas = await client.get_calculator_characters(sync=True)
        except:
            embed = defaultEmbed(
                '等等!',
                '你需要先進行下列的操作才能使用此功能\n'
                '由於米哈遊非常想要大家使用他們的 hoyolab APP\n'
                '所以以下操作只能在手機上用 APP 進行 <:penguin_dead:978841159147343962>\n'
                'APP 下載連結: [IOS](https://apps.apple.com/us/app/hoyolab/id1559483982) [Android](https://play.google.com/store/apps/details?id=com.mihoyo.hoyolab&hl=en&gl=US)')
            embed.set_image(url='https://i.imgur.com/GiYbVwU.gif')
            await i.response.send_message(embed=embed, ephemeral=True)
            return
        chara_list = []
        for chara in charas:
            chara_list.append([chara.name, chara.id, chara.element])
        button_view = CalcCog.CalcultorElementButtonView(
            i.user, chara_list, '角色')
        embed = defaultEmbed().set_author(name='選擇角色的元素', icon_url=i.user.avatar)
        await i.response.send_message(embed=embed, view=button_view)
        await button_view.wait()
        embed = defaultEmbed().set_author(name='選擇角色', icon_url=i.user.avatar)
        select_view = CalcCog.CalculatorItems(
            i.user, button_view.element_chara_list, button_view.item_type)
        await i.edit_original_message(embed=embed, view=select_view)
        await select_view.wait()
        valid, error_msg = self.check_level_validity(
            select_view.target, select_view.a, select_view.e, select_view.q)
        if not valid:
            return await i.followup.send(embed=error_msg, ephemeral=True)
        chara_name = ''
        for chara in chara_list:
            if int(select_view.value) == int(chara[1]):
                chara_name = chara[0]
        details = await client.get_character_details(select_view.value)
        character = (await client.get_calculator_characters(query=chara_name, sync=True))[0]
        if character.level > select_view.target:
            return await i.followup.send(embed=errEmbed().set_author(name='目前等級大於目標等級', icon_url=i.user.avatar))
        talent_targets = [select_view.a, select_view.e, select_view.q]
        for index in range(0, 3):
            if details.talents[index].level > talent_targets[index]:
                return await i.followup.send(embed=errEmbed().set_author(name='目前等級大於目標等級', icon_url=i.user.avatar))
        embed = defaultEmbed().set_author(name='計算結果', icon_url=i.user.avatar)
        embed.set_thumbnail(url=character.icon)
        value = ''
        value += f'角色等級 {character.level} ▸ {select_view.target}\n'
        value += f'普攻等級 {details.talents[0].level} ▸ {select_view.a}\n'
        value += f'元素戰技(E)等級 {details.talents[1].level} ▸ {select_view.e}\n'
        value += f'元素爆發(Q)等級 {details.talents[2].level} ▸ {select_view.q}\n'
        embed.add_field(name='計算內容', value=value, inline=False)
        cost = await (
            client.calculator()
            .set_character(select_view.value, current=character.level, target=select_view.target)
            .with_current_talents(attack=select_view.a, skill=select_view.e, burst=select_view.q)
        )
        materials = []
        value = ''
        for consumable in cost.character:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='角色所需素材', value=value, inline=False)
        value = ''
        for consumable in cost.talents:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='天賦所需素材', value=value, inline=False)
        disabled = True if len(materials) == 0 else False
        view = CalcCog.AddMaterialsView(
            self.bot.db, disabled, i.user, materials)
        await i.edit_original_message(embed=embed, view=view)

    class CalcWeaponView(DefaultView):
        def __init__(self, weapons, author: Member, db: aiosqlite.Connection):
            super().__init__(timeout=None)
            self.author = author
            self.add_item(CalcCog.CalcWeaponSelect(weapons, db))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/calc weapon` 來計算武器所需素材').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar))
            return self.author.id == interaction.user.id

    class CalcWeaponSelect(Select):
        def __init__(self, weapons, db: aiosqlite.Connection):
            options = []
            for w in weapons:
                options.append(SelectOption(
                    label=w.name, value=w.id, emoji=getWeapon(w.id)['emoji']))
            super().__init__(placeholder='選擇武器', options=options)
            self.weapons = weapons
            self.db = db

        async def callback(self, interaction: Interaction) -> Any:
            await interaction.response.send_modal(CalcCog.CalcWeaponModal(self.values[0], self.db))

    class CalcWeaponModal(Modal):
        current = TextInput(
            label='目前等級', placeholder='例如: 1')
        target = TextInput(label='目標等級', placeholder='例如: 90')

        def __init__(self, chosen_weapon: str, db: aiosqlite.Connection) -> None:
            super().__init__(
                title=f'設置{getWeapon(chosen_weapon)["name"]}要計算的等級', timeout=None)
            self.chosen_weapon = chosen_weapon
            self.db = db

        async def on_submit(self, interaction: Interaction) -> None:
            if int(self.current.value) < 1 or int(self.target.value) < 1:
                return await interaction.response.send_message(embed=errEmbed().set_author(name='等級不可小於1', icon_url=interaction.user.avatar), ephemeral=True)
            if int(self.target.value) > 90 or int(self.current.value) > 90:
                return await interaction.response.send_message(embed=errEmbed().set_author(name='等級不可大於90', icon_url=interaction.user.avatar), ephemeral=True)
            client = getClient()
            cost = await (
                client.calculator()
                .set_weapon(self.chosen_weapon, current=int(self.current.value), target=int(self.target.value))
            )
            embed = defaultEmbed().set_author(name='計算結果', icon_url=interaction.user.avatar)
            embed.add_field(
                name='計算內容', value=f'武器: {getWeapon(self.chosen_weapon)["name"]}\n等級: {self.current.value} ▸ {self.target.value}', inline=False)
            materials = []
            value = ''
            for consumable in cost.weapon:
                value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
                materials.append([consumable.name, consumable.amount])
            if value == '':
                value = '不需要任何素材'
            embed.add_field(name='武器所需素材', value=value, inline=False)
            embed.set_thumbnail(url=getWeapon(self.chosen_weapon)["icon"])
            disabled = True if len(materials) == 0 else False
            view = CalcCog.AddMaterialsView(
                self.db, disabled, interaction.user, materials)
            await interaction.response.edit_message(embed=embed, view=view)

    @app_commands.command(name='weapon武器', description='計算武器所需的素材')
    @app_commands.rename(types='武器類別', rarities='稀有度')
    @app_commands.describe(types='要計算的武器的類別', rarities='武器的稀有度')
    @app_commands.choices(
        types=[
            Choice(name='單手劍', value=1),
            Choice(name='法器', value=10),
            Choice(name='大劍', value=11),
            Choice(name='弓箭', value=12),
            Choice(name='長槍', value=13)],
        rarities=[
            Choice(name='★★★★★', value=5),
            Choice(name='★★★★', value=4),
            Choice(name='★★★', value=3),
            Choice(name='★★', value=2),
            Choice(name='★', value=1)])
    async def calc_weapon(self, i: Interaction, types: int, rarities: int):
        client = getClient()
        weapons = await client.get_calculator_weapons(types=[types], rarities=[rarities])
        await i.response.send_message(view=CalcCog.CalcWeaponView(weapons, i.user, self.bot.db))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CalcCog(bot))