DOCKER_REPO=fredericcombes

all:

build: build-web build-worker-split build-worker-fft build-worker-peak build-worker-score

push:
	# docker tag scorify-web:latest $(DOCKER_REPO)/scorify-web:latest
	# docker tag scorify-worker-split:latest $(DOCKER_REPO)/scorify-worker-split:latest
	# docker tag scorify-worker-fft:latest $(DOCKER_REPO)/scorify-worker-fft:latest
	# docker tag scorify-worker-peak:latest $(DOCKER_REPO)/scorify-worker-peak:latest
	# docker tag scorify-worker-score:latest $(DOCKER_REPO)/scorify-worker-score:latest
	docker push $(DOCKER_REPO)/scorify-web:latest
	docker push $(DOCKER_REPO)/scorify-worker-split:latest
	docker push $(DOCKER_REPO)/scorify-worker-fft:latest
	docker push $(DOCKER_REPO)/scorify-worker-peak:latest
	docker push $(DOCKER_REPO)/scorify-worker-score:latest


pull:
	docker pull $(DOCKER_REPO)/scorify-web:latest			|| :
	docker pull $(DOCKER_REPO)/scorify-worker-split:latest 	|| :
	docker pull $(DOCKER_REPO)/scorify-worker-fft:latest 	|| :
	docker pull $(DOCKER_REPO)/scorify-worker-peak:latest 	|| :
	docker pull $(DOCKER_REPO)/scorify-worker-score:latest 	|| :

build-web:
	docker build -f docker-files/docker-web -t scorify-web:latest .

build-worker-split:
	docker-compose -f docker-files/compose.yml build worker-split

build-worker-fft:
	docker-compose -f docker-files/compose.yml build worker-fft

build-worker-peak:
	docker-compose -f docker-files/compose.yml build worker-peak

build-worker-score:
	docker-compose -f docker-files/compose.yml build worker-score

run: run-redis

run-redis:
	docker-compose -f docker-files/compose.yml up -d redis

run-all:
	docker-compose -f docker-files/compose.yml up -d

run-web:
	docker-compose -f docker-files/compose.yml up -d web

run-worker-split:
	docker-compose -f docker-files/compose.yml up -d worker-split
