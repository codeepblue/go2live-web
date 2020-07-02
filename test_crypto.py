from unittest import TestCase
from unittest.mock import MagicMock

from crypto import Crypto


class CryptoTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()
        mocked_config = MagicMock()
        mocked_config.app_password_salt = "secret"
        self.crypto = Crypto(mocked_config)

    def test_hash(self):
        hash = self.crypto.hash("something")
        self.assertIsNotNone(hash)

    def test_hash_can_be_generated_twice(self):
        hash1 = self.crypto.hash("something")
        hash2 = self.crypto.hash("something")
        self.assertEqual(hash1, hash2)
