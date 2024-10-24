from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import asyncio
import os
import scr.database as db
import datetime
import random
import string


transactionIDNum = 10
with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class tokenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog token.py init!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog token.py ready!")

    @app_commands.command(name=settings["commands"]["show"]["command"], description=settings["commands"]["show"]["description"])
    async def show(self, interaction: discord.Interaction):
        user = db.readDB("user", str(interaction.user.id))
        token = user["token"]
        await interaction.response.send_message(f"あなたのトークン残高は{token:,}トークンです", ephemeral=True)

    @app_commands.command(name=settings["commands"]["send"]["command"], description=settings["commands"]["send"]["description"])
    async def send(self, interaction: discord.Interaction, user: discord.User, amount: int, discription: str):
        userInfo = db.readDB("user", str(interaction.user.id))
        if amount < 0:
            await interaction.response.send_message("トークンの送金数は0以上である必要があります", ephemeral=True)
            return
        if userInfo["token"] < amount:
            await interaction.response.send_message("トークンが不足しています", ephemeral=True)
            return
        else:
            await self.giveToken(interaction.user, user, amount, discription)
            await interaction.response.send_message(f"**{user.display_name}**さんに{amount}トークンを送りました\n説明:{discription}", ephemeral=True)

    @app_commands.command(name=settings["commands"]["adminsend"]["command"], description=settings["commands"]["adminsend"]["description"])
    @app_commands.default_permissions(administrator=True)
    async def adminsend(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await self.giveToken(self.bot.user, user, amount, "管理者からのトークン付与")
        await interaction.response.send_message(f"{user.mention}さんに{amount}トークンを付与しました")

    # サーバー参加時に呼ばれるイベント

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if db.readDB("user", str(member.id)):
            pass
        else:
            userInfomation = self.getDefaultData(member, 0)
            # userInfomationをDBに書き込み
            db.writeDB("user", str(member.id), userInfomation)
            # 非同期で３秒待ってトークン付与
            await asyncio.sleep(3)
            await self.giveToken(self.bot.user, member, settings["token"]["join"]["token"], settings["token"]["join"]["description"])
        await member.add_roles(member.guild.get_role(settings["role"]["listenOnly"]))
        await self.bot.get_guild(settings["general"]["GuildID"]).get_channel(
            settings["channel"]["welcome"]).send(f"{member.mention}さん、ようこそ！")

    # メンバー情報を再読み込み

    @app_commands.command(name="memberreset", description="メンバー全員の全ての情報をリセットします")
    @app_commands.default_permissions(administrator=True)
    async def loadmember(self, interaction: discord.Interaction):
        # メンバー全員の情報を再取得
        await interaction.response.defer()
        members = interaction.guild.members

        for i, member in enumerate(members):
            if db.readDB("user", str(member.id)) != None:
                userinfo = db.readDB("user", str(member.id))
                hasToken = userinfo["token"]
            else:
                hasToken = 0
            userInfomation = self.getDefaultData(member, hasToken)
            db.writeDB("user", str(member.id), userInfomation)
            print(f"{i+1}/{len(members)} {member.display_name}の情報をリセットしました")

        await interaction.followup.send("メンバー情報を再読み込みしました", ephemeral=True)

    def getDefaultData(self, member: discord.Member, hasToken: int):
        userInfomation = {
            "userID": member.id,
            "userDisplayName": member.display_name,
            "userDisplayIcon": str(member.display_avatar.url),
            "token": hasToken,
            "vc": {
                "lastinTime": None,
                "lastoutTime": None,
                "lastinChannelID": 0
            },
            "profile": {
                "done": False,
            },
            "login": {
                "day": None,
                "weekly": None,
                "monthly": None,
            },
            "vote": {
                "count": 3,
                "voteList": None
            },
            "agenda": {
                "idList": None,
            }

        }
        return userInfomation

    async def giveToken(self, fromUser: discord.Member, toUser: discord.Member, amount: int, discription: str):
        print("giveToken fuction called")
        isBOT = False
        # それぞれにおけるトークンの送金処理
        # 送金処理(送られた側)
        targetInfo = db.readDB("user", str(toUser.id))
        targetInfo["token"] = targetInfo["token"] + amount
        db.writeDB("user", str(toUser.id), targetInfo)
        print(targetInfo)

        if fromUser.id == settings["general"]["botClientID"]:
            isBOT = True
        else:
            userInfo = db.readDB("user", str(fromUser.id))
            userInfo["token"] = userInfo["token"] - amount
            db.writeDB("user", str(fromUser.id), userInfo)

        # 送金履歴の記録
        transactionID = ''.join(random.choices(
            string.ascii_letters + string.digits, k=transactionIDNum))
        tokenHistory = {
            "transactionID": transactionID,
            "from": fromUser.id,
            "to": toUser.id,
            "amount": amount,
            "discription": discription,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        db.writeDB("tokenHistory", transactionID, tokenHistory)

        # 送金履歴の送信
        if isBOT:
            embed = discord.Embed(
                title=f"取引番号:``{transactionID}``",
                description=f"from **運営** to **{toUser.mention}**",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title=f"取引番号:``{transactionID}``",
                description=f"from **{fromUser.mention}** to **{toUser.mention}**",
                color=0x00ff00
            )
        embed.add_field(name=f"{amount:,}トークン", value=f"メッセージ:{discription}")
        await self.bot.get_guild(int(settings["general"]["GuildID"])).get_channel(int(
            settings["channel"]["token"])).send(embed=embed)

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     if message.content.startswith("/"):
    #         return
    #     if message.channel.id in connected_channel.values() and message.guild.voice_client:
    #         read_msg = message.content
    #         with open("./VC/user_speaker.json", "r", encoding="UTF-8") as f:
    #             speaker = json.load(f)
    #         speaker_id = int(speaker.get(str(message.author.id), 8))
    #         read_msg = read_msg.replace("_", "")

    #         if os.path.isfile(f"./VC/{message.guild.id}.json"):
    #             with open(f"./VC/{message.guild.id}.json", "r", encoding="UTF-8") as f:
    #                 word = json.load(f)
    #                 # 辞書のキーに基づいてread_msgをフォーマット
    #                 for key, value in word.items():
    #                     read_msg = read_msg.replace(key, value)
    #         read_msg = re.sub(r"https?://.*?\s|https?://.*?$", "URL", read_msg)
    #         read_msg = re.sub(r"\|\|.*?\|\|", "ネタバレ", read_msg)

    #         if "<@" and ">" in message.content:
    #             for user_id in re.findall(r"<@!?([0-9]+)>", message.content):
    #                 user = message.guild.get_member(int(user_id))
    #                 read_msg = re.sub(
    #                     f"<@!?{user_id}>", "アットマーク" + user.display_name, read_msg)

    #         read_msg = re.sub(r"<:(.*?):[0-9]+>", r"\1", read_msg)
    #         read_msg = re.sub(r"\*(.*?)\*", r"\1", read_msg)
    #         read_msg = re.sub(r"_(.*?)_", r"\1", read_msg)
    #         read_msg = re.sub(r'w{3,}', 'わらわら', read_msg)
    #         read_msg = re.sub(r'W{3,}', 'わらわら', read_msg)
    #         read_msg = re.sub(r'ｗ{3,}', 'わらわら', read_msg)

    #         try:
    #             print(
    #                 f"**{message.guild.name}** {message.author.name}: {read_msg}")
    #         except Exception as e:
    #             print(e)

    #         if len(read_msg) > 50:
    #             read_msg = read_msg[:50] + '以下略'
    #         content = text_2_wav(read_msg, speaker_id)
    #         audio_data = io.BytesIO(content)

    #         try:
    #             source = CustomFFmpegPCMAudio(audio_data, pipe=True)
    #             # print(source)
    #             enqueue(message.guild.voice_client, message.guild, source)
    #         except Exception as e:
    #             print(e)

    # @commands.Cog.listener()
    # async def on_voice_state_update(self, member, before, after):
    #     read_msg = ""
    #     if member.guild.voice_client and member.id != self.bot.user.id and member.guild.voice_client.channel == before.channel and len(member.guild.voice_client.channel.members) == 1:
    #         await member.guild.voice_client.disconnect()
    #         return

    #     if member.id == self.bot.user.id:
    #         return

    #     if before.channel and self.bot.user in before.channel.members or after.channel and self.bot.user in after.channel.members:
    #         if before.channel and before.channel != after.channel and self.bot.user in before.channel.members:
    #             read_msg = f"{member.display_name}が退出しました"
    #         if after.channel and before.channel != after.channel and self.bot.user in after.channel.members:
    #             read_msg = f"{member.display_name}が参加しました"

    #         try:
    #             print(
    #                 f"<Status changed voiceChannel> **{member.guild.name}** : {read_msg}")
    #         except Exception as e:
    #             print(e)

    #         with open("./VC/user_speaker.json", "r", encoding="UTF-8") as f:
    #             speaker = json.load(f)
    #         speaker_id = int(speaker.get(str(member.id), 8))

    #         if os.path.isfile(f"./VC/{member.guild.id}.json"):
    #             print("dict load")
    #             with open(f"./VC/{member.guild.id}.json", "r", encoding="UTF-8") as f:
    #                 word = json.load(f)
    #                 # 辞書のキーに基づいてread_msgをフォーマット
    #                 for key, value in word.items():
    #                     read_msg = read_msg.replace(key, value)

    #         print(read_msg)

    #         content = text_2_wav(read_msg, speaker_id)
    #         audio_data = io.BytesIO(content)

    #         try:
    #             source = CustomFFmpegPCMAudio(audio_data, pipe=True)
    #             # print(source)
    #             enqueue(member.guild.voice_client, member.guild, source)
    #         except Exception as e:
    #             print(e)


async def setup(bot: commands.Bot):
    await bot.add_cog(tokenCog(bot))
