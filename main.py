import discord
import discord.opus
from discord.ext import commands
import os
from dotenv import load_dotenv
import argparse
import locale


# mac用
# discord.opus.load_opus("libopus.dylib")
# discord.opus.load_opus("/usr/local/Cellar/opus/1.4/lib/libopus.dylib")

# ubuntu用
# if not discord.opus.is_loaded():
#     discord.opus.load_opus("libopus.so.0")
#     if not discord.opus.is_loaded():
#         discord.opus.load_opus("/usr/lib/x86_64-linux-gnu/libopus.so.0")
#         print("subopus loaded")


locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')

load_dotenv()


parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true",
                    help="Use the debug token")
args = parser.parse_args()

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

if args.debug:
    TOKEN = os.environ['debug']
else:
    TOKEN = os.environ['token']


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.cogmanager")
    await bot.load_extension("cogs.login")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=str(len(bot.guilds))+"servers"))


bot.run(TOKEN)
