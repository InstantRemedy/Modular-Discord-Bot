from datetime import datetime
from colorama import Fore, Style, init
from pathlib import Path

import logging
import asyncio
import aiofiles


init(autoreset=True)


class ColorFormatter(logging.Formatter):
    def format(self, record):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level_color = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.BLUE,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT,
        }.get(record.levelno, Fore.RESET)
        
        log_message = f'{level_color}[{current_time}][{record.levelname}][{record.name}] => {record.getMessage()}{Style.RESET_ALL}'
        return log_message


class FileFormatter(logging.Formatter):
    def format(self, record):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{current_time}][{record.levelname}][{record.name}] => {record.getMessage()}'
        return log_message


class AsyncFileHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

        if not Path('logs').exists():
            Path('logs').mkdir()

        if not Path(f'logs/{self.filename}.log').exists():
            with open(f'logs/{self.filename}.log', 'w') as f:
                pass

    async def _write_log(self, log_entry):
        async with aiofiles.open(f'logs/{self.filename}.log', mode='a', encoding="utf-8") as file:
            await file.write(log_entry + '\n')

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.create_task(self._write_log(log_entry))


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())

    async_file_handler = AsyncFileHandler(name)
    async_file_handler.setFormatter(FileFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(async_file_handler)

    return logger
