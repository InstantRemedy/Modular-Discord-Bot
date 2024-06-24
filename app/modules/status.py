import os
import aiofiles
import discord
import yaml
from discord.ext import commands


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "I'ma status module!"

    @commands.command(name="modstatus")
    async def mod_status(self, ctx):
        embed = discord.Embed(
            title="Status Modules", description="Test", color=discord.Color.blue()
        )

        modules = [
            f[:-3]
            for f in os.listdir("modules")
            if f.endswith(".py") and not f.startswith("_")
        ]
        
        async with open("settings/module_descriptions.yaml", "r+") as f:
            data = await f.read()
            module_description = yaml.safe_load(data)
        
        for module in modules:
            description = module_description.get(module, "Nothing")
            status_emoji = "🟢" if f"modules.{module}" in self.bot.extensions else "🔴"
            embed.add_field(
                name=f"{status_emoji} {module}", value=description, inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Status(bot))
