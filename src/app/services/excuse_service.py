from app.schemas import ExcuseRequest, ExcuseResult
from app.services.excuse_generator import ExcuseGenerator
from app.services.plausibility_grader import PlausibilityGrader


class ExcuseService:
    """
    Основной сервис генерации.
    Связывает генератор отмазки и грейдер правдоподобности.
    """

    def __init__(self) -> None:
        self.generator = ExcuseGenerator()
        self.grader = PlausibilityGrader()

    def generate_result(self, request: ExcuseRequest) -> ExcuseResult:
        draft = self.generator.generate(request)
        evaluation = self.grader.grade(request, draft)

        return ExcuseResult(
            excuse=draft.excuse,
            plausibility=evaluation.plausibility,
            comment=evaluation.comment,
            risk=evaluation.risk,
        )