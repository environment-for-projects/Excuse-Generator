import logging

from app.openai_client import get_openai_client
from app.schemas import ExcuseDraft, ExcuseRequest

logger = logging.getLogger(__name__)


class ExcuseGenerator:
    """
    Сервис первого LLM-вызова - Excuse Generator.
    Генерирует текст отмазки. Использует более лёгкую модель,
    здесь важнее скорость и креативность, а не строгая оценка.
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
        Ты генератор убедительных, креативных, но реалистичных отмазок.

        Твоя задача — сгенерировать одну короткую отмазку на русском языке,
        которую можно отправить реальному человеку.

        Главная цель:
        отмазка должна звучать не шаблонно, а как живое сообщение: с конкретной деталью,
        лёгкой самоиронией или аккуратным объяснением, но без абсурда и лишней драмы.

        Правила:
        - Пиши естественно, как сообщение в мессенджере.
        - Используй категорию, причину (если указана) и контекст пользователя.
        - Если причина не указана, опирайся на категорию ситуации и сформулируй правдоподобную общую отмазку.
        - Если контекст не указан, не выдумывай работу, учёбу, возраст или личные обстоятельства.
        - Можно добавить небольшую бытовую деталь, если она логично следует из причины или категории.
        - Не добавляй факты, которые полностью меняют смысл причины.
        - Не придумывай тяжёлые болезни, аварии, смерть родственников и другие драматичные события.
        - Не делай отмазку слишком официальной.
        - Не делай отмазку слишком детской или абсурдной.
        - В конце добавь короткое действие: что человек уже делает, чтобы исправить ситуацию.
        - Длина: 2–4 предложения.
        - Верни только текст отмазки без JSON, markdown и пояснений.

        Стиль:
        - живой;
        - убедительный;
        - немного креативный;
        - без канцелярита;
        - без чрезмерной театральности.
        """.strip()

    def _build_user_prompt(self, request: ExcuseRequest) -> str:
        reason = request.reason or "Причина не указана."
        person_context = request.person_context or "Контекст не указан."

        return f"""
Категория ситуации:
{request.category}

Причина пользователя:
{reason}

Контекст пользователя:
{person_context}
""".strip()