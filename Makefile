SHELL := /bin/bash

ssh-app:
	terraform -chdir=./terraform output -raw private_key > ~/.ssh/shouldishovel.pem && chmod 600 ~/.ssh/shouldishovel.pem && ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i ~/.ssh/shouldishovel.pem ubuntu@$$(terraform -chdir=./terraform output -raw eip) && rm ~/.ssh/shouldishovel.pem

## Docker
airflow-init:
	docker compose up airflow-init

up:
	docker compose up -d

up-dev:
	docker compose -f docker-compose-localdev.yml up -d

down:
	docker compose down --remove-orphans

restart:
	docker compose restart

docker-delete-all:
	docker compose down --volumes --rmi all

## nginx
nginx-restart:
	docker compose exec frontend nginx -s reload

## api
api-restart:
	docker compose restart api-backend

api-rebuild:
	docker compose build --no-cache api-backend
	docker compose up -d api-backend

## website
update-website:
	aws s3 cp "static website/" "s3://shouldishovel.com/" --recursive

## front end
bundle:
	cd client; npx webpack

refresh_weather_data:
	docker exec -d backend sh -c "cd / && run-parts --report /etc/cron.hourly"