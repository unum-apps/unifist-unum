import unittest
import unittest.mock

import relations
import relations.unittest

import service
import unifist_unum

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

        response = self.api.post("/model/route", json={"route": {"unum": "b", "role": "owner", "holder": "b", "url": "http://b"}})

        self.assertEqual(response.status_code, 201)

        route_id = response.json["route"]["id"]

        response = self.api.get(f"/model/route/{route_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["route"]["holder"], "b")
        self.assertEqual(response.json["route"]["url"], "http://b")

        response = self.api.get("/model/route")

        self.assertEqual([route["id"] for route in response.json["routes"]], [route_id])
