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

run-redis:
	docker-compose -f docker-files/compose.yml up -d redis

run-all:
	docker-compose -f docker-files/compose.yml up -d

run-web:
	docker-compose -f docker-files/compose.yml up -d web
