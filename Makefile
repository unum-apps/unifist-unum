VERSION?=$(shell cat VERSION)
SEMVER=$(shell cat VERSION)
TILT_PORT=7634
.PHONY: up down semver tag untag

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

semver:
	cd api; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;
	cd gui; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;

tag:
	-git tag -a $(VERSION) -m "Version $(VERSION)"
	git push origin --tags

untag:
	-git tag -d $(VERSION)
	git push origin ":refs/tags/$(VERSION)"
