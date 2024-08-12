from discord.ext import commands, tasks
from .plugins.byond_topic import queryStatus
from configs.modules import RoundStatusConfig

import asyncio
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
    LOBBY = [1, 2]
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


class RoundStatus(commands.Cog):
    __footer_icon = "https://cdn.discordapp.com/attachments/" \
                    "593969947579777035/1248147974245056553/" \
                    "Lolth_Icon.png?" \
                    "ex=66629be2&is=66614a62&hm=4e8bb603b14859f7360070cd3c7b38e886eb776edcb9942c3a95f6f7d49a4014&"

    __thumbnail_icon = "https://media.discordapp.net/attachments/" \
                       "1243587366271189084/1246818328991764530/" \
                       "3xb0si6diyi91_copy.png?" \
                       "ex=665dc58e&is=665c740e&hm=" \
                       "263eb17e934939d411b04341df87f30483162ceb486bc7f5d904feb47c66b963&=&format=webp&quality=lossless"

    def __init__(self, bot: commands.Bot):
        self.__bot = bot
        self.__channel_alert_id = config.channel
        self.__last_game_state = GameState.UNKNOWN
        self.__init = False
        self.__is_notification_available_sent = False
        self.__failed_attempts = 0
        self.__channel_alert: discord.TextChannel

    def cog_unload(self):
        self.__task_loop.cancel()

    def server_availability(self):
        if self.__is_notification_available_sent:
            return
        logger.warning("Сервер выключен.")
        self.__is_notification_available_sent = True

    @tasks.loop(seconds=5)
    async def __task_loop(self):
        try:
            await self.__check_tick()
        except Exception as ex:
            logger.error(f"An error occurred: {ex}")

    async def __check_tick(self):
        if not config.host or not config.port:
            logger.warning("host or port not specified")
            return

        try:
            response_data = await ServerConnector(config.host, config.port).query_status()
            self.__is_notification_available_sent = False
        except ConnectionRefusedError:
            self.server_availability()
            self.__failed_attempts += 1
            if self.__failed_attempts >= 5:
                self.__init = False
                self.__failed_attempts = 0
            return
        except (ConnectionError, ConnectionResetError, Exception):
            self.__failed_attempts += 1
            if self.__failed_attempts >= 5:
                self.__init = False
                self.__failed_attempts = 0
            return

        self.__failed_attempts = 0
        current_time = int(response_data["round_duration"][0])
        game_state_value = int(response_data["gamestate"][0])

        if game_state_value in GameState.LOBBY.value:
            current_game_state = GameState.LOBBY
        else:
            current_game_state = GameState(game_state_value)

        logger.info(f"Game state: {current_game_state.name}. " 
                    f"Time: {time.strftime("%H:%M", time.gmtime(current_time))}")

        self.__bot.custom_embed = self.__make_embed(
            response_data=response_data,
            game_state=current_game_state,
            current_time=current_time
        )
        
        if (not self.__init or
                (current_game_state == GameState.STARTUP and
                 current_game_state != self.__last_game_state and
                 self.__last_game_state == GameState.ENDGAME)):
            self.__custom_embed_message = await self.__channel_alert.send(embed=self.__bot.custom_embed)
            await self.__channel_alert.send(
                '<@&1227295722123296799> Новый раунд```byond://rockhill-game.ru:51143```'
            )
            self.__init = True
        else:
            await self.__custom_embed_message.edit(embed=self.__bot.custom_embed)

        self.__last_game_state = GameState(current_game_state.value)

    def __make_embed(self, response_data, current_time, game_state):
        match game_state:
            case GameState.STARTUP:
                embed = RoundStatus.__embed_template(
                    color=discord.Color.orange(),
                    status="Запуск сервера"
                )
            case GameState.LOBBY:
                embed = RoundStatus.__embed_template(
                    color=discord.Color.blue(),
                    status="Лобби"
                )
            case GameState.IN_GAME:
                embed = RoundStatus.__embed_template(
                    color=discord.Color.green(),
                    status="Идёт раунд"
                ).add_field(
                    name="Количество игроков",
                    value=response_data["players"][0] + " игрок(ов)",
                ).add_field(
                    name="Время раунда",
                    value=time.strftime("%H:%M", time.gmtime(current_time)),
                )
            case GameState.ENDGAME:
                embed = RoundStatus.__embed_template(
                    color=discord.Color.dark_magenta(),
                    status="Окончание раунда"
                ).add_field(
                    name="Раунд завершён",
                    value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
            case _:
                raise ValueError("Unknown game state")

        return embed

    def __embed_template(color: discord.Colour, status: str) -> discord.embeds.Embed:
        return discord.Embed(
            title="Раунд",
            color=color,
        ).set_footer(
            text="Сплетено пауком",
            icon_url=RoundStatus.__footer_icon,
        ).set_thumbnail(
            url=RoundStatus.__thumbnail_icon,
        ).add_field(
            name="Статус",
            value=status,
            inline=False,
        )

    @property
    def description(self) -> str:
        return "I'ma roundstatus module!"

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Channel is {self.__channel_alert_id}")
        self.__channel_alert = self.__bot.get_channel(self.__channel_alert_id)
        self.__task_loop.start()

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
    await bot.add_cog(RoundStatus(bot))
