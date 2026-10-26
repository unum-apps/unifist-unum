"""
Module for the Unifist Unum API
"""

import json
import sys

import micro_logger

import flask
import flask_restx
import relations_pymysql
import relations_restx
import relations_unifist

import unifist_unum

WHO = "unifist-unum"
NAME = f"{WHO}-api"

def build():
    """
    Builds the Flask App
    """

    app = flask.Flask(NAME)

    app.logger = micro_logger.getLogger(NAME)
    app.sources = unifist_unum.SOURCES

    api = relations_restx.Api(app)

    with open("/opt/service/secret/mysql.json", "r", encoding="utf-8") as mysql_file:
        mysql = json.loads(mysql_file.read())

    app.source = {
        name: relations_pymysql.Source(name, schema=name, autocommit=True, **mysql) for name in app.sources
    }

    def ping():
        for source in app.source.values():
            source.connection.ping(True)

    app.before_request(ping)

    api.add_resource(Health, '/health')

    relations_unifist.attach(api, sys.modules[__name__], unifist_unum.models())

    return app

class Health(flask_restx.Resource):
    """
    Class for Health checks
    """

    def get(self):
        """
        Just return ok
        """
        return {"message": "OK"}
