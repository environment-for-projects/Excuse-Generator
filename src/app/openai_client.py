from openai import OpenAI

from app.config import get_openai_api_key, logger

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _client

    if _client is not None:
        return _client

    api_key = get_openai_api_key()
    if not api_key:
        logger.error(
            "Нельзя вызвать OpenAI: OPENAI_API_KEY отсутствует в окружении"
        )
        raise RuntimeError(
            "OPENAI_API_KEY не задан. Добавьте ключ в .env или экспортируйте переменную."
        )

    _client = OpenAI(api_key=api_key)
    return _client
