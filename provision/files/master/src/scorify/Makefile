DOCKER_REPO=fredericcombes

all:

build:
	docker build -t scorify-web:latest -f docker-files/dockerfile-web .
	docker build -t scorify-worker-split:latest -f docker-files/dockerfile-worker-split .
	docker build -t scorify-worker-fft:latest -f docker-files/dockerfile-worker-fft .
	docker build -t scorify-worker-peak:latest -f docker-files/dockerfile-worker-peak .
	docker build -t scorify-worker-score:latest -f docker-files/dockerfile-worker-score .

push:
	docker tag scorify-web:latest $DOCKER_REPO/scorify-web:latest
	docker tag scorify-worker-split:latest $DOCKER_REPO/scorify-worker-score:latest
	docker tag scorify-worker-fft:latest $DOCKER_REPO/scorify-worker-fft:latest
	docker tag scorify-worker-peak:latest $DOCKER_REPO/scorify-worker-peak:latest
	docker tag scorify-worker-score:latest $DOCKER_REPO/scorify-worker-score:latest
	docker push $DOCKER_REPO/scorify-web:latest
	docker push $DOCKER_REPO/scorify-worker-peak:latest
	docker push $DOCKER_REPO/scorify-worker-fft:latest
	docker push $DOCKER_REPO/scorify-worker-peak:latest
	docker push $DOCKER_REPO/scorify-worker-score:latest


pull:
	docker pull $DOCKER_REPO/scorify-web:latest			|| :
	docker pull $DOCKER_REPO/scorify-worker-score:latest 	|| :
	docker pull $DOCKER_REPO/scorify-worker-fft:latest 	|| :
	docker pull $DOCKER_REPO/scorify-worker-peak:latest 	|| :
	docker pull $DOCKER_REPO/scorify-worker-score:latest 	|| :

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
