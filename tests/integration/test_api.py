import unittest
import kyberium.api as api

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        pass

    def test_handshake_and_encryption(self):
        bob_pub = api.init_session()
        alice_ciphertext = api.init_session(peer_public_key=bob_pub)
        api.complete_handshake(alice_ciphertext)
        message = "Bonjour Bob, ici Alice !".encode('utf-8')
        ciphertext, nonce = api.encrypt(message)
        plaintext = api.decrypt(ciphertext, nonce)
        self.assertEqual(plaintext, message)

    def test_signature_and_verification(self):
        # Initialisation d'une session avec un vrai handshake
        bob_pub = api.init_session()
        alice_ciphertext = api.init_session(peer_public_key=bob_pub)
        api.complete_handshake(alice_ciphertext)
        message = "Message à signer".encode('utf-8')
        signature = api.sign(message)
        pub = api._session.get_sign_public_key()
        valid = api.verify(message, signature, public_key=pub)
        self.assertTrue(valid)

    def test_wrong_signature(self):
        # Initialisation d'une session avec un vrai handshake
        bob_pub = api.init_session()
        alice_ciphertext = api.init_session(peer_public_key=bob_pub)
        api.complete_handshake(alice_ciphertext)
        message = "Message à signer".encode('utf-8')
        signature = api.sign(message)
        bad_signature = signature[:-1] + b'\x00'
        pub = api._session.get_sign_public_key()
        valid = api.verify(message, bad_signature, public_key=pub)
        self.assertFalse(valid)

    def test_wrong_decryption(self):
        # Initialisation d'une session avec un vrai handshake
        bob_pub = api.init_session()
        alice_ciphertext = api.init_session(peer_public_key=bob_pub)
        api.complete_handshake(alice_ciphertext)
        message = "Test de chiffrement".encode('utf-8')
        ciphertext, nonce = api.encrypt(message)
        bad_nonce = nonce[:-1] + b'\x00'
        with self.assertRaises(Exception):
            api.decrypt(ciphertext, bad_nonce)

if __name__ == '__main__':
    unittest.main()
