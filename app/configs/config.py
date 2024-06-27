import yaml
import os
import aiofiles


_DEFAULT_CONFIG_PATH = "settings/config.yaml"
_DISCORD_CONFIG_PATH = "DISORD_CONFIG_PATH"


def _load() -> dict:
    path = os.getenv(_DISCORD_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
    with open(path) as config_file:
        return yaml.safe_load(config_file)


def _save(config: dict) -> None:
    path = os.getenv(_DISCORD_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
    with open(path, "w") as config_file:
        yaml.dump(config, config_file)


async def _async_load() -> dict:
    path = os.getenv(_DISCORD_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
    async with aiofiles.open(path, "r") as f:
        return yaml.safe_load(await f.read())


async def _async_save(config: dict) -> None:
    path = os.getenv(_DISCORD_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
    async with aiofiles.open(path, "w") as f:
        await f.write(yaml.dump(config))


def load_discord() -> dict:
    return _load()["discord"]


def load_module(module_name) -> dict:
    return _load()["modules"][module_name]


def save_module(module_name: str,  value: dict) -> None:
    config = _load()
    config["modules"][module_name] = value
    _save(config)


async def async_save_module(module_name: str, value: dict) -> None:
    config = await _async_load()
    config["modules"][module_name] = value
    await _async_save(config)


async def async_load_module(module_name: str) -> dict:
    return (await _async_load())["modules"][module_name]
