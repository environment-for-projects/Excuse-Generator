from __future__ import annotations

import logging

import httpx
from nicegui import ui

logger = logging.getLogger(__name__)

API_BASE_URL = "http://127.0.0.1:8000"

# FALLBACK_CATEGORIES используется только как аварийный режим,
# если backend endpoint GET /api/categories недоступен.
# Основной источник категорий — backend API, а не frontend.
FALLBACK_CATEGORIES = [
    "Опоздание",
    "Не сделал задачу",
    "Забыл событие",
    "Не ответил вовремя",
    "Не пришёл на встречу",
]

BTN_GENERATE = "Сгенерировать отмазку"
BTN_GENERATING = "Генерируем..."

CARD = "w-full bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden"
TOOLBAR = "w-full bg-gray-50 border-b border-gray-200 px-4 py-2 sm:px-5 sm:py-3"
CARD_BODY = "w-full px-4 py-3 sm:px-5 sm:py-4 gap-2 sm:gap-3"
SECTION = "text-xs font-semibold uppercase tracking-wide text-gray-600"
BODY = "text-[15px] leading-snug text-gray-900 whitespace-pre-wrap"
MUTED = "text-sm leading-snug text-gray-500 whitespace-pre-wrap"


# --- API ---


async def load_categories() -> list[str]:
    """Категории с backend (GET /api/categories). FALLBACK_CATEGORIES — только при сбое."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/api/categories")
            response.raise_for_status()
            names = [item["name"] for item in response.json().get("categories", [])]
        if not names:
            raise ValueError("empty categories")
        return names
    except Exception:
        logger.exception(
            "Failed to load categories from %s/api/categories",
            API_BASE_URL,
        )
        ui.notify(
            "Не удалось загрузить категории с сервера. Используем список по умолчанию.",
            type="warning",
        )
        return list(FALLBACK_CATEGORIES)


async def request_excuse(
    category: str,
    reason: str,
    person_context: str | None,
) -> dict:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/generate",
            json={
                "category": category,
                "reason": reason,
                "person_context": person_context,
            },
        )
        response.raise_for_status()
        return response.json()


# --- UI ---


def copy_excuse(text: str) -> None:
    ui.clipboard.write(text)
    ui.notify("Отмазка скопирована", type="positive")


def _card_toolbar(title: str) -> None:
    with ui.row().classes(f"{TOOLBAR} items-center"):
        ui.label(title).classes("text-sm font-semibold text-gray-900")


def _progress_color(plausibility: int) -> str:
    if plausibility >= 75:
        return "dark"
    if plausibility >= 50:
        return "grey-8"
    return "grey-5"


def build_header() -> None:
    with ui.column().classes("w-full gap-1 sm:gap-2"):
        ui.label("Генератор отмазок").classes(
            "text-xl sm:text-3xl font-semibold text-gray-900 tracking-tight"
        )
        ui.label(
            "Выбери ситуацию, добавь причину и контекст — "
            "AI сформирует правдоподобное сообщение."
        ).classes("text-gray-500 text-xs sm:text-sm leading-relaxed max-w-2xl")
        ui.chip("Generator + LLM Grader", icon="auto_awesome").props(
            "outline dense color=grey-9"
        ).classes("self-start text-gray-800")


def render_empty_result(container: ui.column) -> None:
    container.clear()
    with container:
        with ui.column().classes("w-full items-center gap-2 py-8 sm:py-10"):
            ui.icon("inbox", size="sm").classes("text-gray-300")
            ui.label("Результат появится здесь после генерации").classes(
                "text-gray-500 text-center text-sm"
            )


def render_result(container: ui.column, data: dict) -> None:
    container.clear()

    excuse = (data.get("excuse") or "").strip() or "—"
    plausibility = max(0, min(100, int(data.get("plausibility", 0))))
    comment = (data.get("comment") or "").strip() or "—"
    risk = (data.get("risk") or "").strip() or "—"

    with container:
        with ui.column().classes("w-full gap-1.5"):
            with ui.row().classes("w-full items-center justify-between gap-2"):
                ui.label("Отмазка").classes(SECTION)
                ui.button(
                    icon="content_copy",
                    on_click=lambda t=excuse: copy_excuse(t),
                ).props("flat round dense color=grey-9").tooltip("Скопировать")
            ui.label(excuse).classes(BODY)

        ui.separator().classes("my-2 sm:my-2.5 bg-gray-200")

        with ui.column().classes("w-full gap-1"):
            ui.label("Правдоподобность").classes(SECTION)
            ui.label(f"{plausibility} / 100").classes(
                "text-lg sm:text-xl font-semibold text-gray-900"
            )
            ui.linear_progress(
                value=plausibility / 100,
                show_value=False,
            ).classes("h-1.5").props(f"color={_progress_color(plausibility)} rounded")

        ui.separator().classes("my-2 sm:my-2.5 bg-gray-200")

        with ui.column().classes("w-full gap-0.5"):
            ui.label("Комментарий").classes(SECTION)
            ui.label(comment).classes(MUTED)

        with ui.column().classes("w-full gap-0.5 mt-1.5 sm:mt-2"):
            ui.label("Риск").classes(SECTION)
            ui.label(risk).classes(MUTED)


async def handle_generate(
    result_container: ui.column,
    category_select: ui.select,
    reason_input: ui.textarea,
    person_context_input: ui.textarea,
    generate_button: ui.button,
    spinner: ui.spinner,
) -> None:
    category = category_select.value
    if not category:
        ui.notify("Выберите категорию", type="warning")
        return

    reason = (reason_input.value or "").strip()
    if len(reason) < 3:
        ui.notify("Опишите причину — минимум 3 символа", type="warning")
        return

    person_context = (person_context_input.value or "").strip() or None

    generate_button.disable()
    generate_button.set_text(BTN_GENERATING)
    spinner.set_visibility(True)

    try:
        data = await request_excuse(category, reason, person_context)
        render_result(result_container, data)
    except Exception:
        logger.exception(
            "Failed to generate excuse via %s/api/generate",
            API_BASE_URL,
        )
        ui.notify(
            "Не удалось сгенерировать отмазку. Проверь backend или API-ключ.",
            type="negative",
        )
    finally:
        generate_button.enable()
        generate_button.set_text(BTN_GENERATE)
        spinner.set_visibility(False)


def bind_generate_handler(
    result_container: ui.column,
    category_select: ui.select,
    reason_input: ui.textarea,
    person_context_input: ui.textarea,
    generate_button: ui.button,
    spinner: ui.spinner,
) -> None:
    generate_button.on_click(
        lambda: handle_generate(
            result_container,
            category_select,
            reason_input,
            person_context_input,
            generate_button,
            spinner,
        )
    )


def build_page(category_options: list[str]) -> None:
    ui.add_head_html("<style>body { background: #F8FAFC !important; }</style>")

    with ui.column().classes(
        "w-full max-w-[1120px] mx-auto px-4 py-4 sm:px-6 sm:py-8 gap-4 sm:gap-6"
    ):
        with ui.card().classes(
            "w-full bg-white border border-gray-200 rounded-xl shadow-sm"
        ).props("flat bordered"):
            with ui.row().classes(
                "w-full items-center justify-between gap-3 sm:gap-4 px-4 py-3 sm:px-5 sm:py-4"
            ):
                with ui.column().classes("gap-1 sm:gap-2"):
                    build_header()

        # columns=1 у NiceGUI задаёт inline grid-template-columns и ломает md:grid-cols-2;
        # одна колонка на mobile — через grid-cols-1, две на desktop — md:grid-cols-2.
        with ui.grid().classes("w-full gap-3 sm:gap-4 grid-cols-1 md:grid-cols-2 items-start"):
            with ui.card().classes(CARD).props("flat bordered"):
                _card_toolbar("Параметры")
                with ui.column().classes(CARD_BODY):
                    category_select = ui.select(
                        options=category_options,
                        label="Категория",
                        value=category_options[0] if category_options else None,
                    ).classes("w-full").props("outlined dense")

                    reason_input = ui.textarea(
                        label="Почему так получилось",
                        placeholder="Например: проспал, потому что ночью доделывал проект",
                    ).classes("w-full").props("outlined dense autogrow")

                    person_context_input = ui.textarea(
                        label="Контекст о тебе (опционально)",
                        placeholder="Например: я студент, учусь и работаю",
                    ).classes("w-full").props("outlined dense autogrow")

                    with ui.row().classes("w-full items-center gap-2 pt-0.5 sm:pt-1"):
                        generate_button = ui.button(BTN_GENERATE).classes(
                            "flex-grow"
                        ).props("color=grey-10 unelevated no-caps")
                        spinner = ui.spinner(size="sm", color="grey")
                        spinner.set_visibility(False)

            with ui.card().classes(CARD).props("flat bordered"):
                _card_toolbar("Результат")
                with ui.column().classes(CARD_BODY):
                    result_container = ui.column().classes("w-full")
                    render_empty_result(result_container)

        bind_generate_handler(
            result_container,
            category_select,
            reason_input,
            person_context_input,
            generate_button,
            spinner,
        )


@ui.page("/")
async def index() -> None:
    categories = await load_categories()
    build_page(categories)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    ui.run(
        title="Генератор отмазок",
        host="0.0.0.0",
        port=8080,
        reload=False,
        show=True,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
