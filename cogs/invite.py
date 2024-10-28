from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import cogs.token as token
import scr.database as db

# 設定ファイルの読み込み
with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)

# inviteCogクラスの定義


class inviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        # 設定ファイルの再読み込み
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog invite.py init!")

    # 招待リンクが作成されたときに呼ばれるイベントリスナー
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild.id == int(settings["general"]["GuildID"]):
            # 招待リンクの情報を取得してデータベースに保存
            inviteInfo = {
                "id": invite.id,
                "url": invite.url,
                "inviter": invite.inviter.id,
                "max_age": invite.max_age,
                "uses": invite.uses
            }
            db.writeDB("invite", str(invite.id), inviteInfo)

    # 招待リンクが削除されたときに呼ばれるイベントリスナー
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if invite.guild.id == int(settings["general"]["GuildID"]):
            # データベースから招待リンクの情報を削除
            db.deleteDB("invite", str(invite.id))

    # メンバーがサーバーに参加したときに呼ばれるイベントリスナー
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == int(settings["general"]["GuildID"]):
            # 新規メンバーの情報がデータベースに存在しない場合
            if db.readDB("user", str(member.id)) is None:
                # 現在の招待リンクの使用状況を取得
                invites = await member.guild.invites()
                oldInvites = db.readDB("invite")
                for invite in invites:
                    # 招待リンクの使用回数が増えている場合
                    if int(oldInvites[invite.id]["uses"]) < int(invite.uses):
                        # 招待者にトークンを付与
                        await token.tokenCog(self.bot).giveToken(self.bot.user, member.guild.get_member(int(oldInvites[invite.id]["inviter"])), settings["token"]["invited"]["token"], settings["token"]["invited"]["description"])
                        oldInvites[invite.id]["users"] = invite.uses
                    oldInvites[invite.id]["uses"] = invite.uses
                    # 有効期限が切れた招待リンクを削除
                    if invite.max_age == 0:
                        oldInvites.pop(invite.id)

                # 更新された招待リンクの情報をデータベースに保存
                db.writeDB("invite", oldInvites)

# Cogをセットアップする関数


async def setup(bot: commands.Bot):
    await bot.add_cog(inviteCog(bot))
