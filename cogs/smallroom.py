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
        # self.announce17Task.start()
        print("Cog smallroom.py init!")

    @tasks.loop(time=announceTimes)
    async def announce17Task(self):
        result, channelid = await self.announce(17)
        if result is not None:
            if result == "weelDayAfter":
                self.archive_channel(channelid)

    @tasks.loop(time=endTimes)
    async def endTask(self):
        result, channelid = await self.announce(0)
        if result is not None:
            if result == "1DayAfter":
                channel = self.bot.get_channel(channelid)
                # ターゲットとする役職を取得
                role = discord.utils.get(channel.guild.roles, name="@everyone")

                overwrite = discord.PermissionOverwrite()
                overwrite.send_messages = False

                # 変更する
                await channel.set_permissions(role, overwrite=overwrite)

    async def announce(self, announceTime):
        announceTime = "announce" + str(announceTime)
        data = db.readDB("agenda")
        for agendaID in data.keys():
            channelId = data[agendaID]["channelId"]
            agendaTime = datetime.strptime(data[agendaID]["endTime"], "%Y%m%d")
            nowTime = datetime.now(JST)
            timeDelta = agendaTime - nowTime
            for dayOption in settings["smallroom"].keys():
                if dayOption == "descriptions":
                    continue
                else:
                    timeDelta2end = timeDelta if dayOption == "before" else timeDelta*-1
                    for announce in settings["smallroom"][dayOption][announceTime].keys():
                        if announce == "descriptions":
                            continue
                        # ここを変更
                        elif timeDelta2end.days == settings["smallroom"][dayOption][announceTime][announce]["day"]:
                            announceMessage = settings["smallroom"][dayOption]["announce17"][announce]["message"]
                            await self.bot.get_channel(channelId).send(content="@everyone\n" + announceMessage)
                            return announce, channelId

    async def archive_channel(self, channelid):
        FORUM_CHANNEL_ID = settings["channel"]["forum"]
        channel = self.bot.get_channel(channelid)
        if channel is None:
            print(f"Channel with ID {channelid} not found.")
            return

        # フォーラムチャンネルを取得
        forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)
        if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
            print(
                f"Forum channel with ID {FORUM_CHANNEL_ID} not found or is not a ForumChannel.")
            return

        # 新規トピックを作成
        topic_title = f"{channel.name}"
        topic = await forum_channel.create_thread(name=topic_title, type=discord.ChannelType.public_thread)

        # チャンネルの履歴を取得
        messages = await channel.history(limit=None).flatten()

        # メッセージをEmbedにして投稿
        for message in messages:
            embed = discord.Embed(
                title=f"{message.author}",
                description=message.content,
                timestamp=message.created_at
            )
            await topic.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(smallroomCog(bot))
