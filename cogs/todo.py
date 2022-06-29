from tkinter.tix import Select

import aiosqlite
from discord import (ButtonStyle, Interaction, Member, SelectOption,
                     app_commands)
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput
from debug import DefaultView
from utility.utils import defaultEmbed, errEmbed, getConsumableEmojiWithId, getConsumableIdWithName


class Todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def chunks(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

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
            todo_list.append(f'{getConsumableEmojiWithId(getConsumableIdWithName(item))} {item} x{count}')
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
                await interaction.response.send_message(embed=errEmbed('這不是你的代辦清單','輸入 `/todo` 來開啟一個'), ephemeral=True)
            return self.author.id == interaction.user.id

    class AddTodoButton(Button):
        def __init__(self, db):
            self.db = db
            super().__init__(label='新增素材', style=ButtonStyle.green)

        async def callback(self, i: Interaction):
            modal = Todo.AddTodoModal()
            await i.response.send_modal(modal)
            await modal.wait()
            c = await self.db.cursor()
            await c.execute('SELECT count FROM todo WHERE user_id = ? AND item = ?', (i.user.id, modal.item.value))
            count = await c.fetchone()
            if count is None:
                await c.execute('INSERT INTO todo (user_id, item, count) VALUES (?, ?, ?)', (i.user.id, modal.item.value, int((modal.count.value).replace(',', ''))))
            else:
                count = count[0]
                await c.execute('UPDATE todo SET count = ? WHERE user_id = ? AND item = ?', (count+int((modal.count.value).replace(',', '')), i.user.id, modal.item.value))
            await self.db.commit()
            embed = await Todo.get_todo_embed(self.db, i.user)
            await c.execute('SELECT count FROM todo WHERE user_id = ?', (i.user.id,))
            count = await c.fetchone()
            disabled = False
            if count is None:
                disabled = True
            view = Todo.TodoListView(self.db, disabled, i.user)
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
