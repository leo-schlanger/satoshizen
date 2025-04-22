import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import json
import os
from datetime import datetime, timedelta, time, timezone
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Load the quote databases
with open("frases.json", "r", encoding="utf-8") as f:
    QUOTES = json.load(f)

with open("frases_degen.json", "r", encoding="utf-8") as f:
    DEGEN_QUOTES = json.load(f)

def pick_quote(degen=False):
    if degen:
        quote = random.choice(DEGEN_QUOTES)
        birthday = False
    else:
        today = datetime.now(timezone.utc).strftime("%m-%d")
        birthday_quotes = [q for q in QUOTES if q["data_nascimento"][5:] == today]
        if birthday_quotes:
            quote = random.choice(birthday_quotes)
            birthday = True
        else:
            quote = random.choice(QUOTES)
            birthday = False
    return quote, birthday

def is_degen_time():
    now = datetime.now(timezone.utc).time()
    return (time(7, 20) <= now <= time(7, 30)) or (time(19, 20) <= now <= time(19, 30))

def build_embed(quote, birthday, periodo):
    titulos = {
        "manha": "🌅 Reflexão Matinal",
        "almoco": "🍽️ Sabedoria do Almoço",
        "encerramento": "🌇 Encerramento do Mercado",
        "manual": None,
        "degen": "🧨 Reflexão Degenerada do Dia"
    }
    is_degen = periodo == "degen" or is_degen_time()
    embed = discord.Embed(
        title=titulos.get(periodo) if not is_degen else "🍃 Reflexão Chapada do Mestre",
        description=f'👤 *{quote["autor"]}*\n\n💬 “{quote["frase"]}”',
        color=discord.Color.purple() if is_degen else discord.Color.gold()
    )
    if birthday:
        embed.add_field(name="🎂", value=f"Hoje é aniversário de {quote['autor']}! 🎉")
    if is_degen:
        embed.set_footer(text="420 approved 🍃 | Ninguém viu isso aqui")
    else:
        embed.set_footer(text="SatoshiZen – Sabedoria cripto diária 🧘‍♂️")
    return embed

async def send_quote(periodo):
    await bot.wait_until_ready()
    channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))
    if channel:
        quote, birthday = pick_quote(degen=(periodo == "degen"))
        await channel.send(embed=build_embed(quote, birthday, periodo))

@tasks.loop(hours=24)
async def quote_manha():
    await send_quote("manha")

@tasks.loop(hours=24)
async def quote_almoco():
    await send_quote("almoco")

@tasks.loop(hours=24)
async def quote_encerramento():
    await send_quote("encerramento")

@tasks.loop(hours=24)
async def quote_degen_1620():
    await send_quote("degen")

@tasks.loop(hours=24)
async def quote_degen_0420():
    await send_quote("degen")

@quote_manha.before_loop
async def before_manha():
    now = datetime.now(timezone.utc)
    target = now.replace(hour=11, minute=30, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

@quote_almoco.before_loop
async def before_almoco():
    now = datetime.now(timezone.utc)
    target = now.replace(hour=15, minute=0, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

@quote_encerramento.before_loop
async def before_encerramento():
    now = datetime.now(timezone.utc)
    target = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

@quote_degen_1620.before_loop
async def before_degen_1620():
    now = datetime.now(timezone.utc)
    target = now.replace(hour=19, minute=20, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

@quote_degen_0420.before_loop
async def before_degen_0420():
    now = datetime.now(timezone.utc)
    target = now.replace(hour=7, minute=20, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

class SatoshiZenGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="satoshizen", description="Frases de sabedoria do mestre SatoshiZen")

    @app_commands.command(name="guideme", description="Peça uma frase de sabedoria cripto do mestre Zen")
    async def guideme(self, interaction: discord.Interaction):
        degen = is_degen_time()
        quote, birthday = pick_quote(degen=degen)
        await interaction.response.send_message(embed=build_embed(quote, birthday, periodo="degen" if degen else "manual"))

@bot.event
async def on_ready():
    print(f"{bot.user} está online.")
    try:
        tree.add_command(SatoshiZenGroup())
        synced = await tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    quote_manha.start()
    quote_almoco.start()
    quote_encerramento.start()
    quote_degen_1620.start()
    quote_degen_0420.start()

keep_alive()
bot.run(TOKEN)
