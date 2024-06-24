import yaml
import os
import aiofiles
import async_property

_DEFAULT_CONFIG_PATH = "settings/config.yaml"
_DISCORD_CONFIG_PATH = "DISORD_CONFIG_PATH"


def _load() -> dict:
    path = os.getenv(_DISCORD_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
    
    with open(path) as config_file:
        return yaml.safe_load(config_file)
    

def _save(key: str, value) -> None:
    global _config
    path = os.getenv(_DISCORD_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
    
    config = _load()
    
    config[key] = value
    
    with open(path, "w") as config_file:
        yaml.dump(config, config_file)

async def _async_save(key: str, value) -> None:
    path = os.getenv(_DISCORD_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
    
    async with aiofiles.open(path, "r") as f:
        config = yaml.safe_load(await f.read())
        config[key] = value
    
    async with aiofiles.open(path, "w") as f:
        await f.write(yaml.dump(config)) 


class OpenAIConfig:
    def __init__(self):
        self._api_key: str
        self._assistant_id: str
        self._org_id: str | None
        self._project_id: str | None
        self._thread_id: str | None
        self._isLoaded: bool = False
        self._load()
    
    def _load(self):
        config = _load()
        self._org_id = config["openai"].get("org_id")
        self._project_id = config["openai"].get("project_id")
        self._thread_id = config["openai"].get("thread_id")
        self._api_key = config["openai"].get("api_key")
        self._assistant_id = config["openai"]["assistant_id"]
        self._isLoaded = True
    
    def _save(self):
        _save("openai", {
            "api_key": self._api_key,
            "org_id": self._org_id,
            "project_id": self._project_id,
            "assistant_id": self._assistant_id,
            "thread_id": self._thread_id
        })
        
    async def _async_save(self):
        await _async_save("openai", {
            "api_key": self._api_key,
            "org_id": self._org_id,
            "project_id": self._project_id,
            "assistant_id": self._assistant_id,
            "thread_id": self._thread_id
        })
    
    @property
    def api_key(self) -> str:
        if not self._isLoaded:
            self._load()
        
        return self._api_key
    
    @property
    def org_id(self) -> str | None:
        if not self._isLoaded:
            self._load()
        
        return self._org_id
    
    @property
    def project_id(self) -> str | None:
        if not self._isLoaded:
            self._load()
        
        return self._project_id
    
    @property
    def assistant_id(self) -> str | None:
        if not self._isLoaded:
            self._load()
        
        return self._assistant_id
    
    @property
    def thread_id(self) -> str | None:
        if not self._isLoaded:
            self._load()
        
        return self._thread_id
    
    @thread_id.setter
    def thread_id(self, value: str) -> None:
        self._thread_id = value
        self._save()

    async def async_set_thread_id(self, value: str) -> None:
        self._thread_id = value
        await self._async_save()
    

class ByondConfig:
    def __init__(self):
        self._host: str
        self._port: int
        self._isLoaded = False
        self._load()
        
    def _load(self):
        config = _load()
        self._host = config["byond"].get("host")
        self._port = config["byond"].get("port")
        self._isLoaded = True
        
    def _save(self):
        _save("byond", {
            "host": self._host,
            "port": self._port
        })
        
    async def _async_save(self):
        await _async_save("byond", {
            "host": self._host,
            "port": self._port
        })
        
    @property
    def host(self) -> str:
        if not self._isLoaded:
            self._load()
        
        return self._host
    
    @property
    def port(self) -> str:
        if not self._isLoaded:
            self._load()
        
        return self._port
    
    @host.setter
    def host(self, value: str):
        self._host = value
        self._save()
        
    @port.setter
    def port(self, value: str):
        self._port = value
        self._save()
        
    async def async_set_host(self, value: str):
        self._host = value
        await self._async_save()
        
    async def async_set_port(self, value: str):
        self._port = value
        await self._async_save()


class DiscordConfig:
    def __init__(self):
        self._load()
        self._token: str
        self._bot_prefix: str
        self._case_insensitive: bool
        self._isLoaded: bool = False
             
    def _load(self):
        config = _load()
        self._token = config["discord"].get("token")
        self._bot_prefix = config["discord"].get("bot_prefix")
        self._case_insensitive = config["discord"].get("case_insensitive")
        if self._case_insensitive is None:
            self._case_insensitive = True
        self._isLoaded = True
        
    @property
    def token(self) -> str:
        if not self._isLoaded:
            self._load()
        
        return self._token
    
    @property
    def bot_prefix(self) -> str:
        if not self._isLoaded:
            self._load()
        
        return self._bot_prefix
    
    @property
    def case_insensitive(self) -> bool:
        if not self._isLoaded:
            self._load()
        
        return self._case_insensitive


discord = DiscordConfig()
byond = ByondConfig()
openai = OpenAIConfig()
