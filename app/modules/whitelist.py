from discord.ext import commands

from configs.modules import WhitelistConfig
import loggers
import os


FORBIDDEN_CHARS = [
    "@",
    "/",
    '"',
    "'",
    ";",
    "<",
    ">",
    "{",
    "}",
    "[",
    "]",
    "|",
    "&",
    "^",
    "%",
    "$",
    "#",
    "!",
    "\\",
    ":",
    "*",
    "?",
    "`",
    "~",
    "=",
    "+",
]

logger = loggers.setup_logger("whitelist")
config = WhitelistConfig()


def check_roles(ctx: commands.Context):
    if any(role.id == config.main_role for role in ctx.author.roles):
        return True
    if any(role.id in config.allowed_roles for role in ctx.author.roles):
        return True
    
    raise commands.CheckFailure(
        f"User '{ctx.author.display_name}' don't have access to the 'Whitelist' module.")


def check_main_role(ctx: commands.Context):
    if any(role.id == config.main_role for role in ctx.author.roles):
        return True
    
    raise commands.CheckFailure(
        f"User '{ctx.author.display_name}' don't have access to the 'Whitelist' module.")


def contains_forbidden_chars(name):
    return any(char in name for char in FORBIDDEN_CHARS)


class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "I'ma whitelist module!"

    @commands.check(check_roles)
    @commands.command()
    async def whitelist(self, ctx, action, *, name):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, "whitelist.txt")
        action = action.lower()

        # Отладочное сообщение
        logger.info(f"Работаем с файлом: {file_path}")
        logger.info(f"Действие: {action}, пользователь: {name}")

        if contains_forbidden_chars(name):
            await ctx.send(
                "Недопустимые символы в имени. Пожалуйста, используйте другое имя."
            )
            return

        with open(file_path, "r") as f:
            lines = f.readlines()

        if action == "add":
            if name + "\n" in lines:
                await ctx.send(f"{name} уже есть в списке!")
                return
            with open(file_path, "a") as f:
                f.write(name + "\n")
            await ctx.send(f"{name} было отправлено на опыты!")
            logger.warning(f"{ctx.author} добавил {name}")

        elif action == "remove":
            if name + "\n" not in lines:
                await ctx.send(f"{name} нет в списке!")
                return
            with open(file_path, "w") as f:
                for line in lines:
                    if line.strip("\n") != name:
                        f.write(line)
            await ctx.send(f"{name} было отправлено в чистилище!")
            logger.warning(f"{ctx.author} удалил {name}")

        else:
            await ctx.send(f"Неизвестное действие: {action}")

    @whitelist.error
    async def whitelist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Недостаточно прав для использования этой команды!")
        else:
            await ctx.send("Произошла ошибка!")

    @commands.check(check_main_role)
    @commands.command(name="wl_add_role")
    async def add_role(self, ctx: commands.Context, *, role: int):
        config.add_role(role)
        await ctx.reply(f"Role {role} added")

    @commands.check(check_main_role)
    @commands.command(name="wl_remove_role")
    async def remove_role(self, ctx: commands.Context, *, role: int):
        config.remove_role(role)
        await ctx.reply(f"Role {role} removed")


async def setup(bot):
    await bot.add_cog(Whitelist(bot))
