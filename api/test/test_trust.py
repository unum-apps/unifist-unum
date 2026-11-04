import base64
import datetime
import unittest
import unittest.mock

import cryptography.hazmat.primitives.asymmetric.ec
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.primitives.serialization
import cryptography.x509
import cryptography.x509.oid

import trust

def root(name):
    """
    A root certificate named for a unum, as PEM
    """

    key = cryptography.hazmat.primitives.asymmetric.ec.generate_private_key(cryptography.hazmat.primitives.asymmetric.ec.SECP256R1())
    subject = cryptography.x509.Name([cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, name)])
    now = datetime.datetime.now(datetime.timezone.utc)

    certificate = (
        cryptography.x509.CertificateBuilder()
        .subject_name(subject).issuer_name(subject).public_key(key.public_key())
        .serial_number(cryptography.x509.random_serial_number())
        .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(cryptography.x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, cryptography.hazmat.primitives.hashes.SHA256())
    )

    return certificate.public_bytes(cryptography.hazmat.primitives.serialization.Encoding.PEM).decode()


class TestBundle(unittest.TestCase):

    def setUp(self):

        self.us = root("us")
        self.them = root("them")
        self.cloud = root("cloud")

    def test_split(self):

        self.assertEqual(trust.split(""), [])
        self.assertEqual(trust.split(self.us), [self.us])
        self.assertEqual(trust.split(self.us + "\n" + self.them), [self.us, self.them])

    def test_name(self):

        self.assertEqual(trust.name(self.them), "them")

    def test_fingerprint(self):

        self.assertEqual(len(trust.fingerprint(self.us)), 64)
        self.assertEqual(trust.fingerprint(self.us), trust.fingerprint(self.us.strip()))
        self.assertNotEqual(trust.fingerprint(self.us), trust.fingerprint(self.them))

    def test_add(self):

        # Added after what is there

        self.assertEqual(trust.split(trust.add("", self.us)), [self.us])
        self.assertEqual(trust.split(trust.add(self.us, self.them)), [self.us, self.them])

        # Once, however many times

        bundle = trust.add(self.us, self.them)

        self.assertEqual(trust.add(bundle, self.them), bundle)

    def test_remove(self):

        bundle = trust.add(trust.add(self.us, self.them), self.cloud)

        # Every root with the name, the others kept in order

        self.assertEqual(trust.split(trust.remove(bundle, "them")), [self.us, self.cloud])

        again = trust.add(bundle, root("them"))

        self.assertEqual(trust.split(trust.remove(again, "them")), [self.us, self.cloud])

        # None named, nothing changes

        self.assertEqual(trust.remove(bundle, "away"), bundle)


class Missing(Exception):
    pass


class TestSecret(unittest.TestCase):

    def setUp(self):

        patcher = unittest.mock.patch("trust.pykube")
        self.pykube = patcher.start()
        self.addCleanup(patcher.stop)

        self.pykube.ObjectDoesNotExist = Missing
        self.secrets = self.pykube.Secret.objects.return_value.filter.return_value
        self.us = root("us")

    def test_read(self):

        # What the secret holds, decoded

        self.secrets.get_by_name.return_value.obj = {"data": {"ca.crt": base64.b64encode(self.us.encode()).decode()}}

        self.assertEqual(trust.read("traefik/trusted"), self.us)

        self.pykube.Secret.objects.return_value.filter.assert_called_once_with(namespace="traefik")
        self.secrets.get_by_name.assert_called_once_with("trusted")

        # Nothing if there is none, or it is empty

        self.secrets.get_by_name.return_value.obj = {"data": {}}

        self.assertEqual(trust.read("traefik/trusted"), "")

        self.secrets.get_by_name.side_effect = Missing

        self.assertEqual(trust.read("traefik/trusted"), "")

    def test_write(self):

        # Updated where it is

        secret = self.secrets.get_by_name.return_value
        secret.obj = {"data": {}}

        trust.write("cumulus/unum-roots", self.us)

        self.assertEqual(base64.b64decode(secret.obj["data"]["ca.crt"]).decode(), self.us)
        secret.update.assert_called_once_with()
        self.pykube.Secret.assert_not_called()

        # Made where it isn't

        self.secrets.get_by_name.side_effect = Missing

        trust.write("cumulus/unum-roots", self.us)

        made = self.pykube.Secret.call_args.args[1]

        self.assertEqual(made["metadata"], {"name": "unum-roots", "namespace": "cumulus"})
        self.assertEqual(base64.b64decode(made["data"]["ca.crt"]).decode(), self.us)
        self.pykube.Secret.return_value.create.assert_called_once_with()
