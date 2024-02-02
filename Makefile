run:
	@poetry run streamlit run mortgage_calculator/calculator.py

run-plus:
	@poetry run streamlit run mortgage_calculator/test_calculator.py

test:
	@poetry run pytest tests/test_utils_finance.py

build:
	@docker build -t mortgage-calculator .

tar:
	@docker save mortgage-calculator > cdk/docker-image.tar

run-docker:
	@docker run --rm -it -p 8501:8501 mortgage-calculator