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
endTimes = [
    time(hour=0, tzinfo=JST),
]

announceTimes = [
    time(hour=17, tzinfo=JST),
]


class smallroomCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        if self.announce17Task.is_running():
            self.announce17Task.restart()
        else:
            self.announce17Task.start()
        if self.endTask.is_running():
            self.endTask.restart()
        else:
            self.endTask.start()
        print("Cog smallroom.py init!")

    @tasks.loop(time=announceTimes)
    async def announce17Task(self):
        results = await self.announce(17)
        if results is not None:
            for result in results:
                if result[0] == "weekDayAfter":
                    await self.archive_channel(result[1])

    @tasks.loop(time=endTimes)
    async def endTask(self):
        results = await self.announce(0)
        print(results)
        if results is not None:
            for result in results:
                if result[0] == "1DayAfter":
                    channel = self.bot.get_channel(result[1])
                    # ターゲットとする役職を取得
                    role = discord.utils.get(
                        channel.guild.roles, name="@everyone")

                    overwrite = discord.PermissionOverwrite()
                    overwrite.send_messages = False

                    # 変更する
                    await channel.set_permissions(role, overwrite=overwrite)

    async def announce(self, announceTime):
        announceTime = "announce" + str(announceTime)
        data = db.readDB("agenda")
        returnData = []
        for agendaID in data.keys():
            channelId = data[agendaID]["channelId"]
            agendaTime = datetime.strptime(
                data[agendaID]["endTime"], "%Y%m%d").replace(tzinfo=JST)
            nowTime = datetime.now(JST)
            timeDelta = agendaTime - nowTime
            for dayOption in settings["smallroom"].keys():
                if dayOption != "descriptions":
                    timeDelta2end = timeDelta.days
                    try:
                        for announce in settings["smallroom"][dayOption][announceTime].keys():
                            if announce != "descriptions":
                                if int(timeDelta2end) == int(settings["smallroom"][dayOption][announceTime][announce]["day"]):

                                    announceMessage = settings["smallroom"][dayOption][announceTime][announce]["message"]
                                    await self.bot.get_channel(channelId).send(content="@everyone\n" + announceMessage)
                                    returnData.append([announce, channelId])
                    except:
                        pass
        return returnData

    async def archive_channel(self, channelid):
        FORUM_CHANNEL_ID = int(settings["channel"]["forum"])
        channel = self.bot.get_channel(channelid)
        print(channel.name)
        if channel is None:
            print(f"Channel with ID {channelid} not found.")
            return

        # フォーラムチャンネルを取得
        forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)
        if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
            print(
                f"Forum channel with ID {FORUM_CHANNEL_ID} not found or is not a ForumChannel.")
            return

        topic = await forum_channel.create_thread(name=channel.name, content=channel.topic)

        # チャンネルの履歴を取得
        # メッセージをEmbedにして投稿
        async for message in channel.history(limit=None, oldest_first=True):
            embed = discord.Embed(
                title=f"{message.author}",
                description=message.content,
                timestamp=message.created_at
            )
            await topic[0].send(embed=embed)  # 修正箇所
        await channel.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(smallroomCog(bot))
