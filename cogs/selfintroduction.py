from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import cogs.token as token
import scr.database as db

with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class selfintroductionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog selfintroduction.py init!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != int(settings["channel"]["selfintroduction"]):
            return
        else:
            if message.content.startswith("/"):
                try:
                    await message.delete()
                except:
                    pass
                return
            if message.author.bot:
                try:
                    await message.delete()
                except:
                    pass
                return
            userInfo = db.readDB("user", str(message.author.id))
            if userInfo["profile"]["done"] is not False:
                await message.delete()
                await message.channel.send(f"{message.author.mention}さん、すでに自己紹介を完了しています\n編集はwebページから可能です（未開設）", delete_after=20)
                return
            mustItems = [settings["selfintroduction"][str(
                index)]["content"] for index in settings["selfintroduction"].keys()]
            originalMessage = message.content
            selfintroduction = message.content.split("\n")
            missingItems = {}
            for i, items in enumerate(mustItems):
                try:
                    item = selfintroduction[i].split(":")
                    if item[0] != items:
                        missingItems[f"{i+1}1"] = f"項目名**「{items}」**が見つかりませんでした"
                    elif len(item[1]) < settings["selfintroduction"][f"{i+1}"]["min"]:
                        min = settings["selfintroduction"][f"{i+1}"]["min"]
                        missingItems[f"{i+1}2"] = f"項目名**「{items}」**は{min}文字以上で入力してください"
                    else:
                        userInfo["profile"][f"{items}"] = item[1]
                except IndexError:
                    missingItems[f"{i+1}1"] = f"項目名**「{items}」**が見つかりませんでした"

            if len(missingItems.keys()) == 0:
                await message.channel.send(f"{message.author.mention}さん、自己紹介ありがとうございます！！", delete_after=20)
                await message.author.remove_roles(discord.Object(int(settings["role"]["listenOnly"])))
                await message.author.add_roles(discord.Object(int(settings["role"]["individualMember"])))
                await message.add_reaction(":white_check_mark:")
                userInfo["profile"]["done"] = True
                db.writeDB("user", str(message.author.id), userInfo)
                await token.tokenCog(self.bot).giveToken(self.bot.user, message.author, settings["token"]["selfintroduction"]["token"], settings["token"]["selfintroduction"]["description"])
            else:
                await message.delete()
                embed = discord.Embed(
                    title="以下を修正してください", description="修正して再度投稿してください", color=0xff0000)
                for key in missingItems.keys():
                    item = settings["selfintroduction"][f"{key[:1]}"]["content"]
                    embed.add_field(
                        name=f"{item}", value=missingItems[key], inline=False)
                await message.guild.get_channel(int(settings["channel"]["reject"])).send(f"{message.author.mention}さん、修正お願いします\n元のメッセージ\n{originalMessage}", embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(selfintroductionCog(bot))
