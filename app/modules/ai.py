from discord.ext import commands
from openai import OpenAI, AsyncOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread
from configs.modules import AIConfig

import enum
import discord
import asyncio
import loggers
import uuid

logger = loggers.setup_logger("ai")
ai_config = AIConfig()


def check_roles(ctx: commands.Context):
    if any(role.id == ai_config.main_role for role in ctx.author.roles):
        return True
    if any(role.id in ai_config.allowed_roles for role in ctx.author.roles):
        return True

    raise commands.CheckFailure(
        f"User '{ctx.author.display_name}' don't have access to the 'AI' module.")


def check_main_role(ctx: commands.Context):
    if any(role.id == ai_config.main_role for role in ctx.author.roles):
        return True

    raise commands.CheckFailure(
        f"User '{ctx.author.display_name}' don't have access to the 'AI' module.")


class OpenAIHandler:
    def __init__(self) -> None:
        self.__async_client: AsyncOpenAI = self._create_async_client()  # Use when prompting
        self.__sync_client: OpenAI = self._create_sync_client()  # Use when initialization
        self.__assistant: Assistant = self._get_assistant()
        self.__thread: Thread = self._get_thread()  # OpenAI thread

    def _create_async_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=ai_config.api_key,
            project=ai_config.project_id,
            organization=ai_config.org_id,
        )

    def _create_sync_client(self) -> OpenAI:
        return OpenAI(
            api_key=ai_config.api_key,
            project=ai_config.project_id,
            organization=ai_config.org_id,
        )

    def _get_assistant(self) -> Assistant:
        return self.__sync_client.beta.assistants.retrieve(assistant_id=ai_config.assistant_id)

    def _get_thread(self) -> Thread:
        if ai_config.thread_id:
            return self.__sync_client.beta.threads.retrieve(thread_id=ai_config.thread_id)

        # if thread_id is not provided, create a new thread and save it to the config file
        thread = self.__sync_client.beta.threads.create()
        ai_config.thread_id = thread.id

    def _get_formatted_response(self, user_name: str, promt_message: str) -> str:
        return f"{user_name}:\"{promt_message}\""

    async def get_reponse_message(self, user_name: str, promt_message: str):
        promt_message = self._get_formatted_response(user_name, promt_message)
        await self.__async_client.beta.threads.messages.create(
            thread_id=self.__thread.id,
            role="user",
            content=promt_message
        )

        await self.__async_client.beta.threads.runs.create_and_poll(
            thread_id=self.__thread.id,
            assistant_id=self.__assistant.id,
            timeout=15
        )

        messages = await self.__async_client.beta.threads.messages.list(
            thread_id=self.__thread.id
        )

        response_message = messages.data[0].content[0].text.value
        if response_message == promt_message:
            return "Простите, но я не могу ответить на ваш вопрос. Попробуйте позже"

        return response_message

    async def new_thread(self):
        await self.__async_client.beta.threads.delete(thread_id=self.__thread.id)
        self.__thread = await self.__async_client.beta.threads.create()
        await ai_config.async_set_thread_id(self.__thread.id)

    @property
    def assistant_name(self) -> str:
        return self.__assistant.name

    @property
    def assistant_id(self) -> str:
        return self.__assistant.id

    @property
    def thread_id(self) -> str:
        return self.__thread.id


class Status(enum.Enum):
    OFF = "Дремлет"
    READY = "Плетёт интриги"


class Request:
    def __init__(self, uuid_str: str, ctx: commands.Context, prompt_message: str) -> None:
        self.__uuid_str = uuid_str
        self.__ctx = ctx
        self.__prompt_message = prompt_message

    @property
    def uuid_str(self) -> str:
        return self.__uuid_str

    @property
    def ctx(self) -> commands.Context:
        return self.__ctx

    @property
    def prompt_message(self) -> str:
        return self.__prompt_message


class Ai(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.__bot = bot
        self.__ai_handler = OpenAIHandler()
        self.__is_switched_on = False
        self.__is_active = False
        self.__queue: asyncio.Queue[Request] = asyncio.Queue()
        self.__max_requests = 10
        self.__current_requests = 0
        self.__lock = asyncio.Lock()

    @commands.command(name="mind")
    async def prompt(self, ctx: commands.Context, *, prompt_message: str = ""):
        if not self.__is_switched_on:
            await ctx.reply(
                "Увы, мои силы иссякли, и мне нужно время на восстановление. "
                "Скоро я буду готова к новой беседе.")
            logger.warning(
                f"{ctx.author.display_name} tried to use the AI module, but it is turned off.")
            return
        if self.__current_requests >= self.__max_requests:
            logger.warning(
                f"{ctx.author.display_name} tried to use the AI module, "
                "but the max number of requests is reached.")
            await ctx.reply(
                "Увы, мои силы иссякли, и мне нужно время на восстановление. "
                "Скоро я буду готова к новой беседе.")
            return

        self.__current_requests += 1
        if not prompt_message:
            logger.info(
                f"'{ctx.author.display_name}' => requested an empty prompt message.")
            async with ctx.typing():
                await ctx.reply(
                    f"Привет! я {self.__ai_handler.assistant_name}. Чего бы {ctx.author.display_name} хотел знать?")
                return

        uuid_str = str(uuid.uuid4())
        await self.__queue.put(Request(uuid_str, ctx, prompt_message))
        logger.info(
            f"[{uuid_str}][{ctx.author.display_name}] "
            f"=> added a message to the queue. Prompt: {prompt_message}")
        await self._process_queue()

    async def _process_queue(self):
        async with self.__lock:
            if self.__is_active:
                return
            self.__is_active = True
            while not self.__queue.empty():
                request = await self.__queue.get()
                try:
                    await self._process_request(request)
                except Exception as ex:
                    logger.error(
                        f"[{request.uuid_str}][{request.ctx.author.display_name}] "
                        f"=> error: {ex}")
                    await request.ctx.reply(
                        "Простите, но я не могу ответить на ваш вопрос. "
                        "Попробуйте позже")

                self.__queue.task_done()

            logger.info(f"Queue is empty.")
            self.__is_active = False
            if self.__current_requests >= self.__max_requests:
                await self._change_status(Status.OFF)

    async def _process_request(self, request: Request):
        current_prompt_message = request.prompt_message
        logger.info(
            f"[{request.uuid_str}][{request.ctx.author.display_name}] "
            f"=> is handling a message from the queue. "
            f"Prompt: {current_prompt_message}")
        async with request.ctx.typing():
            response = await self.__ai_handler.get_reponse_message(
                request.ctx.author.display_name, current_prompt_message)
            await request.ctx.reply(response)
        logger.info(
            f"[{request.uuid_str}][{request.ctx.author.display_name}] "
            f"=> response: {response}")

    @commands.command(name="ai_new_thread")
    @commands.check(check_roles)
    async def new_thread(self, ctx: commands.Context):
        await self.__ai_handler.new_thread()
        logger.info(
            f"'{ctx.author.display_name}' => created a new thread.")
        await ctx.reply("AI created new thread")

    @commands.check(check_roles)
    @commands.command(name="ai_switch_on")
    async def switch_on(self, ctx):
        self.__is_switched_on = True
        logger.info(
            f"'{ctx.author.display_name}' => turned on the AI module.")
        await ctx.reply("AI switched on")
        if self.__current_requests < self.__max_requests:
            await self._change_status(Status.READY)

    @commands.check(check_roles)
    @commands.command(name="ai_switch_off")
    async def switch_off(self, ctx):
        self.__is_switched_on = False
        logger.info(
            f"'{ctx.author.display_name}' => turned off the AI module.")
        await ctx.reply("AI swtched off")
        await self._change_status(Status.OFF)

    @commands.check(check_roles)
    @commands.command(name="ai_max_requests")
    async def set_max_requests(self, ctx: commands.Context, max_requests: int):
        if max_requests <= 0:
            raise commands.BadArgument(f"The number of requests must be greater than 1.")
        self.__current_requests = 0
        self.__max_requests = max_requests
        logger.info(
            f"'{ctx.author.display_name}' => set the max number of requests to {max_requests}.")
        await self._change_status(Status.READY)
        await ctx.reply(f"AI set max requests: {max_requests}")

    @commands.check(check_roles)
    @commands.command(name="ai_reset_requests")
    async def reset_requests(self, ctx: commands.Context):
        self.__current_requests = 0
        logger.info(f"'{ctx.author.display_name}' => reset the number of requests.")
        await self._change_status(Status.READY)
        await ctx.reply("AI reset request counter")

    @commands.check(check_main_role)
    @commands.command(name="ai_add_role")
    async def add_role(self, ctx: commands.Context, role: int):
        await ai_config.async_add_role(role)
        await ctx.reply(f"AI role {role} added")

    @commands.check(check_main_role)
    @commands.command(name="ai_remove_role")
    async def remove_role(self, ctx: commands.Context, role: int):
        await ai_config.async_remove_role(role)
        await ctx.reply(f"AI role {role} was removed")

    async def _change_status(self, status: Status):
        await self.__bot.change_presence(activity=discord.CustomActivity(name=status.value))
        logger.info(f"Status was changed to {status.value}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self._change_status(Status.OFF)
        logger.info("AI module is ready.")


async def setup(bot):
    await bot.add_cog(Ai(bot))
