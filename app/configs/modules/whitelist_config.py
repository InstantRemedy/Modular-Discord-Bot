from configs import config


class WhitelistConfig:
    def __init__(self):
        self._main_role: int = int()
        self._allowed_roles: list[int] = list()
        self._load()

    def _load(self):
        data = config.load_module("whitelist")
        self._main_role = data.get("main_role", 0)
        self._allowed_roles = data.get("allowed_roles", [])

    def _save(self):
        config.save_module("whitelist", {
            "main_role": self._main_role,
            "allowed_roles": self._allowed_roles
        })

    async def _async_save(self):
        await config.async_save_module("whitelist", {
            "main_role": self._main_role,
            "allowed_roles": self._allowed_roles
        })

    @property
    def main_role(self) -> int:
        return self._main_role

    @property
    def allowed_roles(self) -> list[int]:
        return self._allowed_roles

    def add_role(self, role: int):
        self._allowed_roles.append(role)
        self._save()

    def remove_role(self, role: int):
        self._allowed_roles.remove(role)
        self._save()

    async def async_add_role(self, role: int):
        self._allowed_roles.append(role)
        await self._async_save()

    async def async_remove_role(self, role: int):
        self._allowed_roles.remove(role)
        await self._async_save()
