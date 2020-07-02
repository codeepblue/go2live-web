from unittest import TestCase

from config import Configuration
from crypto import Crypto


class CryptoIntegTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.crypto = Crypto(Configuration())

    def test_hash(self):
        hash = self.crypto.hash("something")
        self.assertIsNotNone(hash)

    def test_hash_can_be_generated_twice(self):
        hash1 = self.crypto.hash("something")
        hash2 = self.crypto.hash("something")
        self.assertEqual(hash1, hash2)
