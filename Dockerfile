FROM python:3.12-slim

RUN pip install poetry==1.7.1

WORKDIR /app

COPY poetry.lock .
COPY pyproject.toml .
COPY README.md .
COPY mortgage_calculator/ ./mortgage_calculator/

RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

EXPOSE 8501

# "--server.port=8501", "--server.address=0.0.0.0"
ENTRYPOINT ["poetry", "run", "streamlit", "run", "mortgage_calculator/calculator.py"]