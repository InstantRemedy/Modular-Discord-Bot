# modules/embed_module.py
from discord.ext import commands
from loggers import logger, action_logger
from collections import deque

#openai
from openai import OpenAI, AsyncOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread

import config
import uuid


ALLOWED_ROLE_IDS = [
    1227291822917816402
]

def info(message):
    logger.info(f"[AI MODULE] => {message}")
    action_logger.info(f"[AI MODULE] => {message}")

def warning(message):
    logger.warning(f"[AI MODULE] => {message}")
    action_logger.warning(f"[AI MODULE] => {message}")
    
def error(message):
    logger.error(f"[AI MODULE] => {message}")
    action_logger.error(f"[AI MODULE] => {message}")


def check_roles(ctx):
    if any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        return True
    
    raise commands.CheckFailure(f"User '{ctx.author.display_name}' don't have access to the 'AI' module.")

class OpenAIHandler:
    def __init__(self) -> None:
        self._async_client: AsyncOpenAI = self._create_async_client() # Use when prompting
        self._sync_client: OpenAI = self._create_sync_client() # Use when initialization
        self._assistant: Assistant = self._get_assistant()
        self._thread: Thread = self._get_thread()
    
    def _create_async_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=config.openai.api_key,
            project=config.openai.project_id,
            organization=config.openai.org_id,
        )
        
    def _create_sync_client(self) -> OpenAI:
        return OpenAI(
            api_key=config.openai.api_key,
            project=config.openai.project_id,
            organization=config.openai.org_id,
        )
        
    def _get_assistant(self) -> Assistant:
        return self._sync_client.beta.assistants.retrieve(assistant_id=config.openai.assistant_id)
    
    def _get_thread(self) -> Thread:
        if config.openai.thread_id:
            return self._sync_client.beta.threads.retrieve(thread_id=config.openai.thread_id)
        
        # if thread_id is not provided, create a new thread and save it to the config file
        thread = self._sync_client.beta.threads.create()
        config.openai.thread_id = thread.id
    
    def _get_formatted_response(self, user_name: str, promt_message: str) -> str:
        return f"{user_name}:\"{promt_message}\""
        
        
    async def get_reponse_message(self, user_name: str, promt_message: str):
        promt_message = self._get_formatted_response(user_name, promt_message)
        await self._async_client.beta.threads.messages.create(
            thread_id=self._thread.id,
            role="user",
            content=promt_message
        )
        
        await self._async_client.beta.threads.runs.create_and_poll(
            thread_id=self._thread.id,
            assistant_id=self._assistant.id,
        )
        
        messages = await self._async_client.beta.threads.messages.list(
            thread_id=self._thread.id
        )
                
        return messages.data[0].content[0].text.value
    
    async def new_thread(self):
        await self._async_client.beta.threads.delete(thread_id=self._thread.id)
        self._thread = await self._async_client.beta.threads.create()
        await config.openai.async_set_thread_id(self._thread.id)
    
    @property
    def assistant_name(self) -> str:
        return self._assistant.name
    
    @property
    def assistant_id(self) -> str:
        return self._assistant.id
    
    @property
    def thread_id(self) -> str:
        return self._thread.id
    
    
class Ai(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "I'm AI module!"
        self._ai_handler = OpenAIHandler()
        self._is_switched_on = False
        self._is_active = False # check if the llm is handling a request
        self._deque: deque[dict] = deque() # deque for messages
        self._max_requests = 10 # max number of requests that can be handled at the same time
        self._current_requests = 0
        
    @commands.command(name="mind")
    async def promt(self, ctx, *, promt_message: str = ""):
        if not self._is_switched_on:
            warning(f"{ctx.author.display_name} tried to use the AI module, but it is turned off.")
            return
        if self._current_requests >= self._max_requests:
            warning(f"{ctx.author.display_name} tried to use the AI module, but the max number of requests is reached.")
            return
        
        self._current_requests += 1
        if not promt_message:
            info(f"{ctx.author.display_name} requested a empty promt message.")
            response = f"Привет! я {self._ai_handler.assistant_name}. Чего бы {ctx.author.display_name} хотел знать?"
        else:
            uuid_str = str(uuid.uuid4())
            self._deque.append({"uuid": uuid_str, "ctx": ctx, "promt_message": promt_message})
            info(f"UUID:{uuid_str} => {ctx.author.display_name} added a message to the deque. Promt: {promt_message}")
            if self._is_active:
                return
            
            # handle all messages in the deque. 
            while len(self._deque) > 0: 
                self._is_active = True
                request = self._deque.popleft()
                current_promt_message = request["promt_message"]
                current_ctx = request["ctx"]
                uuid_str = request["uuid"]
                info(f"UUID: {uuid_str} => {current_ctx.author.display_name} is handling a message from the deque. Promt: {promt_message}")
                async with ctx.typing():
                    try:
                        response = await self._ai_handler.get_reponse_message(current_ctx.author.display_name, current_promt_message)
                    except Exception as ex:
                        logger.error(f"An error occurred while handling a message from the deque. Error: {ex}")
                        await current_ctx.reply("Простите, но я не могу ответить на ваш вопрос. Попробуйте позже")
                        continue
                    
                    await current_ctx.reply(response)
                info(f"Response: {response}")

            
            info("All messages from the deque are handled.")
            self._is_active = False
        
    @commands.command(name="ai_new_thread")
    @commands.check(check_roles)
    async def new_thread(self, ctx):
        await self._ai_handler.new_thread() 
        info(f"User '{ctx.author.display_name}' created a new thread.")
        await ctx.reply("Тень ума, что скрыться хочет.")
    
    @commands.check(check_roles)
    @commands.command(name="ai_help")
    async def help_ai(self, ctx):
        help = f"Я {self._ai_handler.assistant_name}, спутник мыслей, что не виден\n\n" \
                f"mind - Расскажу тебе, {ctx.author.display_name}, о странствиях моего разума.\n" \
                f"renew_thread - Тень ума, что скрыться хочет.\n" \
                f"ai_switch_on - Позволю тебе услышать мои мысли.\n" \
                f"ai_switch_off - Скрою свои мысли от тебя."

        info(f"User '{ctx.author.display_name}' requested help from the AI module.")
        await ctx.author.reply(help)

    @commands.check(check_roles)
    @commands.command(name="ai_switch_on")
    async def switch_on(self, ctx):
        self._is_switched_on = True
        info(f"User '{ctx.author.display_name}' turned on the AI module.")
        await ctx.reply("Позволь мне рассказать тебе о моих мыслях.")

    @commands.check(check_roles)
    @commands.command(name="ai_switch_off")
    async def switch_off(self, ctx):
        self._is_switched_on = False
        info(f"User '{ctx.author.display_name}' turned off the AI module.")
        await ctx.reply("Скрою свои мысли от тебя.")

    @commands.check(check_roles)
    @commands.command(name="ai_max_requests")
    async def set_max_requests(self, ctx, max_requests: int):
        uuid_str = str(uuid.uuid4())
        info(f"UUID: {uuid_str} => User '{ctx.author.display_name}' tried to set the max number of requests to {max_requests}.")
        if max_requests <= 0:
            raise commands.BadArgument(f"UUID: {uuid_str} => The number of requests must be greater than 1.")
        self._current_requests = 0
        self._max_requests = max_requests
        info(f"UUID: {uuid_str} => User '{ctx.author.display_name}' set the max number of requests to {max_requests}.")

    @commands.check(check_roles)
    @commands.command(name="ai_reset_requests")
    async def reset_requests(self, ctx):
        self._current_requests = 0
        info(f"User '{ctx.author.display_name}' reset the number of requests.")
    
async def setup(bot):
    await bot.add_cog(Ai(bot))
