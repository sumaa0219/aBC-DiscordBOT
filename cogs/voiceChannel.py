import discord
import json
import time
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View

with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)


class VoiceChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.created_channels = []  # 作成されたチャンネルのIDを保持するリスト
        global settings
        with open(f"setting.json", "r", encoding="UTF-8") as f:
            settings = json.load(f)
        print("Cog voiceChannel.py init!")
        if self.check_empty_channels.is_running():
            self.check_empty_channels.restart()
        else:
            self.check_empty_channels.start()

    def cog_unload(self):
        self.check_empty_channels.cancel()

    @app_commands.command(name=settings["commands"]["add"]["command"], description=settings["commands"]["add"]["description"])
    async def add(self, interaction: discord.Interaction, user: discord.Member):
        guild = interaction.guild
        channel = interaction.channel

        if channel.id not in self.created_channels:
            await interaction.response.send_message("このチャンネルはボタンで作成されたチャンネルではありません。", ephemeral=True)
            return

        await channel.set_permissions(user, view_channel=True)

        await interaction.response.send_message(f"{user.mention}にチャンネルの閲覧権限を付与しました。")

    @tasks.loop(minutes=3)
    async def check_empty_channels(self):
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if channel.id in self.created_channels and len(channel.members) == 0:
                    await channel.delete()
                    self.created_channels.remove(
                        channel.id)  # 削除されたチャンネルのIDをリストから削除


async def buttonSetup(bot: commands.Bot):
    channel = bot.get_channel(int(settings["channel"]["voiceChannelButton"]))
    try:
        async for message in channel.history(limit=200):
            await message.delete()
            time.sleep(0.1)
    except:
        pass
    view = voiceChannelView(bot, timeout=None)
    await channel.send(view=view)


class voiceChannelView(discord.ui.View):  # UIキットを利用するためにdiscord.ui.Viewを継承する
    def __init__(self, bot, timeout=None):  # Viewにはtimeoutがあり、初期値は180(s)である
        super().__init__(timeout=timeout)
        self.bot = bot

    @discord.ui.button(label="ボイスチャンネル作成", style=discord.ButtonStyle.success)
    async def genVoiceChannel(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        category_id = settings["category"]["interchange"]  # カテゴリIDを設定ファイルから取得
        category = discord.utils.get(guild.categories, id=int(category_id))

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=False),
            member: discord.PermissionOverwrite(
                connect=True, view_channel=True)
        }
        channel = await guild.create_voice_channel(f"{member.name}のチャンネル", overwrites=overwrites, category=category)
        await channel.send(f"{member.mention} がこのチャンネルを作成しました。\n``/add``を使用することで他のユーザーをこのボイスチャンネルに追加できます。")
        self.bot.get_cog("VoiceChannelCog").created_channels.append(
            channel.id)  # 作成されたチャンネルのIDをリストに追加
        await interaction.response.send_message(f"プライベートボイスチャンネルを作成しました: {channel.name}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(VoiceChannelCog(bot))
    await buttonSetup(bot)
