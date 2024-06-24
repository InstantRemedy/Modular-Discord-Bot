from datetime import datetime
from colorama import Fore, Style, init
from pathlib import Path

import logging
import asyncio
import aiofiles


if not Path('logs').exists():
    Path('logs').mkdir()

if not Path('logs/actions.log').exists():
    with open('logs/actions.log', 'w') as f:
        pass

# Инициализация colorama
init(autoreset=True)

# Форматер для логов в консоль
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

# Форматер для логов в файл
class FileFormatter(logging.Formatter):
    def format(self, record):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{current_time}][{record.levelname}][{record.name}] => {record.getMessage()}'
        return log_message

# Асинхронный хендлер для записи логов в файл
class AsyncFileHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    async def _write_log(self, log_entry):
        async with aiofiles.open(self.filename, mode='a', encoding="utf-8") as file:
            await file.write(log_entry + '\n')

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.create_task(self._write_log(log_entry))

# Функция для настройки логгера
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Создаем и настраиваем хендлеры
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())

    async_file_handler = AsyncFileHandler(f'logs/actions.log')
    async_file_handler.setFormatter(FileFormatter())

    # Добавляем хендлеры к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(async_file_handler)

    return logger