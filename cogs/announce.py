from discord.ext import commands, tasks
from discord import ui, app_commands
import discord
import json
from datetime import time, timezone, timedelta, datetime
import scr.database as db
import requests


with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)
JST = timezone(timedelta(hours=+9), "JST")

# 時刻をリストで設定
# アナウンスの時間を設定
announce10Times = [
    time(hour=10, tzinfo=JST),
]

announce17Times = [
    time(hour=17, tzinfo=JST),
]

announce22Times = [
    time(hour=22, tzinfo=JST),
]


class announceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        self.announce10Task.start()
        self.announce17Task.start()
        self.announce22Task.start()
        print("Cog announce.py init!")

    @tasks.loop(time=announce10Times)
    async def announce10Task(self):
        nowday = datetime.now(JST).day
        announceList = settings["announcement"]["announce10"].keys()
        for announce in announceList:
            if announce == "descriptions":
                pass
            elif nowday == int(settings["announcement"]["announce10"][announce]["day"]):
                announceMessage = settings["announcement"]["announce10"][announce]["message"]
                await self.bot.get_channel(
                    int(settings["channel"]["announcement"])).send(content="@everyone\n" + announceMessage)
                return

    @tasks.loop(time=announce17Times)
    async def announce17Task(self):
        nowday = datetime.now(JST).day
        announceList = settings["announcement"]["announce17"].keys()
        for announce in announceList:
            if announce == "descriptions":
                pass
            elif nowday == int(settings["announcement"]["announce17"][announce]["day"]):
                announceMessage = settings["announcement"]["announce17"][announce]["message"]
                await self.bot.get_channel(
                    int(settings["channel"]["announcement"])).send(content="@everyone\n" + announceMessage)
                return

    @tasks.loop(time=announce22Times)
    async def announce22Task(self):
        nowday = datetime.now(JST).day
        announceList = settings["announcement"]["announce22"].keys()
        for announce in announceList:
            if announce == "descriptions":
                pass
            elif nowday == int(settings["announcement"]["announce22"][announce]["day"]):
                announceMessage = settings["announcement"]["announce22"][announce]["message"]
                await self.bot.get_channel(
                    int(settings["channel"]["announcement"])).send(content="@everyone\n" + announceMessage)
                return


async def setup(bot: commands.Bot):
    await bot.add_cog(announceCog(bot))
