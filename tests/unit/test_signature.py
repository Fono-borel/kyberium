import unittest
from kyberium.signature.dilithium import DilithiumSignature

class TestDilithiumSignature(unittest.TestCase):
    def setUp(self):
        self.sig = DilithiumSignature()
        self.pub, self.priv = self.sig.generate_keypair()

    def test_generate_keypair(self):
        self.assertIsInstance(self.pub, bytes)
        self.assertIsInstance(self.priv, bytes)

    def test_sign_and_verify(self):
        message = b"kyberium test message"
        signature = self.sig.sign(message, self.priv)
        self.assertTrue(self.sig.verify(message, signature, self.pub))

    def test_bitflip_signature(self):
        message = b"kyberium test message"
        signature = self.sig.sign(message, self.priv)
        tampered = bytearray(signature)
        tampered[0] ^= 0xFF
        self.assertFalse(self.sig.verify(message, bytes(tampered), self.pub))

    def test_bitflip_message(self):
        message = b"kyberium test message"
        signature = self.sig.sign(message, self.priv)
        tampered = bytearray(message)
        tampered[0] ^= 0xFF
        self.assertFalse(self.sig.verify(bytes(tampered), signature, self.pub))

    def test_bitflip_public_key(self):
        message = b"kyberium test message"
        signature = self.sig.sign(message, self.priv)
        tampered = bytearray(self.pub)
        tampered[0] ^= 0xFF
        self.assertFalse(self.sig.verify(message, signature, bytes(tampered)))

    def test_empty_message(self):
        signature = self.sig.sign(b'', self.priv)
        self.assertTrue(self.sig.verify(b'', signature, self.pub))

if __name__ == '__main__':
    unittest.main()
