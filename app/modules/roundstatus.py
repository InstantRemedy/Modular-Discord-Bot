from discord.ext import commands, tasks
from .plugins.byond_topic import queryStatus
from configs.modules import RoundStatusConfig

import enum
import datetime
import time
import discord
import loggers
import ipaddress

logger = loggers.setup_logger("roundstatus")
config = RoundStatusConfig()


def check_roles(ctx: commands.Context):
    if any(role.id == config.main_role for role in ctx.author.roles):
        return True
    if any(role.id in config.allowed_roles for role in ctx.author.roles):
        return True
    
    raise commands.CheckFailure(
        f"User '{ctx.author.display_name}' don't have access to the 'AI' module.")


def check_main_role(ctx: commands.Context):
    if any(role.id == config.main_role for role in ctx.author.roles):
        return True
    
    raise commands.CheckFailure(
        f"User '{ctx.author.display_name}' don't have access to the 'AI' module.")


class GameState(enum.Enum):
    UNKNOWN = -1337
    STARTUP = 0
    LOBBY = 1 or 2
    IN_GAME = 3
    ENDGAME = 4


class ServerConnector:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def query_status(self):
        try:
            logger.info(f"Trying get query status from {self.host}:{self.port}")
            response_data = await queryStatus(self.host, self.port)
            return response_data
        except ConnectionRefusedError:
            logger.warning("Connection refused by the server.")
            raise
        except ConnectionResetError:
            logger.info("Server is restarting.")
            raise
        except ConnectionError as conn_err:
            logger.info(f"Connection error: {conn_err}")
            raise
        except Exception as ex:
            logger.warning(f"An error occurred: {ex}")
            raise


class Roundstatus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "Checks for round continuity on server."
        self.channel_alert = None 
        self.channel_alert_id = config.channel
        self.last_game_state = GameState.UNKNOWN
        self.init = False
        self.is_notification_available_sended = False
    
    def cog_unload(self):
        self.round_checker.cancel()

    def server_availability(self):
        if self.is_notification_available_sended:
            return
        logger.warning("Сервер выключен.")
        self.is_notification_available_sended = True

    def make_embed(self, response_data, current_time, current_game_state):
        footer_text = "Сплетено пауком"
        footer_icon = "https://cdn.discordapp.com/attachments/593969947579777035/1248147974245056553/Lolth_Icon.png?ex=66629be2&is=66614a62&hm=4e8bb603b14859f7360070cd3c7b38e886eb776edcb9942c3a95f6f7d49a4014&"
        thumbnail = "https://media.discordapp.net/attachments/1243587366271189084/1246818328991764530/3xb0si6diyi91_copy.png?ex=665dc58e&is=665c740e&hm=263eb17e934939d411b04341df87f30483162ceb486bc7f5d904feb47c66b963&=&format=webp&quality=lossless"

        if current_game_state == GameState.STARTUP:
            embed = discord.Embed(
                title="Раунд",
                color=discord.Color.orange(),
            ).set_footer(
                text=footer_text,
                icon_url=footer_icon,
            ).set_thumbnail(
                url=thumbnail,
            ).add_field(
                name="Статус",
                value="Запуск сервера",
                inline=False,
            )
        elif current_game_state == GameState.LOBBY:
            embed = discord.Embed(
                title="Раунд",
                color=discord.Color.blue(),
            ).set_footer(
                text=footer_text,
                icon_url=footer_icon,
            ).set_thumbnail(
                url=thumbnail,
            ).add_field(
                name="Статус",
                value="Лобби",
                inline=False,
            )
        elif current_game_state == GameState.IN_GAME:
            embed = discord.Embed(
                title="Раунд",
                color=discord.Color.green(),
            ).set_footer(
                text=footer_text,
                icon_url=footer_icon,
            ).set_thumbnail(
                url=thumbnail,
            ).add_field(
                name="Статус",
                value="Идёт раунд",
                inline=False,
            ).add_field(
                name="Количество игроков",
                value=response_data["players"][0] + " игрок(ов)",
            ).add_field(
                name="Время раунда",
                value=time.strftime("%H:%M", time.gmtime(current_time)),
            )
        elif current_game_state == GameState.ENDGAME:
            embed = discord.Embed(
                title="Раунд",
                color=discord.Color.dark_magenta(),
            ).set_footer(
                text=footer_text,
                icon_url=footer_icon,
            ).set_thumbnail(
                url=thumbnail,
            ).add_field(
                name="Статус",
                value="Окончание раунда",
                inline=False,
            ).add_field(
                name="Раунд завершён",
                value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        else:
            raise ValueError("Unknown game state")

        return embed

    @tasks.loop(seconds=60.0)
    async def round_checker(self):
        if not config.host or not config.port:
            logger.warning("host or port not specified")
            return
        
        try:
            response_data = await ServerConnector(config.host, config.port).query_status()
            self.is_notification_available_sended = False
        except ConnectionRefusedError:
            self.server_availability()
            return
        except ConnectionResetError:
            return
        except ConnectionError:
            return
        except Exception as ex:
            return

        logger.info(f"Response data: {response_data}")
        current_time = int(response_data["round_duration"][0])
        game_state_value = int(response_data["gamestate"][0])

        if game_state_value == 1 or game_state_value == 2:
            current_game_state = GameState.LOBBY
        else:
            current_game_state = GameState(game_state_value)

        self.bot.custom_embed = self.make_embed(
            response_data=response_data,
            current_game_state=current_game_state,
            current_time=current_time
        )
        if not self.init or \
                (current_game_state == GameState.STARTUP and
                 current_game_state != self.last_game_state):
            self.bot.custom_embed_message = await self.channel_alert.send(embed=self.bot.custom_embed)
            await self.channel_alert.send(
                f'<@&1227295722123296799> Новый раунд```byond://rockhill-game.ru:51143```'
            )
        else:
            await self.bot.custom_embed_message.edit(embed=self.bot.custom_embed)

        self.last_game_state = current_game_state
        self.init = True

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Channel is {self.channel_alert_id}")
        self.channel_alert = self.bot.get_channel(self.channel_alert_id)
        self.round_checker.start()

    @commands.check(check_roles)
    @commands.command(name="rs_host")
    async def setup_host(self, ctx: commands.Context, *, host: str):
        try:
            ipaddress.ip_address(host)
            await config.async_set_host(host)
            logger.info(f"User {ctx.author.display_name} set the host to {host}")
            await ctx.reply(f"Host set to {host}")
        except ValueError:
            await ctx.reply("Invalid IP address")

    @commands.check(check_roles)
    @commands.command(name="rs_port")
    async def setup_port(self, ctx: commands.Context, *, port: int):
        if port < 0 or port > 65535:
            await ctx.reply("Invalid port")
            return

        logger.info(f"User {ctx.author.display_name} set the port to {port}")
        await config.async_set_port(port)

    @commands.check(check_main_role)
    @commands.command(name="rs_add_role")
    async def add_role(self, ctx: commands.Context, *, role: int):
        await config.async_add_role(role)
        await ctx.reply(f"Role {role} added")

    @commands.check(check_main_role)
    @commands.command(name="rs_remove_role")
    async def remove_role(self, ctx: commands.Context, *, role: int):
        await config.async_remove_role(role)
        await ctx.reply(f"Role {role} removed")


async def setup(bot):
    await bot.add_cog(Roundstatus(bot))
