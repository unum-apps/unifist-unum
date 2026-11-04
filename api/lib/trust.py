"""
The roots a Unum trusts or verifies with, as a PEM bundle in the ca.crt of a Secret, read and written from inside the cluster
"""

import base64
import hashlib
import re

import cryptography.hazmat.primitives.serialization
import cryptography.x509
import cryptography.x509.oid
import pykube

PEM = re.compile(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.DOTALL)

def split(bundle):
    """
    The certificates in a bundle, each as PEM
    """

    return [pem + "\n" for pem in PEM.findall(bundle)]

def load(pem):
    """
    The certificate a PEM holds
    """

    return cryptography.x509.load_pem_x509_certificate(pem.encode())

def name(pem):
    """
    The common name of a certificate, which a Unum's root is named by
    """

    return load(pem).subject.get_attributes_for_oid(cryptography.x509.oid.NameOID.COMMON_NAME)[0].value

def fingerprint(pem):
    """
    The sha256 of a certificate, in hex, which the person joining a Unum confirms
    """

    return hashlib.sha256(load(pem).public_bytes(cryptography.hazmat.primitives.serialization.Encoding.DER)).hexdigest()

def add(bundle, pem):
    """
    The bundle with the certificate after the others, if it wasn't in it already
    """

    if fingerprint(pem) in [fingerprint(held) for held in split(bundle)]:
        return bundle

    return "".join(split(bundle) + split(pem))

def remove(bundle, unum):
    """
    The bundle without the roots named for the unum
    """

    return "".join(pem for pem in split(bundle) if name(pem) != unum)

def secrets(ref):
    """
    The Secrets in the namespace of ref, which is namespace/secret, and the name of the Secret
    """

    namespace, secret = ref.split("/")

    return pykube.Secret.objects(pykube.HTTPClient(pykube.KubeConfig.from_env())).filter(namespace=namespace), namespace, secret

def read(ref):
    """
    The bundle in the Secret, none if there is no Secret
    """

    objects, _, secret = secrets(ref)

    try:
        data = objects.get_by_name(secret).obj.get("data", {})
    except pykube.ObjectDoesNotExist:
        return ""

    return base64.b64decode(data.get("ca.crt", "")).decode()

def write(ref, bundle):
    """
    The Secret with the bundle in it, made if there is none
    """

    objects, namespace, secret = secrets(ref)
    encoded = base64.b64encode(bundle.encode()).decode()

    try:
        found = objects.get_by_name(secret)
    except pykube.ObjectDoesNotExist:
        pykube.Secret(pykube.HTTPClient(pykube.KubeConfig.from_env()), {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": secret, "namespace": namespace},
            "type": "Opaque",
            "data": {"ca.crt": encoded}
        }).create()
        return

    found.obj.setdefault("data", {})["ca.crt"] = encoded
    found.update()
