import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def setup_env() -> None:
    load_dotenv(ENV_FILE)


def get_openai_api_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key or not key.strip():
        return None
    return key.strip()


def log_openai_key_status() -> bool:
    """
    Пишет в лог, есть ли OPENAI_API_KEY после load_dotenv.
    Возвращает True, если ключ найден.
    """
    if get_openai_api_key():
        logger.info("OPENAI_API_KEY найден в окружении")
        return True

    if ENV_FILE.is_file():
        logger.warning(
            "OPENAI_API_KEY не задан: в файле %s нет переменной или она пустая",
            ENV_FILE,
        )
    else:
        logger.warning(
            "OPENAI_API_KEY не задан: файл %s не найден, задайте переменную в окружении",
            ENV_FILE,
        )
    return False
