from pydantic import BaseModel, Field


class ExcuseRequest(BaseModel):
    """
    Данные, которые frontend отправляет на backend для генерации отмазки.
    """

    category: str = Field(..., min_length=1, max_length=80, description="Категория ситуации оправдания")
    reason: str = Field(..., min_length=3, max_length=300, description="Почему так получилось")
    person_context: str | None = Field(
        default=None,
        max_length=700,
        description="Краткий контекст о пользователе, опционально"
    )


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
