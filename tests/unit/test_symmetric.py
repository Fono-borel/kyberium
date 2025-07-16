import unittest
from kyberium.symmetric.aesgcm import AESGCMCipher
from kyberium.symmetric.chacha20 import ChaCha20Cipher
import os

class TestAESGCM(unittest.TestCase):
    def setUp(self):
        self.cipher = AESGCMCipher()
        self.test_key = os.urandom(32)  # 256 bits
        self.test_plaintext = b"Hello, Kyberium! This is a test message."
    
    def test_encrypt_decrypt_basic(self):
        """Test basique de chiffrement/déchiffrement AES-GCM."""
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce)
        self.assertEqual(self.test_plaintext, decrypted)
    
    def test_encrypt_decrypt_with_aad(self):
        """Test avec données authentifiées associées (AAD)."""
        aad = b"authenticated_data"
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key, associated_data=aad)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce, associated_data=aad)
        self.assertEqual(self.test_plaintext, decrypted)
    
    def test_encrypt_decrypt_with_custom_nonce(self):
        """Test avec un nonce personnalisé."""
        custom_nonce = os.urandom(12)
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key, nonce=custom_nonce)
        self.assertEqual(nonce, custom_nonce)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce)
        self.assertEqual(self.test_plaintext, decrypted)
    
    def test_multiple_encryptions(self):
        """Test de plusieurs chiffrements avec la même clé."""
        ciphertext1, nonce1 = self.cipher.encrypt(self.test_plaintext, self.test_key)
        ciphertext2, nonce2 = self.cipher.encrypt(self.test_plaintext, self.test_key)
        
        # Les nonces doivent être différents (aléatoires)
        self.assertNotEqual(nonce1, nonce2)
        # Les ciphertexts doivent être différents
        self.assertNotEqual(ciphertext1, ciphertext2)
        
        # Les deux doivent se déchiffrer correctement
        decrypted1 = self.cipher.decrypt(ciphertext1, self.test_key, nonce1)
        decrypted2 = self.cipher.decrypt(ciphertext2, self.test_key, nonce2)
        self.assertEqual(decrypted1, decrypted2)
    
    def test_invalid_key_size(self):
        """Test avec une taille de clé invalide."""
        with self.assertRaises(ValueError):
            AESGCMCipher(key_size=64)  # Taille invalide
    
    def test_invalid_key(self):
        """Test avec une clé invalide."""
        with self.assertRaises(ValueError):
            self.cipher.encrypt(self.test_plaintext, b"invalid_key")
    
    def test_invalid_nonce(self):
        """Test avec un nonce invalide."""
        with self.assertRaises(ValueError):
            self.cipher.encrypt(self.test_plaintext, self.test_key, nonce=b"invalid_nonce")
    
    def test_authentication_failure(self):
        """Test d'échec d'authentification."""
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key)
        
        # Modifier le ciphertext
        tampered_ciphertext = ciphertext[:-1] + b'\x00'
        
        with self.assertRaises(RuntimeError):
            self.cipher.decrypt(tampered_ciphertext, self.test_key, nonce)
    
    def test_wrong_aad(self):
        """Test avec des AAD incorrectes."""
        aad = b"correct_aad"
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key, associated_data=aad)
        
        with self.assertRaises(RuntimeError):
            self.cipher.decrypt(ciphertext, self.test_key, nonce, associated_data=b"wrong_aad")

    def test_empty_message(self):
        ciphertext, nonce = self.cipher.encrypt(b'', self.test_key)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce)
        self.assertEqual(b'', decrypted)

    def test_long_message(self):
        long_message = b'A' * 10000
        ciphertext, nonce = self.cipher.encrypt(long_message, self.test_key)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce)
        self.assertEqual(long_message, decrypted)

    def test_bitflip_ciphertext(self):
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key)
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF
        with self.assertRaises(Exception):
            self.cipher.decrypt(bytes(tampered), self.test_key, nonce)

    def test_bitflip_nonce(self):
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key)
        tampered = bytearray(nonce)
        tampered[0] ^= 0xFF
        with self.assertRaises(Exception):
            self.cipher.decrypt(ciphertext, self.test_key, bytes(tampered))

    def test_bitflip_aad(self):
        aad = b"authenticated_data"
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key, associated_data=aad)
        tampered = bytearray(aad)
        tampered[0] ^= 0xFF
        with self.assertRaises(Exception):
            self.cipher.decrypt(ciphertext, self.test_key, nonce, associated_data=bytes(tampered))


class TestChaCha20(unittest.TestCase):
    def setUp(self):
        self.cipher = ChaCha20Cipher()
        self.test_key = os.urandom(32)  # 256 bits
        self.test_plaintext = b"Hello, Kyberium! This is a test message."
    
    def test_encrypt_decrypt_basic(self):
        """Test basique de chiffrement/déchiffrement ChaCha20-Poly1305."""
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce)
        self.assertEqual(self.test_plaintext, decrypted)
    
    def test_encrypt_decrypt_with_aad(self):
        """Test avec données authentifiées associées (AAD)."""
        aad = b"authenticated_data"
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key, associated_data=aad)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce, associated_data=aad)
        self.assertEqual(self.test_plaintext, decrypted)
    
    def test_encrypt_decrypt_with_custom_nonce(self):
        """Test avec un nonce personnalisé."""
        custom_nonce = os.urandom(12)
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key, nonce=custom_nonce)
        self.assertEqual(nonce, custom_nonce)
        decrypted = self.cipher.decrypt(ciphertext, self.test_key, nonce)
        self.assertEqual(self.test_plaintext, decrypted)
    
    def test_multiple_encryptions(self):
        """Test de plusieurs chiffrements avec la même clé."""
        ciphertext1, nonce1 = self.cipher.encrypt(self.test_plaintext, self.test_key)
        ciphertext2, nonce2 = self.cipher.encrypt(self.test_plaintext, self.test_key)
        
        # Les nonces doivent être différents (aléatoires)
        self.assertNotEqual(nonce1, nonce2)
        # Les ciphertexts doivent être différents
        self.assertNotEqual(ciphertext1, ciphertext2)
        
        # Les deux doivent se déchiffrer correctement
        decrypted1 = self.cipher.decrypt(ciphertext1, self.test_key, nonce1)
        decrypted2 = self.cipher.decrypt(ciphertext2, self.test_key, nonce2)
        self.assertEqual(decrypted1, decrypted2)
    
    def test_invalid_key_size(self):
        """Test avec une taille de clé invalide."""
        with self.assertRaises(ValueError):
            ChaCha20Cipher(key_size=16)  # Taille invalide
    
    def test_invalid_key(self):
        """Test avec une clé invalide."""
        with self.assertRaises(ValueError):
            self.cipher.encrypt(self.test_plaintext, b"invalid_key")
    
    def test_invalid_nonce(self):
        """Test avec un nonce invalide."""
        with self.assertRaises(ValueError):
            self.cipher.encrypt(self.test_plaintext, self.test_key, nonce=b"invalid_nonce")
    
    def test_authentication_failure(self):
        """Test d'échec d'authentification."""
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key)
        
        # Modifier le ciphertext
        tampered_ciphertext = ciphertext[:-1] + b'\x00'
        
        with self.assertRaises(RuntimeError):
            self.cipher.decrypt(tampered_ciphertext, self.test_key, nonce)
    
    def test_wrong_aad(self):
        """Test avec des AAD incorrectes."""
        aad = b"correct_aad"
        ciphertext, nonce = self.cipher.encrypt(self.test_plaintext, self.test_key, associated_data=aad)
        
        with self.assertRaises(RuntimeError):
            self.cipher.decrypt(ciphertext, self.test_key, nonce, associated_data=b"wrong_aad")


if __name__ == '__main__':
    unittest.main()
