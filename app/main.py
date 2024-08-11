from discord.ext import commands
from configs import DiscordConfig

import loggers
import asyncio
import colorama
import discord
import os
import yaml


colorama.init(autoreset=True)

# Устанавливаем параметры намерений (intents) для бота
intents = discord.Intents.all()
intents.message_content = True
intents.messages = True
intents.members = True

discord_config = DiscordConfig()

# Create an instance of a bot
bot = commands.Bot(
    command_prefix=discord_config.bot_prefix,
    case_insensitive=bool(discord_config.case_insensitive),
    intents=intents,
)

logger = loggers.setup_logger("main")


async def load():
    module_states = load_modules_states()
    if not module_states:
        module_states = {}
    for filename in os.listdir("./modules"):        
        if filename.endswith(".py"):
            module_name = filename[:-3]
            if module_name == "__init__":
                continue
            if not module_states.get(module_name):
                module_states[module_name] = "loaded"
                save_modules_states(module_states)
            if module_states.get(module_name, "loaded") != "unloaded":
                try:
                    await bot.load_extension(f"modules.{module_name}")
                    logger.info(f"[modules] Modules {module_name} working")
                except Exception as e:
                    logger.error(f"[modules] Modules {module_name} not working => {e}")


def load_modules_states():
    if not os.path.isfile("./settings/module_state.yaml"):
        with open("./settings/module_state.yaml", "w+") as file:
            yaml.dump({}, file)
            return {}

    with open("./settings/module_state.yaml", "r") as file:
        return yaml.safe_load(file)


def save_modules_states(state):
    with open("./settings/module_state.yaml", "w+") as file:
        yaml.dump(state, file)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f"Error: {error}")
    raise error


@bot.command(name="reload")
@commands.is_owner()
async def reload(ctx, extension):
    if os.path.isfile(f"./modules/{extension}.py"):
        try:
            await bot.unload_extension(f"modules.{extension}")
            await bot.load_extension(f"modules.{extension}")
            await ctx.send(f"Модуль {extension} был перезагружен.")
        except Exception as e:
            await ctx.send(f"Ошибка при перезагрузке модуля: {e}")


@bot.command(name="load")
@commands.is_owner()
async def loads(ctx, extension):
    if os.path.isfile(f"./modules/{extension}.py"):
        try:
            await bot.load_extension(f"modules.{extension}")
            _text = f"Модуль {extension} загружен."
            await ctx.send(_text)
            logger.info(_text)
        except Exception as e:
            await ctx.send(f"Ошибка при загрузке модуля: {e}")
    else:
        await ctx.send(f"Модуль {extension} не найден.")
    state = load_modules_states()
    state[extension] = "loaded"
    save_modules_states(state)


@bot.command(name="unload")
@commands.is_owner()
async def unload(ctx, extension):
    try:
        await bot.unload_extension(f"modules.{extension}")
        await ctx.send(f"Модуль {extension} выгружен.")
    except Exception as e:
        await ctx.send(f"Ошибка при выгрузке модуля: {e}")
    state = load_modules_states()
    state[extension] = "unloaded"
    save_modules_states(state)


async def main():
    logger.info("Bot started.")
    await load()
    await bot.start(discord_config.token)

asyncio.run(main())
