from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import scr.database as db
import datetime
import cogs.token as token
import time

with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class loginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog login.py init!")


async def buttonSetup(bot: commands.Bot):
    channel = bot.get_channel(int(settings["channel"]["login"]))
    try:
        async for message in channel.history(limit=200):
            await message.delete()
            time.sleep(0.1)
    except:
        pass
    view = LoginView(bot, timeout=None)
    await channel.send(view=view)


class LoginView(discord.ui.View):  # UIキットを利用するためにdiscord.ui.Viewを継承する
    def __init__(self, bot, timeout=None):  # Viewにはtimeoutがあり、初期値は180(s)である
        super().__init__(timeout=timeout)
        self.bot = bot

    @discord.ui.button(label="ログイン", style=discord.ButtonStyle.success)
    async def login(self, interaction: discord.Interaction, button: discord.ui.Button):
        now = datetime.datetime.now().strftime('%Y年%m月%d日')
        await interaction.response.send_message(f"{now} ログインしました", ephemeral=True)
        userInfo = db.readDB("user", str(interaction.user.id))
        today = datetime.datetime.now().strftime('%Y:%m:%d')
        loginMessage = ""
        loginMenu = []
        try:
            try:
                time = datetime.datetime.strptime(
                    userInfo["login"]["yearly"], '%Y:%m:%d')
            except:
                time = datetime.datetime.strptime(
                    "2023:1:1", '%Y:%m:%d')
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

            if daydaltaDays == 1:
                try:
                    userInfo["login"]["continuous"] += 1
                except:
                    userInfo["login"]["continuous"] = 1

            else:
                userInfo["login"]["continuous"] = 1

            userInfo["login"]["day"] = today
            userInfo["login"]["total"] += 1

        if userInfo["login"]["continuous"] % 7 == 0:
            loginMessage += settings["token"]["loginWeekly"]["description"] + "\n"
            userInfo["login"]["weekly"] = today
            loginMenu.append("loginWeekly")

        for item in loginMenu:
            await token.tokenCog(self.bot).giveToken(self.bot.user, interaction.user, settings["token"][item]["token"], settings["token"][item]["description"])
            userInfo["token"] += settings["token"][item]["token"]

        db.writeDB("user", str(interaction.user.id), userInfo)

    @discord.ui.button(label="トークン残高", style=discord.ButtonStyle.gray)
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = db.readDB("user", str(interaction.user.id))
        token = user["token"]
        await interaction.response.send_message(f"あなたのトークン残高は{token:,}トークンです", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(loginCog(bot))
    await buttonSetup(bot)
