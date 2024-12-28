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


class jobtaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print(self.announceTask.is_running())
        if self.announceTask.is_running():
            self.announceTask.restart()
        else:
            self.announceTask.start()
        print("Cog jobtask.py init!")

    @tasks.loop(minutes=1)
    async def announceTask(self):
        tasks = db.readDB("tasks")
        # tasksを展開してisAnnounceがFalseのものを取得,アナウンスしたのちにisAnnounceをTrueに変更
        for key in tasks.keys():
            task = tasks[key]
            if task["isAnnounce"] == False:
                task["isAnnounce"] = True
                db.writeDB("tasks", key, task)
                surpplier = await self.bot.fetch_user(task["supplierID"])
                embed = discord.Embed(
                    title=task["name"], description=f"依頼者:{surpplier.mention}", color=0x00ff00)
                # task["content"]に含まれる改行コードを置換
                task["content"] = task["content"].replace("\n", "")
                embed.add_field(name="内容", value=task["content"], inline=False)
                embed.add_field(
                    name="目安時間", value=task['workingTime'], inline=False)
                embed.add_field(
                    name="締切", value=task["limitDay"], inline=False)
                embed.add_field(name="難易度", value="星" +
                                str(task["rank"])+"つ", inline=False)
                reportMessage = "あり" if task["isReport"] == True else "なし"
                embed.add_field(
                    name="報告", value=f"報告{reportMessage}", inline=False)

                await self.bot.get_channel(int(settings["channel"]["announcement"])).send(content=f"新たなタスクが追加されました", embed=embed)
                # await self.bot.get_channel(1298147892485427260).send(content=f"新たなタスクが追加されました", embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(jobtaskCog(bot))
