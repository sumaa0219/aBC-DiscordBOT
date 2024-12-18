from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import cogs.token as token
import scr.database as db
import random
import string
import datetime

# 設定ファイルの読み込み
with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)

agendaIDNum = 15
# bigroomnCogクラスの定義


class bigroomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        # 設定ファイルの再読み込み
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog bigroom.py init!")

    # メッセージが送信されたときに呼ばれるイベントリスナー

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 自己紹介チャンネル以外では処理を行わない
        if message.channel.id != int(settings["channel"]["bigroom"]):
            return
        else:
            # コマンドメッセージは削除
            if message.content.startswith("/"):
                try:
                    await message.delete()
                except:
                    pass
                return
            # Botのメッセージは削除
            if message.author.bot and "アジェンダID" not in message.content and "アナウンス" not in message.content:
                try:
                    await message.delete()
                except:
                    pass
                return
            elif message.author.bot and "アジェンダID" in message.content and "アナウンス" in message.content:
                return
            else:

                originalMessage = message.content
                text = message.content.split("\n")
                errormessage = ""
                if len(text) > 4:
                    for i in range(4, len(text)):
                        text[3] += text[i]

                for agenda in list(settings["agenda"].keys()):
                    try:
                        if str(settings["agenda"][agenda]["content"]) not in text[int(agenda)-1]:
                            if agenda == "1":
                                errormessage += "文の一番上に``[プロジェクトエントリー]``と書いてください。\n"
                            else:
                                errormessage += f"{settings['agenda'][agenda]['content']}がありません。\n"
                    except IndexError:
                        errormessage += f"{settings['agenda'][agenda]['content']}がありません。\n"

                    try:
                        if int(agenda)-1 == 3:
                            if len(text[int(agenda)-1]) > int(settings["agenda"][agenda]["max"]):
                                errormessage += f"{settings['agenda'][agenda]['content']}は{settings['agenda'][agenda]['max']}文字以下で入力してください。\n"
                            if len(text[int(agenda)-1]) <= int(settings["agenda"][agenda]["min"]):
                                errormessage += f"{settings['agenda'][agenda]['content']}は{settings['agenda'][agenda]['min']}文字以上で入力してください。\n"
                        else:
                            if len(text[int(agenda)-1]) <= int(settings["agenda"][agenda]["min"]):
                                errormessage += f"{settings['agenda'][agenda]['content']}は{settings['agenda'][agenda]['min']}文字以上で入力してください。\n"
                    except IndexError:
                        pass

                if errormessage != "":
                    await message.guild.get_channel(int(settings["channel"]["reject"])).send(f"アジェンダID{message.author.mention}さん、以下のエラーがあります。\n{errormessage}\n{originalMessage}")
                    await message.delete()
                # アジェンダ承認された場合
                else:
                    agendaID = ''.join(random.choices(
                        string.ascii_letters + string.digits, k=agendaIDNum))
                    title = text[1].split(":")
                    channelName = text[2].split(":")
                    content = text[3].split(":")
                    userInfo = db.readDB("user", str(message.author.id))
                    if userInfo["agenda"]["idList"] == None:
                        userInfo["agenda"]["idList"] = [agendaID]
                    else:
                        list(userInfo["agenda"]["idList"]).append(agendaID)
                    db.writeDB("user", str(message.author.id), userInfo)

                    await message.reply(f"アジェンダID: {agendaID}")
                    await message.add_reaction("✅")

                    createdChannel = await self.createChannel(message.guild, channelName[1], content[1])
                    data = {
                        "agendaID": agendaID,
                        "title": title[1],
                        "channelname": channelName[1],
                        "channelId": createdChannel.id,
                        "content": content[1],
                        "author": str(message.author.id),
                        "time": datetime.datetime.now().strftime('%Y%m%d'),
                        "endTime": (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y%m%d'),
                        "autherIcon": message.author.avatar.url,
                        "voteUser": []
                    }
                    db.writeDB("agenda", agendaID, data)
                    await createdChannel.send(f"アジェンダID: {agendaID}")
                    await createdChannel.send(f"アジェンダオーナー: {message.author.mention}")

    async def createChannel(self, guild: discord.Guild, channelName: str, topic: str):
        category = guild.get_channel(int(settings["category"]["smallroom"]))
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }
        channel = await category.create_text_channel(channelName, overwrites=overwrites, topic=topic)
        return channel
# Cogをセットアップする関数


async def setup(bot: commands.Bot):
    await bot.add_cog(bigroomCog(bot))
