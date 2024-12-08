from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import cogs.token as token
import scr.database as db
import time

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

    # 招待リンクが削除されたときに呼ばれるイベントリスナー

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        print("invite_delete")
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


async def buttonSetup(bot: commands.Bot):
    channel = bot.get_channel(int(settings["channel"]["invitation"]))
    try:
        async for message in channel.history(limit=200):
            await message.delete()
            time.sleep(0.1)
    except:
        pass
    view = InvitationView(bot, timeout=None)
    await channel.send(view=view)


class InvitationView(discord.ui.View):  # UIキットを利用するためにdiscord.ui.Viewを継承する
    def __init__(self, bot, timeout=None):  # Viewにはtimeoutがあり、初期値は180(s)である
        super().__init__(timeout=timeout)
        self.bot = bot

    @discord.ui.button(label="招待リンクを作成", style=discord.ButtonStyle.success)
    async def invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        invite = await interaction.channel.create_invite(max_age=0, max_uses=1, unique=True)
        # 招待リンクの情報を取得してデータベースに保存
        inviteInfo = {
            "id": invite.id,
            "url": invite.url,
            "inviter": interaction.user.id,
            "max_age": invite.max_age,
            "max_uses": invite.max_uses,
            "uses": invite.uses
        }
        db.writeDB("invite", str(invite.id), inviteInfo)
        message = f"招待リンクを作成しました。招待リンクは\nhttps://dao.andbeyondcompany.com/join?code={invite.id}\nです。"
        await interaction.response.send_message(content=message, ephemeral=True)

# Cogをセットアップする関数


async def setup(bot: commands.Bot):
    await bot.add_cog(inviteCog(bot))
    await buttonSetup(bot)
