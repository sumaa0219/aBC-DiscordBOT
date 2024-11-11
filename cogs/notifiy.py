from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import cogs.token as token
import scr.database as db
from dotenv import load_dotenv
import requests
import smtplib
from email.mime.text import MIMEText
import os
load_dotenv()

# 設定ファイルの読み込み
with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)

# notifiyCogクラスの定義


class notifiyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        # 設定ファイルの再読み込み
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog notifiy.py init!")

    # 特定のロールを持っているユーザーにメッセージを転送するコマンド
    @app_commands.command(name=settings["commands"]["resistmail"]["command"], description=settings["commands"]["resistmail"]["description"])
    @app_commands.checks.has_role(int(settings["role"]["manager"]))
    async def resistmail(self, interaction: discord.Interaction):
        modal = resiEmail(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name=settings["commands"]["switchmail"]["command"], description=settings["commands"]["switchmail"]["description"])
    @app_commands.checks.has_role(int(settings["role"]["manager"]))
    async def switchmail(self, interaction: discord.Interaction):
        if db.readDB("notifiemail", str(interaction.user.id)) is None:
            await interaction.response.send_message("メールアドレスが登録されていません", ephemeral=True)
            return
        if db.readDB("notifiemail", str(interaction.user.id))["active"]:
            userINfo = db.readDB("notifiemail", str(interaction.user.id))
            userINfo["active"] = False
            db.writeDB("notifiemail", str(interaction.user.id), userINfo)
            await interaction.response.send_message("メールアドレスの通知をオフにしました", ephemeral=True)
        else:
            userINfo = db.readDB("notifiemail", str(interaction.user.id))
            userINfo["active"] = True
            db.writeDB("notifiemail", str(interaction.user.id), userINfo)
            await interaction.response.send_message("メールアドレスの通知をオンにしました", ephemeral=True)

    # メッセージが送信されたときに呼ばれるイベントリスナー

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # 特定のチャンネルでメッセージが送信された場合
        if str(message.channel.id) in list(settings["notification"].keys()):
            message.content = message.content.replace(
                "@everyone", "<!channel>").replace("@here", "<!here>")
            notifiyMessage = f"*Discordからの転送*\n{message.author.display_name}さん\n\n\n{message.content}\n\n\n{message.jump_url}"
            self.sendNotifiySlack(message.channel.id, notifiyMessage)
            print("send slack")
            for mailAdress in db.readDB("notifiemail").values():
                print(mailAdress)
                if mailAdress["active"]:
                    print("send mail")
                    self.sendNotifiyEmail(
                        notifiyMessage, mailAdress["email"])

            return

    # メッセージを転送する関数
    def sendNotifiySlack(self, channelID, message: str):
        webhookURL = settings["notification"][str(channelID)]["webhookURL"]
        payload = {
            'text': message
        }

        response = requests.post(webhookURL, json=payload)

        if response.status_code == 200:
            print('Message posted successfully')
        else:
            print(f'Failed to post message: {response.status_code}')

    def sendNotifiyEmail(self, message: str, toAdress: str):
        """ メッセージのオブジェクト """
        msg = MIMEText(message, "plain", "utf-8")
        msg['Subject'] = "Discordからの転送"
        msg['From'] = os.environ["notifiemail"]
        msg['To'] = toAdress

        # エラーキャッチ
        try:
            """ SMTPメールサーバーに接続 """
            smtpobj = smtplib.SMTP(
                'smtp.gmail.com', 587)  # SMTPオブジェクトを作成。smtp.gmail.comのSMTPサーバーの587番ポートを設定。
            smtpobj.ehlo()                                 # SMTPサーバとの接続を確立
            smtpobj.starttls()                             # TLS暗号化通信開始
            # Googleアカウント(このアドレスをFromにして送られるっぽい)
            gmail_addr = os.environ["notifiemail"]
            app_passwd = os.environ['notifipassword']       # アプリパスワード
            smtpobj.login(gmail_addr, app_passwd)          # SMTPサーバーへログイン

            """ メール送信 """
            smtpobj.sendmail(os.environ["notifiemail"],
                             toAdress, msg.as_string())

            """ SMTPサーバーとの接続解除 """
            smtpobj.quit()

        except Exception as e:
            print(e)

        return "メール送信完了"
# メールアドレスを登録するためのモーダルクラス


class resiEmail(ui.Modal):
    def __init__(self, cog):
        super().__init__(title="メッセージを転送してほしいメールアドレスを入力してください",)
        self.cog = cog
        self.email = discord.ui.TextInput(
            label="adress", placeholder="メールアドレスを入力してください", min_length=1, max_length=100)
        self.add_item(self.email)

    # モーダルが送信されたときに呼ばれる関数

    async def on_submit(self, interaction: discord.Interaction):
        # メールアドレスになっているかチェック
        if "@" not in self.email.value:
            await interaction.response.send_message("メールアドレスの形式が正しくありません", ephemeral=True)
            return
        if db.readDB("notifiemail", str(interaction.user.id)) is None:
            userINfo = {
                "email": self.email.value,
                "active": True
            }
            db.writeDB("notifiemail", str(interaction.user.id), userINfo)

            await interaction.response.send_message("メールアドレスの登録が完了しました。", ephemeral=True)

        else:
            userINfo = db.readDB("notifiemail", str(interaction.user.id))
            userINfo["email"] = self.email.value
            userINfo["active"] = True
            db.writeDB("notifiemail", str(interaction.user.id), userINfo)
            await interaction.response.send_message("メールアドレスの変更が完了しました。", ephemeral=True)

# Cogをセットアップする関数


async def setup(bot: commands.Bot):
    await bot.add_cog(notifiyCog(bot))
