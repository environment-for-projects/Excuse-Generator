import uvicorn

from app.config import configure_logging, log_openai_key_status, setup_env


def main() -> None:
    configure_logging()
    setup_env()
    log_openai_key_status()


if __name__ == "__main__":
    main()
    uvicorn.run(app="app.app:app", host="0.0.0.0", port=8000, reload=True)


