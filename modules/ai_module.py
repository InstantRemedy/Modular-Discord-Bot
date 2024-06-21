# modules/embed_module.py
from discord import Embed
from discord.ext import commands

#openai
from typing_extensions import override
from openai import OpenAI, AsyncOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread

import aiofiles
import os
import yaml


class OpenAIConfig:
    def __init__(self, 
                 api_key: str, 
                 org_id: str, 
                 project_id: str,
                 assistant_id: str,
                 thread_id: str = ""):
        self._api_key = api_key
        self._org_id = org_id
        self._project_id = project_id
        self._assistant_id = assistant_id
        self._thread_id = thread_id
        
    @property
    def api_key(self) -> str:
        return self._api_key
    
    @property
    def org_id(self) -> str:
        return self._org_id
    
    @property
    def project_id(self) -> str:
        return self._project_id
    
    @property
    def assistant_id(self) -> str:
        return self._assistant_id
    
    @property
    def thread_id(self) -> str:
        return self._thread_id
    
    def __str__(self) -> str:
        output = "OpenAI Config("
        output += f"api_key={self.api_key}, "
        output += f"org_id={self.org_id}, "
        output += f"project_id={self.project_id}, "
        output += f"assistant_id={self.assistant_id}, "
        output += f"thread_id={self.thread_id})"
        return output


class OpenAIHandler:
    def __init__(self) -> None:
        config: OpenAIConfig = self._load_openai_config()
        self._async_client: AsyncOpenAI = self._create_async_client(config=config) # Use when prompting
        self._sync_client: OpenAI = self._create_sync_client(config=config) # Use when initialization
        self._assistant: Assistant = self._get_assistant(assistant_id=config.assistant_id)
        self._thread: Thread = self._get_thread(thread_id=config.thread_id)
    
    def _load_openai_config(self) -> OpenAIConfig:
        config_path = os.getenv("DISORD_CONFIG_PATH", "./settings/config.yaml")
        
        with open(config_path) as config_file:
            config = yaml.safe_load(config_file)
        
        if not config.get("openai").get("thread_id"):
            config["openai"]["thread_id"] = ""
        
        return OpenAIConfig(
            api_key=config["openai"]["api_key"],
            org_id=config["openai"]["org_id"],
            project_id=config["openai"]["project_id"],
            assistant_id=config["openai"]["assistant_id"],
            thread_id=config["openai"]["thread_id"]
        )
        
    def _create_async_client(self, config: OpenAIConfig) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=config.api_key,
            project=config.project_id,
            organization=config.org_id,
        )
        
    def _create_sync_client(self, config: OpenAIConfig) -> OpenAI:
        return OpenAI(
            api_key=config.api_key,
            project=config.project_id,
            organization=config.org_id,
        )
        
    def _get_assistant(self, assistant_id: str) -> Assistant:
        return self._sync_client.beta.assistants.retrieve(assistant_id=assistant_id)
    
    def _get_thread(self, thread_id: str) -> Thread:
        if thread_id != "" and thread_id is not None:
            return self._sync_client.beta.threads.retrieve(thread_id=thread_id)
        
        # if thread_id is not provided, create a new thread and save it to the config file
        thread = self._sync_client.beta.threads.create()
        config_path = os.getenv("DISORD_CONFIG_PATH", "./settings/config.yaml")
        
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)
        
        config["openai"]["thread_id"] = thread.id
        with open(config_path, "w") as config_file:
            yaml.dump(config, config_file)
    
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
            assistant_id=self._assistant.id
        )
        
        messages = await self._async_client.beta.threads.messages.list(
            thread_id=self._thread.id
        )
                
        return messages.data[0].content[0].text.value
    
    async def renew_thread(self):
        await self._async_client.beta.threads.delete(thread_id=self._thread.id)
        self._thread = await self._async_client.beta.threads.create()
        config_path = os.getenv("DISORD_CONFIG_PATH", "./settings/config.yaml")
        
        async with aiofiles.open(config_path, "r") as config_file:
            content = await config_file.read()
            config = yaml.safe_load(content)
        
        config["openai"]["thread_id"] = self._thread.id
        async with aiofiles.open(config_path, "w") as config_file:
            yaml_data = yaml.safe_dump(config)
            await config_file.write(yaml_data)
    
    @property
    def assistant_name(self) -> str:
        return self._assistant.name
    
    @property
    def assistant_id(self) -> str:
        return self._assistant.id
    
    @property
    def thread_id(self) -> str:
        return self._thread.id
    
    
class Ai_module(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "I'm AI module!"
        self._ai_handler = OpenAIHandler()
        
    @commands.command(name="mind")
    async def promt(self, ctx, *, promt_message: str = ""):
        if not promt_message:
            embed = Embed(
                title=f"{self._ai_handler.assistant_name}",
                description=f"Привет! я {self._ai_handler.assistant_name}. Чего бы {ctx.author.display_name} хотел знать?",
            )
        else:
            await ctx.reply("Думаю...")
            
            response = await self._ai_handler.get_reponse_message(ctx.author.display_name, promt_message)
            embed = Embed(
                title=f"{self._ai_handler.assistant_name}", 
                description=response,
            )
            
        await ctx.reply(
            embed=embed, 
            mention_author=True
        )
    
    @commands.command(name="renew_thread")
    async def renew_thread(self, ctx):
        await self._ai_handler.renew_thread()
        await ctx.reply("Тень ума, что скрыться хочет.")
        
        
    @commands.command(name="help_ai")
    async def help_ai(self, ctx):
        help = Embed(
            title= self._ai_handler.assistant_name,
            description=f"Я {self._ai_handler.assistant_name}, спутник мыслей, что не виден",
            color=0x00ff00
        )    
        help.add_field(
            name="mind",
            value=f"Расскажу тебе, {ctx.author.display_name}, о странствиях моего разума.",
            inline=False
        )
        
        help.add_field(
            name="renew_thread",
            value="Тень ума, что скрыться хочет.",
            inline=False
        )
        
        await ctx.reply(embed=help)

async def setup(bot):
    await bot.add_cog(Ai_module(bot))
