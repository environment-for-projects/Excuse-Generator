import logging

from app.openai_client import get_openai_client
from app.schemas import ExcuseDraft, ExcuseRequest

logger = logging.getLogger(__name__)


class ExcuseGenerator:
    """
    Сервис первого LLM-вызова - Excuse Generator.
    Генерирует текст отмазки. Использует более лёгкую модель,
    потому что здесь важнее скорость и креативность, а не строгая оценка.
    """

    def generate(self, request: ExcuseRequest) -> ExcuseDraft:
        response = get_openai_client().responses.create(
            model="gpt-4o",
            instructions=self._build_system_prompt(),
            input=self._build_user_prompt(request),
            temperature=0.75,
            max_output_tokens=220,
        )

        excuse_text = response.output_text.strip()

        if not excuse_text:
            logger.warning("Excuse generator returned empty text")
            excuse_text = "Извини, я задержался из-за непредвиденной ситуации. Постараюсь быстро всё исправить."

        return ExcuseDraft(excuse=excuse_text)

    def _build_system_prompt(self) -> str:
        return """
Ты генератор убедительных, но не чрезмерно драматичных отмазок.

Твоя задача — сгенерировать одну короткую отмазку на русском языке.

Правила:
- Пиши естественно, как сообщение реальному человеку.
- Используй только данные пользователя: категорию, причину и контекст.
- Если контекст не указан, не выдумывай статус, возраст, работу, учёбу или личные обстоятельства пользователя.
- Не добавляй факты, которых нет в причине или контексте.
- Не добавляй экстремальные события, если их не было в причине.
- Не придумывай тяжёлые болезни, аварии, смерть родственников и другие драматичные обстоятельства.
- Не используй театральный или слишком официальный стиль.
- Отмазка должна быть короткой: 2–4 предложения.
- Не оценивай ответ.
- Не объясняй ход рассуждений.
- Верни только текст отмазки без JSON, markdown и пояснений.
""".strip()

    def _build_user_prompt(self, request: ExcuseRequest) -> str:
        person_context = request.person_context or "Контекст не указан."

        return f"""
Категория ситуации:
{request.category}

Причина пользователя:
{request.reason}

Контекст пользователя:
{person_context}
""".strip()