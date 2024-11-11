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


class taskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog task.py init!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("task ready")
        self.nameChangeTask.start()
        self.voteTask.start()
    # my_taskの部分はお好きな名前にしてください

    @tasks.loop(time=voteTimes)
    async def voteTask(self):
        nowday = datetime.now(JST).day
        if nowday != 25:
            return

    # @tasks.loop(seconds=10, reconnect=True)
    # @app_commands.command(name="change", description="名前を変更します")
    async def nameChangeTask(self, intraction: discord.Interaction):
        await intraction.response.send_message("名前を変更しました", ephemeral=True)
        print("nameChangeTask")
        userInfos = db.readDB("user")
        for userInfo in userInfos:
            print(userInfo)
            user = self.bot.get_guild(
                int(settings["general"]["GuildID"])).get_member(int(userInfo))
            print(user.id, userInfos[userInfo]["userID"])
            displayName = user.display_name
            displayAvatarURL = user.display_avatar.url
            if str(userInfos[userInfo]["userID"]) != str(user.id):
                userInfos[userInfo]["userID"] = str(user.id)
                print("userID")
            if userInfos[userInfo]["userDisplayName"] != displayName:
                userInfos[userInfo]["userDisplayName"] = displayName
            if userInfos[userInfo]["userDisplayIcon"] != displayAvatarURL:
                userInfos[userInfo]["userDisplayIcon"] = displayAvatarURL
            db.writeDB("user", userInfo, userInfos[userInfo])


async def setup(bot: commands.Bot):
    await bot.add_cog(taskCog(bot))
