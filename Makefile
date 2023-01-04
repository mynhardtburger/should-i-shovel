SHELL := /bin/bash

ssh-app:
	terraform -chdir=./terraform output -raw private_key > ~/.ssh/shouldishovel.pem && chmod 600 ~/.ssh/shouldishovel.pem && ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i ~/.ssh/shouldishovel.pem ubuntu@$$(terraform -chdir=./terraform output -raw ec2_public_dns) && rm ~/.ssh/shouldishovel.pem

## Docker
airflow-init:
	docker-compose up airflow-init

up:
	docker-compose up

down:
	docker-compose down --volumes --remove-orphans

restart:
	docker-compose restart

docker-delete-all:
	docker-compose down --volumes --rmi all

## nginx
nginx-restart:
	docker-compose exec frontend nginx -s reload

## api
api-start:
	source ~/venv/shouldishovel/bin/activate;\
	cd api;\
	uvicorn main:app --reload &