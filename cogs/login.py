from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import scr.database as db
import datetime
import cogs.token as token

with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class loginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog login.py init!")

    @app_commands.command(name=settings["commands"]["login"]["command"], description=settings["commands"]["login"]["description"])
    async def login(self, interaction: discord.Interaction):
        await interaction.response.send_message("ログインしました", ephemeral=True)
        userInfo = db.readDB("user", str(interaction.user.id))
        today = datetime.datetime.now().strftime('%Y:%m:%d')
        loginMessage = ""
        loginMenu = []
        try:
            time = datetime.datetime.strptime(
                userInfo["login"]["yearly"], '%Y:%m:%d')
            timedelta = datetime.datetime.strptime(today, '%Y:%m:%d') - time

            if timedelta.days >= 365:
                loginMessage += settings["token"]["loginYearly"]["description"] + "\n"
                userInfo["login"]["yearly"] = today
                loginMenu.append("loginYearly")
        except:
            if timedelta.days >= 365:
                loginMessage += settings["token"]["loginYearly"]["description"] + "\n"
                userInfo["login"]["yearly"] = today
                loginMenu.append("loginYearly")

        if len(loginMenu) != 0:
            loginMenu.append("loginMonthly")
            userInfo["login"]["monthly"] = today
            loginMenu.append("loginWeekly")
            userInfo["login"]["weekly"] = today
            userInfo["login"]["total"] = 1
        else:
            mounthlydelta = datetime.datetime.strptime(
                today, '%Y:%m:%d') - datetime.datetime.strptime(userInfo["login"]["monthly"], '%Y:%m:%d')

            if mounthlydelta.days >= 30:
                loginMessage += settings["token"]["loginMonthly"]["description"] + "\n"
                userInfo["login"]["monthly"] = today
                loginMenu.append("loginMonthly")
            weeklydelta = datetime.datetime.strptime(
                today, '%Y:%m:%d') - datetime.datetime.strptime(userInfo["login"]["weekly"], '%Y:%m:%d')

            if weeklydelta.days >= 7:
                loginMessage += settings["token"]["loginWeekly"]["description"] + "\n"
                userInfo["login"]["weekly"] = today
                loginMenu.append("loginWeekly")

        try:
            daydalta = datetime.datetime.strptime(
                today, '%Y:%m:%d') - datetime.datetime.strptime(userInfo["login"]["day"], '%Y:%m:%d')
            daydaltaDays = daydalta.days
        except:
            daydaltaDays = 1

        date = datetime.datetime.now().strftime("%a")
        if daydaltaDays >= 1:
            if date in "月火水木金" or date in "MondayTuesdayWednesdayThursdayFriday":
                loginMessage += settings["token"]["loginWeekday"]["description"] + "\n"
                loginMenu.append("loginWeekday")
            else:
                loginMessage += settings["token"]["loginWeekend"]["description"] + "\n"
                loginMenu.append("loginWeekend")

            userInfo["login"]["day"] = today
            userInfo["login"]["total"] += 1

        for item in loginMenu:
            await token.tokenCog(self.bot).giveToken(self.bot.user, interaction.user, settings["token"][item]["token"], settings["token"][item]["description"])

        db.writeDB("user", str(interaction.user.id), userInfo)


async def setup(bot: commands.Bot):
    await bot.add_cog(loginCog(bot))
