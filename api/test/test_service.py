import unittest
import unittest.mock

import relations
import relations.unittest
import relations_unum

import service
import trust
import unifist_unum

import test_trust

import json
import os
import sys

if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

class Testrestx(relations.unittest.TestCase):

    @unittest.mock.patch.dict('os.environ', {"LOG_LEVEL": "INFO"})
    @unittest.mock.patch('service.open', new_callable=unittest.mock.mock_open, read_data='{"host": "%s", "user": "root", "password": ""}' % os.environ["MYSQL_HOST"])
    def setUp(self, mock_open):

        self.app = service.build()
        self.api = self.app.test_client()

        migrations = relations.Migrations()

        for name, source in self.app.source.items():
            cursor = source.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{name}`")
            migrations.load(name, "definition.sql")

    def tearDown(self):

        for name, source in self.app.source.items():
            cursor = source.connection.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS `{name}`")


class TestModels(unittest.TestCase):

    def test_models(self):

        self.assertEqual(
            sorted(model.__name__ for model in unifist_unum.models()),
            ["Clash", "Journal", "Route", "Scribe", "Sequence", "Slug"]
        )


class TestAPI(Testrestx):

    @unittest.mock.patch.dict('os.environ', {"LOG_LEVEL": "INFO"})
    @unittest.mock.patch('service.open', new_callable=unittest.mock.mock_open, read_data='{"host": "%s", "user": "root", "password": ""}' % os.environ["MYSQL_HOST"])
    def test_build(self, mock_open):

        app = service.build()

        self.assertEqual(app.name, "unifist-unum-api")
        self.assertEqual(app.sources, ["unifist", "unum"])
        self.assertEqual({name: source.schema for name, source in app.source.items()}, {"unifist": "unifist", "unum": "unum"})

    def test_migrations(self):

        migrations = relations.Migrations()

        for name, source in self.app.source.items():

            cursor = source.connection.cursor()

            for stamp, pair in migrations.list(name).items():

                for schema in self.app.source:
                    cursor.execute(f"DROP DATABASE IF EXISTS `{schema}`")
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{schema}`")

                try:
                    migrations.load(name, pair["definition"])
                    migrations.load(name, pair["migration"])
                except Exception as exception:
                    print(stamp)
                    raise exception

    def test_schemas(self):

        cursor = self.app.source["unum"].connection.cursor()

        cursor.execute("SELECT table_schema AS `schema`, table_name AS `table` FROM information_schema.tables WHERE table_schema IN ('unifist', 'unum')")

        self.assertEqual(
            sorted((row["schema"], row["table"]) for row in cursor.fetchall()),
            [
                ("unifist", "journal"), ("unifist", "sequence"), ("unifist", "slug"),
                ("unum", "clash"), ("unum", "route"), ("unum", "scribe")
            ]
        )

class TestHealth(Testrestx):

    def test_get(self):

        self.assertStatusValue(self.api.get("/health"), 200, "message", "OK")


class TestModelAPI(Testrestx):

    def test_models(self):

        response = self.api.get("/model")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(model["title"] for model in response.json["models"]),
            ["Clash", "Journal", "Route", "Scribe", "Sequence", "Slug"]
        )

    def test_empty(self):

        for model in self.api.get("/model").json["models"]:
            response = self.api.get(f"/model/{model['singular']}")
            self.assertEqual(response.status_code, 200, model["singular"])
            self.assertEqual(response.json[model["plural"]], [], model["singular"])

    def test_route(self):

        response = self.api.post("/model/route", json={"route": {"home": "b", "role": "owner", "holder": "b", "url": "http://b"}})

        self.assertEqual(response.status_code, 201)

        route_id = response.json["route"]["id"]

        response = self.api.get(f"/model/route/{route_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["route"]["holder"], "b")
        self.assertEqual(response.json["route"]["url"], "http://b")

        response = self.api.get("/model/route")

        self.assertEqual([route["id"] for route in response.json["routes"]], [route_id])


CONFIG = {
    "unum": "us",
    "apps": {"unifist-unum": "https://api.unifist-unum.us.localhost", "cumulus": "https://api.cumulus.us.localhost"},
    "trusted": "traefik/trusted",
    "roots": ["cumulus/unum-roots"]
}
SECRET = '{"host": "%s", "user": "root", "password": ""}' % os.environ["MYSQL_HOST"]

def opened(files):
    """
    Stands in for open, giving the files their contents and everything else the secret
    """

    def stand_in(path, *args, **kwargs):
        return unittest.mock.mock_open(read_data=files.get(path, SECRET))(path, *args, **kwargs)

    return stand_in


class TestJoin(relations.unittest.TestCase):
    """
    Following and accepting another unum, with the secrets in a dict and the other unum's answers made up
    """

    def setUp(self):

        self.us = test_trust.root("us")
        self.them = test_trust.root("them")

        files = {
            "/opt/service/config/unum.json": json.dumps(CONFIG),
            "/opt/service/certs/client/ca.crt": self.us
        }

        with unittest.mock.patch.dict('os.environ', {"LOG_LEVEL": "INFO"}), unittest.mock.patch('service.open', side_effect=opened(files)):
            self.app = service.build()

        self.api = self.app.test_client()

        self.opener = unittest.mock.patch('service.open', side_effect=opened(files))
        self.opener.start()
        self.addCleanup(self.opener.stop)

        migrations = relations.Migrations()

        for name, source in self.app.source.items():
            source.connection.cursor().execute(f"CREATE DATABASE IF NOT EXISTS `{name}`")
            migrations.load(name, "definition.sql")

        # The secrets, by namespace/secret

        self.secrets = {"traefik/trusted": self.us, "cumulus/unum-roots": ""}

        for method, side in [("read", lambda ref: self.secrets.get(ref, "")), ("write", self.secrets.__setitem__)]:
            patcher = unittest.mock.patch(f"trust.{method}", side_effect=side)
            patcher.start()
            self.addCleanup(patcher.stop)

        # What them answers, first with no certificate checked and then with its root

        self.url = "https://api.unifist-unum.them.localhost"
        self.answer = {
            "unum": "them",
            "root": self.them,
            "fingerprint": trust.fingerprint(self.them),
            "apps": {"unifist-unum": self.url, "cumulus": "https://api.cumulus.them.localhost"}
        }

        patcher = unittest.mock.patch("service.requests.get")
        self.get = patcher.start()
        self.addCleanup(patcher.stop)

        self.get.return_value.json.return_value = self.answer
        self.get.return_value.status_code = 200

    def tearDown(self):

        for name, source in self.app.source.items():
            source.connection.cursor().execute(f"DROP DATABASE IF EXISTS `{name}`")

    def routes(self):

        return [(route.home, route.role, route.holder, route.url) for route in relations_unum.Route.many(holder="them").retrieve()]

    def test_unum(self):

        response = self.api.get("/unum")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            "unum": "us",
            "root": self.us,
            "fingerprint": trust.fingerprint(self.us),
            "apps": CONFIG["apps"]
        })

    def test_follow(self):

        body = {"url": self.url, "fingerprint": trust.fingerprint(self.them)}

        response = self.api.post("/follow", json=body)

        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json["unum"], "them")

        # Asked for the root with nothing checked, and then with the root it gave

        self.assertEqual(self.get.call_count, 2)
        self.assertEqual(self.get.call_args_list[0].args, (f"{self.url}/unum",))
        self.assertIs(self.get.call_args_list[0].kwargs["verify"], False)
        self.assertNotIn(self.get.call_args_list[1].kwargs["verify"], [False, True])

        # The Route row to its cumulus api, the only app it has but the unum app, and its root to verify it with

        self.assertEqual(self.routes(), [("them", "owner", "them", "https://api.cumulus.them.localhost")])
        self.assertEqual(trust.split(self.secrets["cumulus/unum-roots"]), [self.them])
        self.assertEqual(trust.split(self.secrets["traefik/trusted"]), [self.us])

        # Again changes nothing

        response = self.api.post("/follow", json=body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.routes()), 1)
        self.assertEqual(trust.split(self.secrets["cumulus/unum-roots"]), [self.them])

        # A Route on an old url is changed

        route = relations_unum.Route.many(holder="them").retrieve()[0]
        route.url = "http://api.cumulus.them.localhost"
        route.update()

        self.api.post("/follow", json=body)

        self.assertEqual(self.routes(), [("them", "owner", "them", "https://api.cumulus.them.localhost")])

    def test_follow_refused(self):

        # A fingerprint that isn't the root's

        response = self.api.post("/follow", json={"url": self.url, "fingerprint": "0" * 64})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.routes(), [])
        self.assertEqual(self.secrets["cumulus/unum-roots"], "")

        # A server certificate not from that root

        self.get.side_effect = [self.get.return_value, Exception("certificate verify failed")]

        response = self.api.post("/follow", json={"url": self.url, "fingerprint": trust.fingerprint(self.them)})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.routes(), [])
        self.assertEqual(self.secrets["cumulus/unum-roots"], "")

    def test_follow_app(self):

        # Which of its apps to route to, when it has more than one

        self.answer["apps"]["ledger"] = "https://api.ledger.them.localhost"

        body = {"url": self.url, "fingerprint": trust.fingerprint(self.them)}

        self.assertEqual(self.api.post("/follow", json=body).status_code, 400)

        response = self.api.post("/follow", json={**body, "app": "ledger"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.routes(), [("them", "owner", "them", "https://api.ledger.them.localhost")])

        self.assertEqual(self.api.post("/follow", json={**body, "app": "away"}).status_code, 400)

    def test_unfollow(self):

        self.api.post("/follow", json={"url": self.url, "fingerprint": trust.fingerprint(self.them)})

        response = self.api.delete("/follow/them")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.routes(), [])
        self.assertEqual(self.secrets["cumulus/unum-roots"].strip(), "")

        # Not itself

        self.assertEqual(self.api.delete("/follow/us").status_code, 400)

    def test_accept(self):

        body = {"url": self.url, "fingerprint": trust.fingerprint(self.them)}

        response = self.api.post("/accept", json=body)

        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json["unum"], "them")
        self.assertEqual(trust.split(self.secrets["traefik/trusted"]), [self.us, self.them])
        self.assertEqual(self.routes(), [])

        # Once

        self.assertEqual(self.api.post("/accept", json=body).status_code, 200)
        self.assertEqual(trust.split(self.secrets["traefik/trusted"]), [self.us, self.them])

        # Not on a fingerprint that isn't the root's

        self.assertEqual(self.api.post("/accept", json={**body, "fingerprint": "0" * 64}).status_code, 409)

    def test_revoke(self):

        self.api.post("/accept", json={"url": self.url, "fingerprint": trust.fingerprint(self.them)})

        response = self.api.delete("/accept/them")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(trust.split(self.secrets["traefik/trusted"]), [self.us])

        # Nothing to revoke

        self.assertEqual(self.api.delete("/accept/them").status_code, 200)

        # Never the last root

        self.assertEqual(self.api.delete("/accept/us").status_code, 409)
        self.assertEqual(trust.split(self.secrets["traefik/trusted"]), [self.us])
