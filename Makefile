build:
	@docker build -t mortgage-calculator .

ssh:
	@ssh -i ~/.ssh/practice_ec2_keys.pem ec2-user@ec2-3-142-98-137.us-east-2.compute.amazonaws.com

push-ecr:
	@aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 202571202047.dkr.ecr.us-east-2.amazonaws.com
	@docker build -t mortgage-simulator .
	@docker tag mortgage-simulator:latest 202571202047.dkr.ecr.us-east-2.amazonaws.com/mortgage-simulator:latest
	@docker push 202571202047.dkr.ecr.us-east-2.amazonaws.com/mortgage-simulator:latest

run:
	@docker run --rm -it -p 8501:8501 mortgage-calculator