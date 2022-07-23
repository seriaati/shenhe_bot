from tkinter.tix import Select

import aiosqlite
from discord import (ButtonStyle, Interaction, Member, SelectOption,
                     app_commands)
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput
from debug import DefaultView
from utility.utils import defaultEmbed, errEmbed, getConsumable


class Todo(commands.Cog, name='todo'):
    def __init__(self, bot):
        self.bot = bot

    async def get_todo_embed(db: aiosqlite.Connection, user: Member):
        c = await db.cursor()
        await c.execute('SELECT item, count FROM todo WHERE user_id = ?', (user.id,))
        todo = await c.fetchone()
        if todo is None:
            embed = defaultEmbed(
                '代辦事項',
                '太好了, 沒有需要蒐集的素材ˋ( ° ▽、° ) \n'
                '使用 `/calc` 指令來計算角色素材\n'
                '或是使用下方的按鈕來新增素材')
            embed.set_author(name=user, icon_url=user.avatar)
            return embed
        await c.execute('SELECT item, count FROM todo WHERE user_id = ?', (user.id,))
        todo = await c.fetchall()
        todo_list = []
        for index, tuple in enumerate(todo):
            item = tuple[0]
            count = tuple[1]
            todo_list.append(f'{getConsumable(name=item)["emoji"]} {item} x{count}')
        desc = ''
        for todo_item in todo_list:
            desc += f'{todo_item}\n'
        embed = defaultEmbed(message=desc)
        embed.set_author(name='代辦事項', icon_url=user.avatar)
        return embed

    class TodoListView(DefaultView):
        def __init__(self, db: aiosqlite.Connection, empty: bool, author: Member):
            super().__init__(timeout=None)
            self.db = db
            self.author = author
            disabled = True if empty else False
            self.add_item(Todo.AddTodoButton(db))
            self.add_item(Todo.RemoveTodoButton(disabled, db))
            self.add_item(Todo.ClearTodoButton(disabled, db))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/todo` 來開啟一個').set_author(name='這不是你的代辦清單', icon_url=interaction.user.avatar), ephemeral=True)
            return self.author.id == interaction.user.id

    class AddTodoButton(Button):
        def __init__(self, db):
            self.db = db
            super().__init__(label='新增素材', style=ButtonStyle.green)

        async def callback(self, i: Interaction):
            modal = Todo.AddTodoModal()
            await i.response.send_modal(modal)
            await modal.wait()
            try:
                count_value = int(modal.count.value)
            except ValueError:
                return await i.followup.send(embed=errEmbed(message='正確: 100, 6969, 4110\n錯誤: 一百萬, 100K, 100,000').set_author(name='請輸入數字', icon_url=i.user.avatar), ephemeral=True)
            c: aiosqlite.Cursor = await self.db.cursor()
            await c.execute('INSERT INTO todo (user_id, item, count) VALUES (?, ?, ?) ON CONFLICT (user_id, item) DO UPDATE SET count = count + ? WHERE user_id = ? AND item = ?', (i.user.id, modal.item.value, count_value, count_value, i.user.id, modal.item.value))
            await self.db.commit()
            embed = await Todo.get_todo_embed(self.db, i.user)
            await c.execute('SELECT count FROM todo WHERE user_id = ?', (i.user.id,))
            count = await c.fetchone()
            empty = True if count is None else False
            view = Todo.TodoListView(self.db, empty, i.user)
            await i.edit_original_message(embed=embed, view=view)

    class RemoveTodoButton(Button):
        def __init__(self, disabled: bool, db: aiosqlite.Connection):
            super().__init__(label='刪除素材', style=ButtonStyle.red, disabled=disabled)
            self.db = db

        async def callback(self, i: Interaction):
            c: aiosqlite.Cursor = await self.db.cursor()
            await c.execute('SELECT item FROM todo WHERE user_id = ?', (i.user.id,))
            todos = await c.fetchall()
            options = []
            for index, tuple in enumerate(todos):
                options.append(SelectOption(label=tuple[0], value=tuple[0]))
            modal = Todo.RemoveTodoModal(options)
            await i.response.send_modal(modal)
            await modal.wait()
            await c.execute('SELECT count FROM todo WHERE user_id = ? AND item = ?', (i.user.id, modal.item.values[0]))
            count = await c.fetchone()
            count = count[0]
            modal_count_value = modal.count.value or count
            if modal_count_value > count:
                return await i.followup.send(embed=errEmbed().set_author(name='不可輸入大於目前素材數量的數字', icon_url=i.user.avatar), ephemeral=True)
            try:
                modal_count_value = int(modal_count_value)
            except ValueError:
                return await i.followup.send(embed=errEmbed(message='正確: 100, 6969, 4110\n錯誤: 一百萬, 100K, 100,000').set_author(name='請輸入數字', icon_url=i.user.avatar), ephemeral=True)
            await c.execute('UPDATE todo SET count = ? WHERE user_id = ? AND item = ?', (count-int(modal_count_value), i.user.id, modal.item.values[0]))
            await c.execute('DELETE FROM todo WHERE count = 0 AND user_id = ?', (i.user.id,))
            await self.db.commit()
            embed = await Todo.get_todo_embed(self.db, i.user)
            await c.execute('SELECT count FROM todo WHERE user_id = ?', (i.user.id,))
            count = await c.fetchone()
            disabled = False
            if count is None:
                disabled = True
            view = Todo.TodoListView(self.db, disabled, i.user)
            await i.edit_original_message(embed=embed, view=view)

    class ClearTodoButton(Button):
        def __init__(self, disabled: bool, db: aiosqlite.Connection):
            super().__init__(label='清空', style=ButtonStyle.gray, disabled=disabled)
            self.db = db

        async def callback(self, i: Interaction):
            c: aiosqlite.Cursor = await self.db.cursor()
            await c.execute('DELETE FROM todo WHERE user_id = ?', (i.user.id,))
            await self.db.commit()
            view = Todo.TodoListView(self.db, True, i.user)
            embed = await Todo.get_todo_embed(self.db, i.user)
            await i.response.edit_message(embed=embed, view=view)

    class AddTodoModal(Modal):
        item = TextInput(
            label='材料名稱',
            placeholder='例如: 刀譚',
        )

        count = TextInput(
            label='數量',
            placeholder='例如: 96'
        )

        def __init__(self) -> None:
            super().__init__(title='新增素材', timeout=None)

        async def on_submit(self, interaction: Interaction) -> None:
            await interaction.response.defer()

    class RemoveTodoModal(Modal):
        item = Select(
            placeholder='選擇要刪除的素材',
            min_values=1,
            max_values=1,
        )

        count = TextInput(
            label='數量',
            placeholder='例如: 28 (如留空則清空該素材)',
            required=False
        )

        def __init__(self, options) -> None:
            self.item.options = options
            super().__init__(title='刪除素材', timeout=None)

        async def on_submit(self, interaction: Interaction) -> None:
            await interaction.response.defer()

    @app_commands.command(name='todo代辦清單', description='查看代辦清單')
    async def todo_list(self, i: Interaction):
        c = await self.bot.db.cursor()
        await c.execute('SELECT count FROM todo WHERE user_id = ?', (i.user.id,))
        count = await c.fetchone()
        disabled = False
        if count is None:
            disabled = True
        view = Todo.TodoListView(self.bot.db, disabled, i.user)
        embed = await Todo.get_todo_embed(self.bot.db, i.user)
        await i.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Todo(bot))
