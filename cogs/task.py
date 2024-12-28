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
updateTimes = [
    time(hour=0, tzinfo=JST),
    time(hour=6, tzinfo=JST),
    time(hour=12, tzinfo=JST),
    time(hour=18, tzinfo=JST)
]
voteTimes = [
    time(hour=0, tzinfo=JST),
]
# アナウンスの時間を設定
announceTimes = [
    time(hour=17, tzinfo=JST),
]

webCacheReloadTimes = [
    time(hour=0, tzinfo=JST),
    time(hour=6, tzinfo=JST),
    time(hour=12, tzinfo=JST),
    time(hour=18, tzinfo=JST)
]


class taskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        if self.updateTask.is_running():
            self.updateTask.restart()
        else:
            self.updateTask.start()
        if self.announceTask.is_running():
            self.announceTask.restart()
        else:
            self.announceTask.start()
        if self.webCacheReloadTask.is_running():
            self.webCacheReloadTask.restart()
        else:
            self.webCacheReloadTask.start()
        if self.voteTask.is_running():
            self.voteTask.restart()
        else:
            self.voteTask.start()
        print("Cog task.py init!")

    @tasks.loop(time=voteTimes)
    async def voteTask(self):
        nowday = datetime.now(JST).day
        if nowday != 25:
            return

    @tasks.loop(time=webCacheReloadTimes)
    async def webCacheReloadTask(self):
        url = "https://dao.andbeyondcompany.com/api/getMarkdown?pageId=702f9444165b4a62aa5359dc49b83669"
        response = requests.get(url, timeout=30)

    @tasks.loop(time=announceTimes)
    async def announceTask(self):
        nowday = datetime.now(JST).day
        if nowday == int(settings["announcement"]["justbefore"]["day"]):
            announceMessage = settings["announcement"]["justbefore"]["message"]
            self.bot.get_channel(
                int(settings["channel"]["announcement"])).send(announceMessage)
            return

    @tasks.loop(time=updateTimes, reconnect=True)
    async def updateTask(self):
        print("nameChangeTask")
        userInfos = db.readDB("user")
        for userInfo in userInfos:
            changeFlag = 0
            user = self.bot.get_guild(
                int(settings["general"]["GuildID"])).get_member(int(userInfo))
            displayName = user.display_name
            displayAvatarURL = user.display_avatar.url
            roleName = self.bot.get_guild(
                int(settings["general"]["GuildID"])).get_role(int(user.roles[-1].id)).name
            if str(userInfos[userInfo]["userID"]) != str(user.id):
                userInfos[userInfo]["userID"] = str(user.id)
                changeFlag += 1
            if userInfos[userInfo]["userDisplayName"] != displayName:
                userInfos[userInfo]["userDisplayName"] = displayName
                changeFlag += 1
            if userInfos[userInfo]["userDisplayIcon"] != displayAvatarURL:
                userInfos[userInfo]["userDisplayIcon"] = displayAvatarURL
                changeFlag += 1
            if userInfos[userInfo]["userHighestRole"] != roleName:
                userInfos[userInfo]["userHighestRole"] = roleName
                changeFlag += 1
            if changeFlag != 0:
                db.writeDB("user", userInfo, userInfos[userInfo])


async def setup(bot: commands.Bot):
    await bot.add_cog(taskCog(bot))
