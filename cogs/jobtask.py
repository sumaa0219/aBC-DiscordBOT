from discord.ext import commands, tasks
from discord import ui, app_commands
import discord
import json
from datetime import time, timezone, timedelta, datetime
import scr.database as db
import cogs.token as token


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
        if self.tokenCodeTask.is_running():
            self.tokenCodeTask.restart()
        else:
            self.tokenCodeTask.start()
        print("Cog jobtask.py init!")
        
    @tasks.loop(minutes=5)
    async def tokenCodeTask(self):
        codes = db.readDB("codes")
        for key in codes.keys():
            code = codes[key]
            useduser = code["useduser"]
            applicableuser = code["applicableuser"]
            if len(useduser) != len(applicableuser):
                for userid in useduser:
                    if userid not in applicableuser:
                        applicableuser.append(userid)
                        await token.tokenCog(self.bot).giveToken(self.bot.user, await self.bot.fetch_user(int(userid)), int(code["token"]), f"{str(code['token'])}トークンの特典コードを適用しました。")                      
                code["applicableuser"] = applicableuser
                db.writeDB("codes", key, code)
            
            

    @tasks.loop(minutes=1)
    async def announceTask(self):
        tasks = db.readDB("tasks")
        # tasksを展開してisAnnounceがFalseのものを取得,アナウンスしたのちにisAnnounceをTrueに変更
        for key in tasks.keys():
            task = tasks[key]
            if task["isAnnounce"] == False:
                task["isAnnounce"] = True
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
                thread = await self.task_forum_channel(task["name"], task["content"], task["limitDay"], task["rank"], task["isReport"], task["workingTime"], surpplier)
                task["threadID"] = str(thread.thread.id)
                db.writeDB("tasks", key, task)
                await self.bot.get_channel(int(settings["channel"]["announcement"])).send(content=f"新たなタスクが追加されました", embed=embed)
                # await self.bot.get_channel(1298147892485427260).send(content=f"新たなタスクが追加されました", embed=embed)

            if task["isTokenSent"] == False and task["workingStatus"] == "完了":
                task["isTokenSent"] = True
                threadID = task["threadID"]
                task["completeTime"] = datetime.now(JST).strftime("%Y-%m-%d")
                db.writeDB("tasks", key, task)
                thread = self.bot.get_guild(
                    int(settings["general"]["GuildID"])).get_channel(int(settings["channel"]["taskforum"])).get_thread(int(threadID))
                await thread.send(content="タスクの完了されました。")
                for userID in task["clientID"]:
                    await token.tokenCog(self.bot).giveToken(self.bot.user, await self.bot.fetch_user(userID), int(settings["task"]["rank"][(str(task["rank"]))]["token"]), settings["task"]["message"]["content"])
                supplier = await self.bot.fetch_user(task["supplierID"])
                await self.bot.get_channel(int(settings["channel"]["announcement"])).send(content=f"{supplier.mention}さんのタスクが完了しました。", embed=discord.Embed(title=task["name"], description=task["content"], color=0x00ff00))

    async def task_forum_channel(self, taskname: str, taskcontent: str, tasklimit: str, taskrank: int, taskreport: bool, taskworkingtime: str, tasksupplier: discord.User):
        FORUM_CHANNEL_ID = int(settings["channel"]["taskforum"])

        # フォーラムチャンネルを取得
        forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)
        if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
            print(
                f"Forum channel with ID {FORUM_CHANNEL_ID} not found or is not a ForumChannel.")
            return

        report = "あり" if taskreport else "なし"
        messagge = "タスク名:"+taskname+"\n"+"依頼者:"+tasksupplier.mention+"\n内容:"+taskcontent+"\n"+"締切:"+tasklimit+"\n" + \
            "難易度:"+str(taskrank)+"\n"+"報告:"+str(report) + \
            "\n"+"目安時間:"+taskworkingtime
        topic = await forum_channel.create_thread(name=taskname, content=messagge)

        return topic


async def setup(bot: commands.Bot):
    await bot.add_cog(jobtaskCog(bot))
