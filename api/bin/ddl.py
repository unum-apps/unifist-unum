#!/usr/bin/env python

import relations
import relations_pymysql

import unifist_unum

for name in unifist_unum.SOURCES:
    relations_pymysql.Source(name, schema=name, connection=False)

migrations = relations.Migrations()

migrations.generate(unifist_unum.models())

for name in unifist_unum.SOURCES:
    migrations.convert(name)
