from discord.ext import commands, tasks
from .plugins.byond_topic import queryStatus

import enum
import config
import datetime
import time
import discord
import loggers

logger = loggers.setup_logger("roundstatus")


class Gamestate(enum.Enum):
    UNKNOWN = -1337
    STARTUP = 0
    LOBBY = 1 or 2
    INGAME = 3
    ENDGAME = 4


class ServerConnector:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def query_status(self):
        try:
            logger.info(f"Trying get query status from {self.host}:{self.port}")
            responseData = await queryStatus(self.host, self.port)
            return responseData
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
        self.channel_alert_id = 1227292887318925393
        self.last_gamestate = Gamestate.UNKNOWN
        self.init = False
        self.is_notification_available_sended = False
    
    def cog_unload(self):
        self.round_checker.cancel()

    def server_availability(self):
        if self.is_notification_available_sended:
            return
        logger.warning("Сервер выключен.")
        self.is_notification_available_sended = True

    def create_embed(self, responseData, current_time, current_gamestate):
        footer_text = "Сплетено пауком"
        footer_icon = "https://cdn.discordapp.com/attachments/593969947579777035/1248147974245056553/Lolth_Icon.png?ex=66629be2&is=66614a62&hm=4e8bb603b14859f7360070cd3c7b38e886eb776edcb9942c3a95f6f7d49a4014&"
        
        #round_id = responseData["roundid"][0]  # Получение ID раунда

        embed = discord.Embed()
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1243587366271189084/1246818328991764530/3xb0si6diyi91_copy.png?ex=665dc58e&is=665c740e&hm=263eb17e934939d411b04341df87f30483162ceb486bc7f5d904feb47c66b963&=&format=webp&quality=lossless")

        if current_gamestate == Gamestate.STARTUP:
            embed.title = f"Раунд"
            embed.color = discord.Color.orange()
            embed.add_field(name="Статус", value="Запуск сервера", inline=False)
        elif current_gamestate == Gamestate.LOBBY:
            embed.title = f"Раунд"
            embed.color = discord.Color.blue()
            embed.add_field(name="Статус", value="Лобби", inline=False)
        elif current_gamestate == Gamestate.INGAME:
            embed.title = f"Раунд"
            embed.color = discord.Color.dark_purple()
            embed.add_field(name="Статус", value="Идёт раунд", inline=False)
            embed.add_field(
                name="Количество игроков",
                value=responseData["players"][0] + " игрок(ов)",
            )
            embed.add_field(
                name="Время раунда",
                value=time.strftime("%H:%M", time.gmtime(current_time)),
            )
        elif current_gamestate == Gamestate.ENDGAME:
            embed.title = f"Раунд"
            embed.color = discord.Color.dark_magenta()
            embed.add_field(name="Статус", value="Окончание раунда", inline=False)
            embed.add_field(
                name="Раунд завершён",
                value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

        return embed

    
    
    def update_embed(self, embed, responseData, current_time, current_gamestate):
        embed.clear_fields()
        if current_gamestate == Gamestate.STARTUP:
            embed.title = f"Раунд"
            embed.color = discord.Color.orange()
            embed.add_field(name="Статус", value="Запуск сервера", inline=False)
        elif current_gamestate == Gamestate.LOBBY:
            embed.title = f"Раунд"
            embed.color = discord.Color.blue()
            embed.add_field(name="Статус", value="Лобби", inline=False)
        elif current_gamestate == Gamestate.INGAME:
            embed.title = f"Раунд"
            embed.color = discord.Color.green()
            embed.add_field(name="Статус", value="Идёт раунд", inline=False)
            embed.add_field(
                name="Количество игроков",
                value=responseData["players"][0] + " игрок(ов)",
            )
            embed.add_field(
                name="Время раунда",
                value=time.strftime("%H:%M", time.gmtime(current_time)),
            )
        elif current_gamestate == Gamestate.ENDGAME:
            embed.title = f"Раунд"
            embed.color = discord.Color.red()
            embed.add_field(name="Статус", value="Окончание раунда", inline=False)
            embed.add_field(
                name="Раунд завершён",
                value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

    @tasks.loop(seconds=60.0)
    async def round_checker(self):
        try:
            responseData = await ServerConnector(config.byond.host, config.byond.port).query_status()
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

        current_time = int(responseData["round_duration"][0])
        
        if int(responseData["gamestate"][0]) == 1 or int(responseData["gamestate"][0]) == 2:
            current_gamestate = Gamestate.LOBBY
        else:
            current_gamestate = Gamestate(int(responseData["gamestate"][0]))
        
        if not self.init or current_gamestate != self.last_gamestate:
            self.bot.custom_embed = self.create_embed(responseData, current_time, current_gamestate)
            if self.channel_alert is not None:
                if not self.init and current_gamestate != Gamestate.STARTUP:
                    self.bot.custom_embed_message = await self.channel_alert.send(embed=self.bot.custom_embed)
                    await self.bot.custom_embed_message.edit(embed=self.bot.custom_embed)
                elif current_gamestate == Gamestate.STARTUP and self.channel_alert is not None:
                    self.bot.custom_embed_message = await self.channel_alert.send(embed=self.bot.custom_embed)
                    await self.channel_alert.send(
                        f'<@&1227295722123296799> Новый раунд```byond://rockhill-game.ru:51143```'
                    )
                else:
                    await self.bot.custom_embed_message.edit(embed=self.bot.custom_embed)
        else:
            self.update_embed(self.bot.custom_embed, responseData, current_time, current_gamestate)
            if hasattr(self.bot, "custom_embed_message"):
                await self.bot.custom_embed_message.edit(embed=self.bot.custom_embed)

        self.last_gamestate = current_gamestate
        self.init = True

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel_alert = self.bot.get_channel(self.channel_alert_id)
        self.round_checker.start()


async def setup(bot):
    await bot.add_cog(Roundstatus(bot))
