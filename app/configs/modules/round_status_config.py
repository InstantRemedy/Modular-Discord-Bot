from configs import config


class RoundStatusConfig:
    def __init__(self):
        self._host: str = str()
        self._port: int = int()
        self._channel: int = int()
        self._main_role: int = int()
        self._allowed_roles: list[int] = list()
        self._load()

    def _load(self):
        cfg = config.load_module("round_status")
        self._host = cfg.get("host")
        self._port = cfg.get("port")
        self._channel = cfg.get("channel")
        self._main_role = cfg.get("main_role")
        self._allowed_roles = cfg.get("allowed_roles")
        self._isLoaded = True

    def _save(self):
        config.save_module("round_status", {
            "host": self._host,
            "port": self._port,
            "channel": self._channel,
            "main_role": self._main_role,
            "allowed_roles": self._allowed_roles
        })

    async def _async_save(self):
        await config.async_save_module("round_status", {
            "host": self._host,
            "port": self._port,
            "channel": self._channel,
            "main_role": self._main_role,
            "allowed_roles": self._allowed_roles
        })

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def channel(self) -> int:
        return self._channel

    @property
    def main_role(self) -> int:
        return self._main_role

    @property
    def allowed_roles(self) -> list[int]:
        return self._allowed_roles

    async def async_set_host(self, value: str):
        self._host = value
        await self._async_save()

    async def async_set_port(self, value: int):
        self._port = value
        await self._async_save()

    async def async_add_role(self, value: int):
        self._allowed_roles.append(value)
        await self._async_save()

    async def async_remove_role(self, value: int):
        self._allowed_roles.remove(value)
        await self._async_save()
