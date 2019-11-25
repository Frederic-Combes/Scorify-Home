all:

build:
	docker-compose -f docker-files/compose.yml build

build-web:
	docker-compose -f docker-files/compose.yml build web

build-worker-split:
	docker-compose -f docker-files/compose.yml build worker-split

build-worker-fft:
	docker-compose -f docker-files/compose.yml build worker-fft

run: run-redis
	# sudo docker-compose -f docker-files/compose.yml up

run-redis:
	sudo docker-compose -d -f docker-files/compose.yml up redis

run-web:
	sudo docker-compose -f docker-files/compose.yml up scorify-web
