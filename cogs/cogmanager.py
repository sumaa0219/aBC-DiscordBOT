from discord.ext import commands
from discord import app_commands
import discord
import os
from dotenv import load_dotenv
import json

load_dotenv()

# このファイルは読み込まない
# removeCogs = ["tipwave.py", "__pycache__"]
removeCogs = ["__pycache__"]


with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class cogManagerCog(commands.Cog):
    def __init__(self, bot):  # コンストラクタ
        self.bot = bot
        self.switchFlag = False
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog cogmanager.py init!")

    def getCogs(self):
        self.GLOBAL_INITIAL_EXTENSIONS = os.listdir("cogs")
        for cog in removeCogs:
            if cog in self.GLOBAL_INITIAL_EXTENSIONS:
                self.GLOBAL_INITIAL_EXTENSIONS.remove(cog)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog cogmanage.py ready!")
        await self.load_all_extentions()

    @app_commands.command(name=settings["commands"]["reload"]["command"], description=settings["commands"]["reload"]["description"])
    @app_commands.default_permissions(administrator=True)
    async def reload(self, interaction: discord.Interaction):
        self.getCogs()
        for cog in self.GLOBAL_INITIAL_EXTENSIONS:
            print("loading cogs...", "cogs."+cog[:-3])
            await self.bot.reload_extension("cogs."+cog[:-3])
        guild = discord.Object(int(settings["general"]["GuildID"]))
        await interaction.response.send_message("コグを再読み込みしました", ephemeral=True)
        await self.bot.tree.sync(guild=guild)
        await self.bot.tree.sync()

    @app_commands.command(name=settings["commands"]["help"]["command"], description=settings["commands"]["help"]["description"])
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="このBOTに登録されているコマンドを表示します", description="コマンド一覧", color=0x00ff00)
        for command in settings["commands"]:
            embed.add_field(name=settings["commands"][command]["command"],
                            value=settings["commands"][command]["description"], inline=False)
        await interaction.followup.send(embed=embed)

    async def load_all_extentions(self):
        print("loading all cogs...")
        self.getCogs()
        self.GLOBAL_INITIAL_EXTENSIONS.remove("cogmanager.py")
        for cog in self.GLOBAL_INITIAL_EXTENSIONS:
            print("loading cogs...", cog[:-3])
            await self.bot.load_extension("cogs."+cog[:-3])
        guild = discord.Object(int(settings["general"]["GuildID"]))
        # 設定されたギルドに対してコマンドを即時反映
        await self.bot.tree.sync(guild=guild)
        # 全てのギルドに対してコマンドを反映(時間かかる)
        await self.bot.tree.sync()


async def setup(bot):
    await bot.add_cog(cogManagerCog(bot))
