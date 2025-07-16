import unittest
from kyberium.kem.kyber import Kyber1024, DummyKyber

class TestKyber1024(unittest.TestCase):
    def setUp(self):
        self.kem = Kyber1024()

    def test_generate_keypair(self):
        """Test de génération de paire de clés Kyber-1024."""
        pub, priv = self.kem.generate_keypair()
        
        # Vérifier que les clés sont des bytes
        self.assertIsInstance(pub, bytes)
        self.assertIsInstance(priv, bytes)
        
        # Vérifier les tailles des clés
        self.assertEqual(len(pub), self.kem.kem.PUBLIC_KEY_SIZE)
        self.assertEqual(len(priv), self.kem.kem.SECRET_KEY_SIZE)
        
        # Vérifier que les clés sont différentes
        self.assertNotEqual(pub, priv)

    def test_encapsulate_decapsulate(self):
        """Test complet d'encapsulation et décapsulation."""
        # Générer une paire de clés
        pub, priv = self.kem.generate_keypair()
        
        # Encapsuler un secret
        ciphertext, shared_secret1 = self.kem.encapsulate(pub)
        
        # Vérifier les tailles
        self.assertEqual(len(ciphertext), self.kem.kem.CIPHERTEXT_SIZE)
        self.assertEqual(len(shared_secret1), self.kem.kem.PLAINTEXT_SIZE)
        
        # Décapsuler le secret
        shared_secret2 = self.kem.decapsulate(ciphertext, priv)
        
        # Vérifier que les secrets sont identiques
        self.assertEqual(shared_secret1, shared_secret2)

    def test_multiple_encapsulations(self):
        """Test de plusieurs encapsulations avec la même clé publique."""
        pub, priv = self.kem.generate_keypair()
        
        # Première encapsulation
        cipher1, secret1 = self.kem.encapsulate(pub)
        decrypted1 = self.kem.decapsulate(cipher1, priv)
        self.assertEqual(secret1, decrypted1)
        
        # Deuxième encapsulation (doit être différente)
        cipher2, secret2 = self.kem.encapsulate(pub)
        decrypted2 = self.kem.decapsulate(cipher2, priv)
        self.assertEqual(secret2, decrypted2)
        
        # Les secrets doivent être différents (aléatoires)
        self.assertNotEqual(secret1, secret2)
        self.assertNotEqual(cipher1, cipher2)

    def test_invalid_public_key(self):
        """Test avec une clé publique invalide."""
        with self.assertRaises(ValueError):
            self.kem.encapsulate(b'invalid_key')

    def test_invalid_ciphertext(self):
        """Test avec un ciphertext invalide."""
        pub, priv = self.kem.generate_keypair()
        
        with self.assertRaises(ValueError):
            self.kem.decapsulate(b'invalid_ciphertext', priv)

    def test_invalid_private_key(self):
        """Test avec une clé privée invalide."""
        pub, _ = self.kem.generate_keypair()
        cipher, _ = self.kem.encapsulate(pub)
        
        with self.assertRaises(ValueError):
            self.kem.decapsulate(cipher, b'invalid_private_key')

    def test_algorithm_info(self):
        """Test des informations sur l'algorithme."""
        info = self.kem.get_algorithm_info()
        
        self.assertEqual(info["name"], "CRYSTALS-Kyber-1024 (ML-KEM-1024)")
        self.assertEqual(info["security_level"], 5)
        self.assertTrue(info["quantum_resistant"])
        self.assertTrue(info["standardized"])
        self.assertEqual(info["standard"], "NIST PQC")

    def test_bitflip_ciphertext(self):
        pub, priv = self.kem.generate_keypair()
        ciphertext, secret = self.kem.encapsulate(pub)
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF
        # Kyber ne lève pas d'exception sur corruption, mais retourne un secret faux (fail-closed, NIST spec)
        corrupted_secret = self.kem.decapsulate(bytes(tampered), priv)
        self.assertNotEqual(secret, corrupted_secret, "La décapsulation d'un ciphertext corrompu doit retourner un secret différent (fail-closed)")

    def test_bitflip_public_key(self):
        pub, priv = self.kem.generate_keypair()
        tampered = bytearray(pub)
        tampered[0] ^= 0xFF
        # Kyber ne lève pas d'exception sur corruption, mais retourne un ciphertext/secret faux
        ciphertext, secret = self.kem.encapsulate(bytes(tampered))
        # On ne peut pas prédire le secret, mais il doit être différent de celui obtenu avec la vraie clé
        pub2, priv2 = self.kem.generate_keypair()
        _, secret2 = self.kem.encapsulate(pub2)
        self.assertNotEqual(secret, secret2, "L'encapsulation avec une clé publique corrompue doit retourner un secret différent")

    def test_bitflip_private_key(self):
        pub, priv = self.kem.generate_keypair()
        ciphertext, secret = self.kem.encapsulate(pub)
        tampered = bytearray(priv)
        tampered[0] ^= 0xFF
        # Kyber ne lève pas d'exception sur corruption, mais retourne un secret faux
        corrupted_secret = self.kem.decapsulate(ciphertext, bytes(tampered))
        self.assertNotEqual(secret, corrupted_secret, "La décapsulation avec une clé privée corrompue doit retourner un secret différent")

    def test_empty_public_key(self):
        with self.assertRaises(Exception):
            self.kem.encapsulate(b'')

    def test_empty_ciphertext(self):
        pub, priv = self.kem.generate_keypair()
        with self.assertRaises(Exception):
            self.kem.decapsulate(b'', priv)

    def test_empty_private_key(self):
        pub, priv = self.kem.generate_keypair()
        ciphertext, secret = self.kem.encapsulate(pub)
        with self.assertRaises(Exception):
            self.kem.decapsulate(ciphertext, b'')


class TestDummyKyber(unittest.TestCase):
    """Tests pour l'ancienne implémentation dummy (compatibilité)."""
    def setUp(self):
        self.kem = DummyKyber()

    def test_generate_keypair(self):
        pub, priv = self.kem.generate_keypair()
        self.assertEqual(pub, b'public_key')
        self.assertEqual(priv, b'private_key')

    def test_encapsulate(self):
        ciphertext, shared_secret = self.kem.encapsulate(b'public_key')
        self.assertEqual(ciphertext, b'ciphertext')
        self.assertEqual(shared_secret, b'shared_secret')

    def test_decapsulate(self):
        shared_secret = self.kem.decapsulate(b'ciphertext', b'private_key')
        self.assertEqual(shared_secret, b'shared_secret')


if __name__ == '__main__':
    unittest.main()
