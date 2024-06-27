from configs import config


class AIConfig:
    def __init__(self):
        self._api_key: str = str()
        self._assistant_id: str = str()
        self._org_id: str | None = None
        self._project_id: str | None = None
        self._thread_id: str | None = None
        self._allowed_roles: list[int] = []
        self._main_role: int
        self._load()

    def _load(self):
        cfg = config.load_module("ai")
        self._org_id = cfg.get("org_id")
        self._project_id = cfg.get("project_id")
        self._thread_id = cfg.get("thread_id")
        self._api_key = cfg.get("api_key")
        self._assistant_id = cfg.get("assistant_id")
        self._allowed_roles = cfg.get("allowed_roles")
        self._main_role = cfg.get("main_role")
        self._isLoaded = True

    def _save(self):
        config.save_module("ai", {
            "api_key": self._api_key,
            "org_id": self._org_id,
            "project_id": self._project_id,
            "assistant_id": self._assistant_id,
            "thread_id": self._thread_id,
            "allowed_roles": self._allowed_roles,
            "main_role": self._main_role
        })

    async def _async_save(self):
        await config.async_save_module("ai", {
            "api_key": self._api_key,
            "org_id": self._org_id,
            "project_id": self._project_id,
            "assistant_id": self._assistant_id,
            "thread_id": self._thread_id,
            "allowed_roles": self._allowed_roles,
            "main_role": self._main_role
        })

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def org_id(self) -> str | None:
        return self._org_id

    @property
    def project_id(self) -> str | None:
        return self._project_id

    @property
    def assistant_id(self) -> str | None:
        return self._assistant_id

    @property
    def thread_id(self) -> str | None:
        return self._thread_id

    @thread_id.setter
    def thread_id(self, value: str) -> None:
        self._thread_id = value
        self._save()

    @property
    def allowed_roles(self) -> list[int]:
        return self._allowed_roles

    @property
    def main_role(self) -> int:
        return self._main_role

    async def async_set_thread_id(self, value: str) -> None:
        self._thread_id = value
        await self._async_save()

    async def async_set_roles(self, value: list[int]) -> None:
        self._allowed_roles = value
        await self._async_save()

    async def async_add_role(self, value: int) -> None:
        self._allowed_roles.append(value)
        await self._async_save()

    async def async_remove_role(self, value: int) -> None:
        self._allowed_roles.remove(value)
        await self._async_save()
