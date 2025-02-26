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

# トランザクションIDの桁数
transactionIDNum = 10

# 設定ファイルの読み込み
with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)

# tokenCogクラスの定義


class tokenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        # 設定ファイルの再読み込み
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog token.py init!")

    # Botが準備完了したときに呼ばれるイベントリスナー
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog token.py ready!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.giveToken(self.bot.user, payload.member, settings["token"]["reaction"]["token"], settings["token"]["reaction"]["description"])

    # トークン残高を表示するコマンド

    @app_commands.command(name=settings["commands"]["show"]["command"], description=settings["commands"]["show"]["description"])
    async def show(self, interaction: discord.Interaction):
        user = db.readDB("user", str(interaction.user.id))
        token = user["token"]
        await interaction.response.send_message(f"あなたのトークン残高は{token:,}トークンです", ephemeral=True)

    # トークンを送信するコマンド
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

    # 管理者がトークンを送信するコマンド
    @app_commands.command(name=settings["commands"]["adminsend"]["command"], description=settings["commands"]["adminsend"]["description"])
    @app_commands.default_permissions(administrator=True)
    async def adminsend(self, interaction: discord.Interaction, user: discord.Member, amount: int, text: str):
        await self.giveToken(self.bot.user, user, amount, text)
        await interaction.response.send_message(f"{user.mention}さんに{amount}トークンを付与しました")

    @app_commands.command(name=settings["commands"]["showalltoken"]["command"], description=settings["commands"]["showalltoken"]["description"])
    @app_commands.default_permissions(administrator=True)
    async def showalltoken(self, interaction: discord.Interaction):
        userInfos = db.readDB("user")
        tokenList = []
        for userID in userInfos.keys():
            userInfo = userInfos[userID]
            tokenList.append(
                {"name": userInfo["userDisplayName"], "token": userInfo["token"]})
        tokenList = sorted(tokenList, key=lambda x: x["token"], reverse=True)
        ranking = self.format_ranking(tokenList)
        await interaction.response.send_message(content=ranking)

    # サーバー参加時に呼ばれるイベントリスナー

    @app_commands.command(name="addmember", description="addmember")
    @app_commands.default_permissions(administrator=True)
    async def addmember(self, interaction: discord.Interaction, user: discord.Member):
        if db.readDB("user", str(user.id)) != None:
            return
        userInfomation = self.getDefaultData(user, 0)
        # userInfomationをDBに書き込み
        db.writeDB("user", str(user.id), userInfomation)
        # 非同期で３秒待ってトークン付与
        await self.giveToken(self.bot.user, user, settings["token"]["join"]["token"], settings["token"]["join"]["description"])
        # await user.add_roles(user.guild.get_role(int(settings["role"]["listenOnly"])))
        await interaction.response.send_message(f"{user.mention}さん、ようこそ！", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if db.readDB("user", str(member.id)) != None:
            return
        userInfomation = self.getDefaultData(member, 0)
        # userInfomationをDBに書き込み
        db.writeDB("user", str(member.id), userInfomation)
        # 非同期で３秒待ってトークン付与
        await asyncio.sleep(3)
        await self.giveToken(self.bot.user, member, settings["token"]["join"]["token"], settings["token"]["join"]["description"])
        await member.add_roles(member.guild.get_role(int(settings["role"]["listenOnly"])))
        await self.bot.get_guild(int(settings["general"]["GuildID"])).get_channel(
            int(settings["channel"]["welcome"])).send(f"{member.mention}さん、ようこそ！")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        target_channels = [1334164688216264734,
                           1277805623999725590]  # ここに対象のチャンネルIDを追加
        target_categories = [1271333937804873770]  # ここに対象のカテゴリIDを追加
        if (message.channel.id in target_channels or
                (message.channel.category and message.channel.category.id in target_categories)):
            await self.giveToken(self.bot.user, message.author, 100, "投稿ありがとうございます")

    # メンバー情報を再読み込みするコマンド

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

    # デフォルトのユーザー情報を取得する関数
    def getDefaultData(self, member: discord.Member, hasToken: int):
        userInfomation = {
            "userID": str(member.id),
            "userDisplayName": member.display_name,
            "userDisplayIcon": str(member.display_avatar.url),
            "token": hasToken,
            "userHighestRole": member.guild.get_role(int(member.roles[-1].id)).name,
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
                "yearly": None,
                "total": 0
            },
            "vote": {
                "count": 3,
                "voteList": None
            },
            "agenda": {
                "idList": [],
            }

        }
        return userInfomation

    def format_ranking(self, users):
        # 最大の名前の長さを取得
        max_name_length = max(len(user['name']) for user in users)

        ranking = ""
        for i, user in enumerate(users):
            # 名前の長さに応じて空白を追加
            name = user['name']
            token = f"{user['token']:,}トークン"
            spaces = ' ' * (max_name_length - len(name) + 10)  # 5はタブの代わりのスペース数
            ranking += f"{i+1}位 {name}{spaces}{token}\n"

        return ranking

    # トークンを送信する関数
    async def giveToken(self, fromUser: discord.Member, toUser: discord.Member, amount: int, discription: str):
        print("giveToken fuction called")
        isBOT = False

        # 送金処理(送られた側)
        targetInfo = db.readDB("user", str(toUser.id))
        targetInfo["token"] = targetInfo["token"] + amount
        db.writeDB("user", str(toUser.id), targetInfo)
        print(f"{fromUser.display_name}から{toUser.display_name}に{amount}トークン送金を開始します")

        if fromUser.id == int(settings["general"]["botClientID"]):
            isBOT = True
        else:
            userInfo = db.readDB("user", str(fromUser.id))
            userInfo["token"] = userInfo["token"] - amount
            db.writeDB("user", str(fromUser.id), userInfo)

        print("transaction completed")

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

# Cogをセットアップする関数


async def setup(bot: commands.Bot):
    await bot.add_cog(tokenCog(bot))
