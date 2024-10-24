from discord.ext import commands
from discord import ui, app_commands
import discord
import json

with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class tipwaveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog tipwave.py init!")

    @app_commands.command(name=settings["commands"]["tipwavesend"]["command"], description=settings["commands"]["tipwavesend"]["description"])
    @app_commands.default_permissions(administrator=True)
    async def tipwavesend(self, interaction: discord.Interaction, user: discord.User, amount: int):
        tipwave = interaction.guild.get_member(
            int(settings["general"]["tipwaveBotClientID"]))
        await interaction.response.send_message(f"{tipwave.mention} tip_discord {user.mention} お試しポイント {amount}")


async def setup(bot: commands.Bot):
    await bot.add_cog(tipwaveCog(bot))
