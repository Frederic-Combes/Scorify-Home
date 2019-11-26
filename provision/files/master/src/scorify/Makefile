all:

build:
	docker build -t scorify-web:latest -f docker-file/dockerfile-web .
	docker build -tscorify-worker-split:latest -f docker-file/dockerfile-worker-split .
	docker build -tscorify-worker-fft:latest -f docker-file/dockerfile-workder-fft .
	docker build -tscorify-worker-peak:latest -f docker-file/dockerfile-worker-peak .
	docker build -tscorify-worker-score:latest -f docker-file/dockerfile-worker-score .

	docker-compose -f docker-files/compose.yml build

push:
	docker tag scorify-web:latest fredericcombes/scorify-web:latest
	docker tag scorify-worker-split:latest fredericcombes/scorify-worker-score:latest
	docker tag scorify-worker-fft:latest fredericcombes/scorify-worker-fft:latest
	docker tag scorify-worker-pip:latest fredericcombes/scorify-worker-peak:latest
	docker tag scorify-worker-score:latest fredericcombes/scorify-worker-score:latest

build-web:
	docker-compose -f docker-files/compose.yml build web

build-worker-split:
	docker-compose -f docker-files/compose.yml build worker-split

build-worker-fft:
	docker-compose -f docker-files/compose.yml build worker-fft

run: run-redis

run-redis:
	docker-compose -f docker-files/compose.yml up -d redis

run-all:
	docker-compose -f docker-files/compose.yml up -d

run-web:
	docker-compose -f docker-files/compose.yml up -d web
