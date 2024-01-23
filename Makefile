run:
	@poetry run streamlit run mortgage_calculator/mortgage_calculator.py

run-thing:
	@poetry run streamlit run mortgage_calculator/populate_data.py

test:
	@poetry run pytest

build:
	@docker build -t mortgage-calculator .

tar:
	@docker save mortgage-calculator > cdk/docker-image.tar

run-docker:
	@docker run --rm -it -p 8501:8501 mortgage-calculator