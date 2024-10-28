from discord.ext import commands
from discord import ui, app_commands
import discord
import json

with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class loginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog login.py init!")


async def setup(bot: commands.Bot):
    await bot.add_cog(loginCog(bot))
