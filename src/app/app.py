from fastapi import FastAPI

from app.config import configure_logging, log_openai_key_status, setup_env
from app.schemas import CategoriesResponse, Category, ExcuseRequest, ExcuseResult
from app.services.excuse_service import ExcuseService

from fastapi.middleware.cors import CORSMiddleware

configure_logging()
setup_env()
log_openai_key_status()

app = FastAPI(
    title="Excuse Generator API",
    description="Мини-сервис для генерации правдоподобных отмазок",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

excuse_service = ExcuseService()

CATEGORIES = [
    Category(id=1, name="Опоздание"),
    Category(id=2, name="Не сделал задачу"),
    Category(id=3, name="Забыл событие"),
    Category(id=4, name="Не ответил вовремя"),
    Category(id=5, name="Не пришёл на встречу"),
]


@app.get("/api/categories", response_model=CategoriesResponse)
def get_categories() -> CategoriesResponse:
    return CategoriesResponse(categories=CATEGORIES)


@app.post("/api/generate", response_model=ExcuseResult)
def generate_excuse(request: ExcuseRequest) -> ExcuseResult:
    return excuse_service.generate_result(request)