from pydantic import BaseModel, Field, field_validator


class ExcuseRequest(BaseModel):
    """
    Данные, которые frontend отправляет на backend для генерации отмазки.
    """

    category: str = Field(..., min_length=1, max_length=80, description="Категория ситуации оправдания")
    reason: str | None = Field(
        default=None,
        max_length=300,
        description="Ситуация и подсказка для отмазки",
    )
    person_context: str | None = Field(
        default=None,
        max_length=700,
        description="Краткий контекст о пользователе, опционально",
    )

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("reason")
    @classmethod
    def validate_reason_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 3:
            raise ValueError("Причина должна содержать минимум 3 символа")
        return value


class ExcuseDraft(BaseModel):
    """
    Промежуточный результат Excuse Generator LLM-вызова.
    Возвращает только текст отмазки.
    """

    excuse: str = Field(..., min_length=5,max_length=700, description="Сгенерированный текст отмазки")


class ExcuseEvaluation(BaseModel):
    """
    Промежуточный результат второго LLM-вызова Plausibility Grader.
    Grader оценивает правдоподобность отмазки.
    """

    plausibility: int = Field(..., ge=0, le=100, description="Оценка правдоподобности от 0 до 100")
    comment: str = Field(..., min_length=3,max_length=180, description="Краткое объяснение оценки")
    risk: str | None = Field(
        default=None,
        max_length=180,
        description="Главный риск, почему отмазке могут не поверить"
    )


class ExcuseResult(BaseModel):
    """
    Финальный ответ backend'а для frontend.
    """

    excuse: str = Field(..., min_length=5, description="Сгенерированный текст отмазки")
    plausibility: int = Field(..., ge=0, le=100, description="Оценка правдоподобности от 0 до 100")
    comment: str = Field(..., min_length=3, max_length=180, description="Краткое объяснение оценки")
    risk: str | None = Field(
        default=None,
        max_length=180,
        description="Главный риск, почему отмазке могут не поверить",
    )


class Category(BaseModel):
    """
    Категория ситуации.
    """

    id: int
    name: str = Field(..., min_length=1, max_length=80, description="Название категории")

class CategoriesResponse(BaseModel):
    """
    Ответ endpoint'а GET /api/categories.
    """

    categories: list[Category]
