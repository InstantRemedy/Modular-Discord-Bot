from configs import config


class DiscordConfig:
    def __init__(self):
        self._token: str = str()
        self._bot_prefix: str = str()
        self._case_insensitive: bool = bool()
        self._load()

    def _load(self):
        cfg = config.load_discord()
        self._token = cfg.get("token")
        self._bot_prefix = cfg.get("bot_prefix")
        self._case_insensitive = cfg.get("case_insensitive")
        if self._case_insensitive is None:
            self._case_insensitive = True
        self._isLoaded = True

    @property
    def token(self) -> str:
        return self._token

    @property
    def bot_prefix(self) -> str:
        return self._bot_prefix

    @property
    def case_insensitive(self) -> bool:
        return self._case_insensitive
