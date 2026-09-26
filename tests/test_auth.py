import hashlib
import hmac
import json
import unittest
from unittest.mock import patch

import node


class Reply:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, *args):
        return json.dumps(self.body).encode()


class DeviceAuthTests(unittest.TestCase):
    def setUp(self):
        self.secret = "12" * 32
        self.client = node.Node({"hub": "https://example.invalid", "key": "fleet",
                                 "node_id": "a", "sign_key": self.secret})

    def test_auth_token_is_derived_and_different_for_each_device(self):
        expected = hmac.new(bytes.fromhex(self.secret), b"node-auth-v1:a", hashlib.sha256).hexdigest()
        self.assertEqual(self.client.auth_key, expected)
        other = node.Node({**self.client.cfg, "node_id": "b"})
        self.assertNotEqual(other.auth_key, expected)
        self.assertNotEqual(expected, self.secret)

    def test_post_sends_identity_without_signing_secret(self):
        with patch.object(node.urllib.request, "urlopen", return_value=Reply({"ok": True})) as open_:
            self.client._post("/api/hub/poll", self.client.hello(), 2)
        request = open_.call_args.args[0]
        self.assertEqual(request.get_header("X-node-key"), self.client.auth_key)
        self.assertEqual(request.get_header("X-node-id"), "a")
        self.assertNotIn(self.secret, str(request.headers))
        self.assertNotIn(self.secret.encode(), request.data)

    def test_enrollment_requires_personal_key(self):
        with patch.object(node.urllib.request, "urlopen", return_value=Reply({"key": "fleet"})):
            with self.assertRaises(SystemExit):
                node._enroll("https://example.invalid", "one-use", {"node_id": "a"})
        with patch.object(node.urllib.request, "urlopen", return_value=Reply({"key": "fleet", "sign_key": self.secret})):
            got = node._enroll("https://example.invalid", "one-use", {"node_id": "a"})
        self.assertEqual(got, {"key": "fleet", "sign_key": self.secret})

    def test_shared_auth_token_cannot_sign_command(self):
        cmd = {"id": 1, "node_id": "a", "kind": "run", "payload": {},
               "issued_at": 1, "expires_at": 100, "nonce": "test"}
        cmd["sig"] = hmac.new(bytes.fromhex(self.client.auth_key),
                              node._canon(1, "a", "run", {}, 1, 100, "test"), "sha256").hexdigest()
        self.assertFalse(node._verify(self.secret, cmd, "a", 10)[0])


if __name__ == "__main__":
    unittest.main()
