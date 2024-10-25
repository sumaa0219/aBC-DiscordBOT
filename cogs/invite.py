from discord.ext import commands
from discord import ui, app_commands
import discord
import json
import cogs.token as token
import scr.database as db

with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class inviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog invite.py init!")

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild.id == int(settings["general"]["GuildID"]):
            inviteInfo = {
                "id": invite.id,
                "url": invite.url,
                "inviter": invite.inviter.id,
                "max_age": invite.max_age,
                "uses": invite.uses
            }
            db.writeDB("invite", str(invite.id), inviteInfo)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if invite.guild.id == int(settings["general"]["GuildID"]):
            db.deleteDB("invite", str(invite.id))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == int(settings["general"]["GuildID"]):
            if db.readDB("user", str(member.id)) is None:
                invites = await member.guild.invites()
                oldInvites = db.readDB("invite")
                for invite in invites:
                    if int(oldInvites[invite.id]["uses"]) < int(invite.uses):
                        await token.tokenCog(self.bot).giveToken(self.bot.user, member.guild.get_member(int(oldInvites[invite.id]["inviter"])), settings["token"]["invited"]["token"], settings["token"]["invited"]["description"])
                        oldInvites[invite.id]["users"] = invite.uses
                    oldInvites[invite.id]["uses"] = invite.uses
                    if invite.max_age == 0:
                        oldInvites.pop(invite.id)

                db.writeDBDB("invite", oldInvites)


async def setup(bot: commands.Bot):
    await bot.add_cog(inviteCog(bot))
