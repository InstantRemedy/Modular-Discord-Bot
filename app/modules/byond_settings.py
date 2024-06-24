from discord.ext import commands

import loggers
import config

logger = loggers.setup_logger("byond_settings")

ALLOWED_ROLE_IDS = [
    1227291822917816402
]

def check_roles(ctx):
    if any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        return True
    
    raise commands.CheckFailure(f"User '{ctx.author.display_name}' don't have access to the 'Byond settings' module.")


class Byond_settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "I'm byond_settings cog!"

    @commands.check(check_roles)
    @commands.command(name="setup_host")
    async def setup_host(self, ctx, *, host: str):
        logger.info(f"User {ctx.author.display_name} set the host to {host}")
        await config.byond.async_set_host(host)
    
    @commands.check(check_roles)
    @commands.command(name="setup_port")
    async def setup_port(self, ctx, *, port: str):
        logger.info(f"User {ctx.author.display_name} set the port to {port}")
        await config.byond.async_set_port(int(port))


async def setup(bot):
    await bot.add_cog(Byond_settings(bot))
