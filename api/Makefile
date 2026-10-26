ACCOUNT?=$(shell cat ../ACCOUNT)
IMAGE=unum-apps-unifist-unum-api
VERSION?=dev
SEMVER=?=$(VERSION)
NETWORK?=$(VERSION)-unifist-unum.io
MYSQL_IMAGE=mysql/mysql-server:5.7
MYSQL_HOST=$(IMAGE)-mysql-$(NETWORK)
DEBUG_PORT=15447
TTY=$(shell if tty -s; then echo "-it"; fi)
VOLUMES=-v ${PWD}/lib/:/opt/service/lib/ \
		-v ${PWD}/bin/:/opt/service/bin/ \
		-v ${PWD}/test/:/opt/service/test/ \
		-v ${PWD}/ddl/:/opt/service/ddl/ \
		-v ${PWD}/mysql.sh:/opt/service/mysql.sh \
		-v ${PWD}/.pylintrc:/opt/service/.pylintrc
ENVIRONMENT=-e MYSQL_HOST=$(MYSQL_HOST) \
			-e MYSQL_PORT=3306 \
			-e PYTHONDONTWRITEBYTECODE=1 \
			-e PYTHONUNBUFFERED=1 \
			-e test="python -m unittest -v" \
			-e debug="python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m unittest -v"

.PHONY: build cleanup network mysql shell debug test lint ddl image push semver

build:
	mkdir -p ddl
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

cleanup:
	-docker rm --force $(MYSQL_HOST)
	-docker network rm $(NETWORK)

network:
	-docker network create $(NETWORK)

mysql: network
	-docker rm --force $(MYSQL_HOST)
	docker run -d --network=$(NETWORK) -h $(MYSQL_HOST) --name=$(MYSQL_HOST) -e MYSQL_ALLOW_EMPTY_PASSWORD='yes' -e MYSQL_ROOT_HOST='%' $(MYSQL_IMAGE)
	docker run $(TTY) --rm --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "./mysql.sh"

shell: mysql
	-docker run $(TTY) --rm --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh

debug: mysql
	docker run $(TTY) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(DEBUG_PORT):5678 $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m unittest discover -v test"

test: mysql
	docker run $(TTY) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m --include 'lib/*.py'" ; status=$$? ; docker rm --force -v $(MYSQL_HOST) ; docker network rm $(NETWORK) ; exit $$status

lint:
	docker run $(TTY) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "pylint --rcfile=.pylintrc lib/"

ddl:
	docker run $(TTY) --rm $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "bin/ddl.py"

image: build

push: image
	docker push $(ACCOUNT)/$(IMAGE):$(VERSION)

semver:
	docker pull $(ACCOUNT)/$(IMAGE):$(VERSION)
	docker tag $(ACCOUNT)/$(IMAGE):$(VERSION) $(ACCOUNT)/$(IMAGE):$(SEMVER)
	docker push $(ACCOUNT)/$(IMAGE):$(SEMVER)
