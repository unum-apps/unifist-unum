"""
Module for the Unifist Unum API
"""

import json
import sys
import tempfile

import micro_logger

import flask
import flask_restx
import relations_pymysql
import relations_restx
import relations_unifist
import relations_unum
import requests

import trust
import unifist_unum

WHO = "unifist-unum"
NAME = f"{WHO}-api"

CONFIG = "/opt/service/config/unum.json"  # This unum's name, the urls of its apps, and the secrets that hold the roots it trusts
ROOT = "/opt/service/certs/client/ca.crt"  # The root of this unum, which its client certificate comes from

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
    api.add_resource(Unum, '/unum')
    api.add_resource(Lookup, '/lookup')
    api.add_resource(Follow, '/follow')
    api.add_resource(Followed, '/follow/<string:unum>')
    api.add_resource(Accept, '/accept')
    api.add_resource(Accepted, '/accept/<string:unum>')

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


def config():
    """
    What this unum is told about itself
    """

    with open(CONFIG, "r", encoding="utf-8") as config_file:
        return json.loads(config_file.read())

def look(url):
    """
    What the unum at the url says it is, with nothing checked, because its root can only be taken on trust the first time
    """

    other = None

    try:
        other = requests.get(f"{url}/unum", verify=False, timeout=10).json()
    except Exception as exception:  # pylint: disable=broad-except
        flask_restx.abort(502, f"{url} did not answer who it is: {exception}")

    return other

def fetch(url, fingerprint):
    """
    What the unum at the url says it is, if the root it gives is the one with the fingerprint the person confirmed,
    and the server's certificate, which the second request does check, is from that root
    """

    url = url.rstrip("/")
    root = look(url)["root"]

    if trust.fingerprint(root) != fingerprint:
        flask_restx.abort(409, f"{url} has a root with fingerprint {trust.fingerprint(root)}, not {fingerprint}")

    other = None

    with tempfile.NamedTemporaryFile("w", suffix=".crt") as root_file:
        root_file.write(root)
        root_file.flush()

        try:
            other = requests.get(f"{url}/unum", verify=root_file.name, timeout=10).json()
        except Exception as exception:  # pylint: disable=broad-except
            flask_restx.abort(409, f"{url} is not served with a certificate from that root: {exception}")

    return other

def change(refs, unum, root=None):
    """
    Adds the root to the bundle in each secret, or takes out the roots named for the unum if there is none, and
    whether any changed
    """

    changed = False

    for ref in refs:
        bundle = trust.read(ref)
        after = trust.add(bundle, root) if root else trust.remove(bundle, unum)

        if after != bundle:
            trust.write(ref, after)
            changed = True

    return changed


class Unum(flask_restx.Resource):
    """
    Who this unum is, for another to join it
    """

    def get(self):
        """
        Its name, its root and the root's fingerprint, and the urls of its apps
        """

        with open(ROOT, "r", encoding="utf-8") as root_file:
            root = root_file.read()

        return {"unum": config()["unum"], "root": root, "fingerprint": trust.fingerprint(root), "apps": config().get("apps", {})}


class Lookup(flask_restx.Resource):
    """
    Finding out who a unum is before joining it
    """

    def post(self):
        """
        Asks the unum at the url who it is, for the person to confirm its fingerprint, and writes nothing
        """

        other = look((flask.request.json or {}).get("url", "").rstrip("/"))

        return {"unum": other["unum"], "fingerprint": trust.fingerprint(other["root"]), "apps": other.get("apps", {})}


class Follow(flask_restx.Resource):
    """
    Reading the records of another unum: a Route to its app, and its root to verify it with
    """

    def post(self):
        """
        Follows the unum at the url, if its root has the fingerprint, to the app it names, or the only one it has
        besides this one
        """

        body = flask.request.json or {}
        other = fetch(body.get("url", ""), body.get("fingerprint", ""))
        unum = other["unum"]

        apps = {app: url for app, url in other.get("apps", {}).items() if app != WHO}
        app = body.get("app") or (next(iter(apps)) if len(apps) == 1 else None)

        if app not in apps:
            flask_restx.abort(400, f"which of {sorted(apps)} to follow {unum} to?")

        changed = False
        routes = relations_unum.Route.many(holder=unum).retrieve()

        if routes:
            if routes[0].url != apps[app]:
                routes[0].url = apps[app]
                routes[0].update()
                changed = True
        else:
            relations_unum.Route(home=unum, role="owner", holder=unum, url=apps[app]).create()
            changed = True

        changed = change(config()["roots"], unum, other["root"]) or changed

        return {"unum": unum, "fingerprint": trust.fingerprint(other["root"]), "url": apps[app]}, 201 if changed else 200


class Followed(flask_restx.Resource):
    """
    A unum being read
    """

    def delete(self, unum):
        """
        Stops reading it: its Routes, and its roots
        """

        if unum == config()["unum"]:
            flask_restx.abort(400, f"{unum} is this unum")

        for route in relations_unum.Route.many(holder=unum).retrieve():
            route.delete()

        change(config()["roots"], unum)

        return {"unum": unum}


class Accept(flask_restx.Resource):
    """
    Letting another unum read this one's records: its root in what the ingress trusts
    """

    def get(self):
        """
        The unums whose roots it trusts, which includes this one
        """

        roots = trust.split(trust.read(config()["trusted"]))

        return {"accepted": [{"unum": trust.name(pem), "fingerprint": trust.fingerprint(pem)} for pem in roots]}

    def post(self):
        """
        Accepts the unum at the url, if its root has the fingerprint
        """

        body = flask.request.json or {}
        other = fetch(body.get("url", ""), body.get("fingerprint", ""))

        changed = change([config()["trusted"]], other["unum"], other["root"])

        return {"unum": other["unum"], "fingerprint": trust.fingerprint(other["root"])}, 201 if changed else 200


class Accepted(flask_restx.Resource):
    """
    A unum that may read this one's records
    """

    def delete(self, unum):
        """
        Revokes it: its roots out of what the ingress trusts, never leaving none
        """

        ref = config()["trusted"]

        if not trust.split(trust.remove(trust.read(ref), unum)):
            flask_restx.abort(409, f"{unum} is the last root, and the ingress would trust no one")

        change([ref], unum)

        return {"unum": unum}
