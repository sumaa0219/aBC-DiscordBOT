from discord.ext import commands, tasks
from discord import ui, app_commands
import discord
import json
from datetime import time, timezone, timedelta, datetime
import scr.database as db


with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)
JST = timezone(timedelta(hours=+9), "JST")

# 時刻をリストで設定
nameChangeTimes = [
    time(hour=0, tzinfo=JST),
    time(hour=12, tzinfo=JST),
]
voteTimes = [
    time(hour=0, tzinfo=JST),
]
# アナウンスの時間を設定
announceTimes = [
    time(hour=0, tzinfo=JST),
    time(hour=12, tzinfo=JST),
]


class taskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        self.nameChangeTask.start()
        self.voteTask.start()
        print("Cog task.py init!")

    @tasks.loop(time=voteTimes)
    async def voteTask(self):
        nowday = datetime.now(JST).day
        if nowday != 25:
            return

    @tasks.loop(time=announceTimes)
    async def announceTask(self):
        nowday = datetime.now(JST).day
        if nowday == int(settings["announcement"]["justbefore"]["day"]):
            announceMessage = settings["announcement"]["justbefore"]["message"]
            self.bot.get_channel(
                int(settings["channel"]["announcement"])).send(announceMessage)
            return

    @tasks.loop(time=nameChangeTimes, reconnect=True)
    async def nameChangeTask(self):
        print("nameChangeTask")
        userInfos = db.readDB("user")
        for userInfo in userInfos:
            user = self.bot.get_guild(
                int(settings["general"]["GuildID"])).get_member(int(userInfo))
            displayName = user.display_name
            displayAvatarURL = user.display_avatar.url
            if str(userInfos[userInfo]["userID"]) != str(user.id):
                userInfos[userInfo]["userID"] = str(user.id)
            if userInfos[userInfo]["userDisplayName"] != displayName:
                userInfos[userInfo]["userDisplayName"] = displayName
            if userInfos[userInfo]["userDisplayIcon"] != displayAvatarURL:
                userInfos[userInfo]["userDisplayIcon"] = displayAvatarURL
            db.writeDB("user", userInfo, userInfos[userInfo])


async def setup(bot: commands.Bot):
    await bot.add_cog(taskCog(bot))
