VERSION?=$(shell cat VERSION)
SEMVER=$(shell cat VERSION)
TILT_PORT=7634
INSTALL=python:3.13
VOLUMES=-v ${PWD}/api/:/opt/service/api/ \
		-v ${PWD}/VERSION:/opt/service/VERSION \
		-v ${PWD}/setup.py:/opt/service/setup.py
.PHONY: up down setup semver tag untag

up:
	kubectx docker-desktop
	mkdir -p secret
	mkdir -p config
	test -f secret/mysql.json || echo '{"host": "db.mysql", "user": "root", "password": "local"}' > secret/mysql.json
	test -d api/ddl || (cd api; make build; make ddl;)
	tilt --port $(TILT_PORT) up

down:
	kubectx docker-desktop
	tilt down

setup:
	docker run $(TTY) $(VOLUMES) $(INSTALL) sh -c "cp -r /opt/service /opt/install && \
	cd /opt/install/ && pip install . && \
	python -m unifist_unum"

semver:
	cd api; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;
	cd gui; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;

tag:
	git ls-remote --exit-code --tags origin $(VERSION) > /dev/null 2>&1 || { \
	git rev-parse -q --verify refs/tags/$(VERSION) > /dev/null || git tag -a $(VERSION) -m "Version $(VERSION)"; \
	git push origin $(VERSION); }

untag:
	-git tag -d $(VERSION)
	git push origin ":refs/tags/$(VERSION)"
