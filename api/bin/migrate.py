#!/usr/bin/env python

import json

import micro_logger

import relations
import relations_pymysql

import unifist_unum

logger = micro_logger.getLogger("unifist-unum-api")

with open("/opt/service/secret/mysql.json", "r", encoding="utf-8") as mysql_file:
    mysql = json.loads(mysql_file.read())

sources = {
    name: relations_pymysql.Source(name, schema=name, autocommit=True, **mysql) for name in unifist_unum.SOURCES
}

cursor = sources["unum"].connection.cursor()

for name in sources:
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{name}`")

migrations = relations.Migrations()

# unifist goes first, its migration moves Route, Scribe and Clash into the unum schema if they were made in unifist

logger.info("migrations", extra={name: migrations.apply(name) for name in sources})
