import logging

from pydantic import ValidationError

from app.openai_client import get_openai_client
from app.schemas import ExcuseDraft, ExcuseEvaluation, ExcuseRequest

logger = logging.getLogger(__name__)


class PlausibilityGrader:
    """
    Сервис второго LLM-вызова - Plausibility Grader.
    Оценивает правдоподобность сгенерированной отмазки.
    """

    def grade(self, request: ExcuseRequest, draft: ExcuseDraft) -> ExcuseEvaluation:
        try:
            response = get_openai_client().responses.parse(
                model="gpt-4.1",
                instructions=self._build_system_prompt(),
                input=self._build_user_prompt(request, draft),
                text_format=ExcuseEvaluation,
                temperature=0.1,
                max_output_tokens=300,
            )

            if response.output_parsed is None:
                logger.warning("Plausibility grader returned empty parsed output")
                return self._fallback_evaluation()

            return self._normalize_evaluation(response.output_parsed)

        except ValidationError as error:
            logger.exception("Plausibility grader validation error: %s", error)
            return self._fallback_evaluation()

        except Exception as error:
            logger.exception("Plausibility grader failed: %s", error)
            return self._fallback_evaluation()

    def _fallback_evaluation(self) -> ExcuseEvaluation:
        return ExcuseEvaluation(
            plausibility=70,
            comment="Отмазка в целом соответствует ситуации и звучит достаточно естественно.",
            risk="Минимальный риск: причина может выглядеть слабее при частом повторении.",
        )

    def _normalize_evaluation(self, evaluation: ExcuseEvaluation) -> ExcuseEvaluation:
        fallback = self._fallback_evaluation()

        plausibility = max(0, min(100, evaluation.plausibility))

        comment = evaluation.comment.strip() if evaluation.comment else fallback.comment
        if len(comment) < 3:
            comment = fallback.comment
        if len(comment) > 180:
            comment = comment[:177] + "..."

        risk = evaluation.risk.strip() if evaluation.risk else fallback.risk
        if len(risk) > 180:
            risk = risk[:177] + "..."

        return ExcuseEvaluation(
            plausibility=plausibility,
            comment=comment,
            risk=risk,
        )

    def _build_system_prompt(self) -> str:
        return """
        Ты строгий оценщик правдоподобности отмазок. Оцени готовую отмазку по шкале 0–100.

         Данные:
        - Категория — тип ситуации.
        - Причина — исходное объяснение пользователя, сли причина не указана, считай причину неизвестной.
        - Контекст — сведения о пользователе. Если контекста нет, считай статус, работу, учёбу и возраст неизвестными.
        - Отмазка — текст для оценки.

        Шкала:
        0–40 — вряд ли поверят.
        41–60 — слабовато.
        61–75 — нормально, с оговорками.
        76–88 — хорошо, можно отправлять.
        89–100 — очень убедительно, редко.

        Ограничения оценки:
        - Не ставь 85 автоматически.
        - Обычная нормальная отмазка чаще получает 60–75.
        - Чем необычнее ситуация для контекста пользователя, тем ниже оценка.
        - Если отмазка не соответствует категории, оценка не выше 50.
        - Если отмазка добавляет факты, которых не было во входных данных, оценка не выше 75.
        - Если причина короткая: "проспал", "забыл", "не успел", оценка обычно не выше 75.

        Формат ответа:
        - plausibility: целое 0–100.
        - comment и risk: только по правилам выше, без markdown.
        """.strip()

    def _build_user_prompt(self, request: ExcuseRequest, draft: ExcuseDraft) -> str:
        reason = request.reason or "Причина не указана."
        person_context = request.person_context or "Контекст не указан."

        return f"""
        Оцени сгенерированную отмазку.

        Категория ситуации:
        {request.category}

        Исходная причина пользователя:
        {reason}

        Контекст пользователя:
        {person_context}

        Сгенерированная отмазка:
        {draft.excuse}
        """.strip()
