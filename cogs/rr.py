import inflect
import yaml
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from utility.utils import defaultEmbed, errEmbed, log
from discord import Role
import re
import emoji


class ReactionRoles(commands.Cog, name='rr', description='表情符號身份組產生器'):
    def __init__(self, bot):
        self.bot = bot
        with open(f'data/rr.yaml', encoding='utf-8') as file:
            self.rr_dict = yaml.full_load(file)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reactor = self.bot.get_user(payload.user_id)
        if reactor.bot:
            return
        if payload.message_id == 963972447600771092:  # 世界等級身份組
            for i in range(1, 9):
                p = inflect.engine()
                word = p.number_to_words(i)
                emojiStr = emoji.emojize(f":{word}:", language='alias')
                if payload.emoji.name == str(emojiStr):
                    guild = self.bot.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    role = discord.utils.get(guild.roles, name=f"W{i}")
                    await member.add_roles(role)
                    break

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        reactor = self.bot.get_user(payload.user_id)
        if reactor.bot:
            return
        if payload.message_id == 963972447600771092:  # 移除世界等級身份組
            for i in range(1, 9):
                p = inflect.engine()
                word = p.number_to_words(i)
                emojiStr = emoji.emojize(f":{word}:", language='alias')
                if payload.emoji.name == str(emojiStr):
                    guild = self.bot.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    role = discord.utils.get(guild.roles, name=f"W{i}")
                    await member.remove_roles(role)
                    break
            
    
    class RoleSelection(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        class ButtonChoices(discord.ui.View):
            def __init__(self, role):
                super().__init__(timeout=None)
                self.role = role

            @discord.ui.button(label='獲取', style=discord.ButtonStyle.green)
            async def get_role_button(self, interaction: Interaction, button: discord.ui.Button):
                g = interaction.client.get_guild(916838066117824553)
                r = discord.utils.get(g.roles, name=self.role)
                if r in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed('你已經擁有這個身份組了!',''), ephemeral=True)
                    return
                await interaction.user.add_roles(r)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ {r} 身份組獲取成功', ''), ephemeral=True)

            @discord.ui.button(label='撤回', style=discord.ButtonStyle.red)
            async def discard_role_button(self, interaction: Interaction, button: discord.ui.Button):
                g = interaction.client.get_guild(916838066117824553)
                r = discord.utils.get(g.roles, name=self.role)
                if r not in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed('你本來就沒有這個身份組!',''),ephemeral=True)
                await interaction.user.remove_roles(r)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ {r} 身份組撤回成功', ''), ephemeral=True)
        
        def get_role_options():
            roles = ['原神世界等級','委託通知', '抽獎通知', '活動通知', '小雪通知']
            role_list = []
            for role in roles:
                role_list.append(discord.SelectOption(label=role))
            return role_list

        class WorldLevelView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                for x in range(1, 9):
                    y = 0 if x <=4 else 1
                    self.add_item(self.WorldLevelButton(x, y))

            class WorldLevelButton(discord.ui.Button):
                def __init__(self, number:int, row:int):
                    super().__init__(style=discord.ButtonStyle.blurple, label=number, row=row)
                    self.number = number

                async def callback(self, interaction: Interaction):
                    for x in range (1, 9):
                        if self.number == x:
                            g = interaction.client.get_guild(916838066117824553)
                            r = discord.utils.get(g.roles, name=f'W{x}')
                            await interaction.user.add_roles(r)
                            break

        @discord.ui.select(options=get_role_options(), placeholder='請選擇身份組', min_values=1, max_values=1)
        async def role_chooser(self, interaction: Interaction, select: discord.ui.Select):
            choice = select.values[0]
            action_menu = self.ButtonChoices(choice)
            wr_menu = self.WorldLevelView()
            if select.values[0] == '原神世界等級':
                await interaction.response.send_message(view=wr_menu, ephemeral=True)
            else:
                await interaction.response.send_message(view=action_menu, ephemeral=True)

    @app_commands.command(name='role', description='取得身份組')
    async def get_role(self, i: Interaction):
        print(log(False, False, 'Role', i.user.id))
        role_selection_view = self.RoleSelection()
        await i.response.send_message(view=role_selection_view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
