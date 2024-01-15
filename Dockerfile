FROM python:3.12-slim

RUN pip install poetry==1.7.1

WORKDIR /app

COPY poetry.lock ./
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

RUN poetry install
EXPOSE 8501

# "--server.port=8501", "--server.address=0.0.0.0"
ENTRYPOINT ["poetry", "run", "streamlit", "run", "src/mortgage_calculator.py"]