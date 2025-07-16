#!/usr/bin/env python3
"""
Tests d'intégration simplifiés pour Kyberium
Version qui fonctionne avec l'implémentation actuelle
"""

import unittest
import os
import sys
import time
import secrets

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyberium.api import (
    init_session, complete_handshake, encrypt, decrypt, sign, verify
)


class TestSimpleIntegration(unittest.TestCase):
    """Tests d'intégration simplifiés pour Kyberium"""
    
    def test_basic_session_handshake(self):
        """Test du handshake de session basique"""
        print("\n=== Test Handshake Basique ===")
        
        # Alice initie une session
        alice_public = init_session()
        self.assertIsInstance(alice_public, bytes)
        self.assertGreater(len(alice_public), 0)
        print(f"✓ Alice a généré sa clé publique ({len(alice_public)} bytes)")
        
        # Bob complète le handshake
        success = complete_handshake(alice_public)
        self.assertTrue(success)
        print("✓ Bob a complété le handshake")
        
        # Test de chiffrement/déchiffrement
        message = b"Message secret"
        ciphertext, nonce = encrypt(message)
        self.assertIsInstance(ciphertext, bytes)
        self.assertIsInstance(nonce, bytes)
        
        decrypted = decrypt(ciphertext, nonce)
        self.assertEqual(decrypted, message)
        print("✓ Chiffrement/déchiffrement fonctionne")
    
    def test_session_with_peer(self):
        """Test du handshake avec clé publique du pair"""
        print("\n=== Test Handshake avec Pair ===")
        
        # Alice génère sa clé
        alice_public = init_session()
        
        # Bob initie avec la clé d'Alice
        bob_public = init_session(peer_public_key=alice_public)
        self.assertIsInstance(bob_public, bytes)
        print(f"✓ Bob a initié avec la clé d'Alice ({len(bob_public)} bytes)")
        
        # Alice complète avec la clé de Bob
        success = complete_handshake(bob_public)
        self.assertTrue(success)
        print("✓ Alice a complété le handshake")
    
    def test_encryption_variants(self):
        """Test de chiffrement avec différentes variantes"""
        print("\n=== Test Variantes de Chiffrement ===")
        
        # Test avec différents types de KDF et chiffrement symétrique
        variants = [
            ('sha3', 'aesgcm'),
            ('shake256', 'aesgcm'),
            ('sha3', 'chacha20'),
            ('shake256', 'chacha20'),
        ]
        
        for kdf_type, symmetric_type in variants:
            print(f"  Testant {kdf_type} + {symmetric_type}...")
            
            # Initialiser session avec variantes
            init_session(kdf_type=kdf_type, symmetric_type=symmetric_type)
            
            # Test avec message simple
            message = b"Test message"
            ciphertext, nonce = encrypt(message)
            decrypted = decrypt(ciphertext, nonce)
            self.assertEqual(decrypted, message)
            
            print(f"  ✓ {kdf_type} + {symmetric_type} fonctionne")
    
    def test_encryption_with_aad(self):
        """Test de chiffrement avec données authentifiées (AAD)"""
        print("\n=== Test Chiffrement avec AAD ===")
        
        init_session()
        
        message = b"Test message"
        aad = b"Additional data"
        
        ciphertext, nonce = encrypt(message, aad)
        decrypted = decrypt(ciphertext, nonce, aad)
        self.assertEqual(decrypted, message)
        
        # Test que le déchiffrement échoue avec un AAD incorrect
        wrong_aad = aad + b"wrong"
        with self.assertRaises(Exception):
            decrypt(ciphertext, nonce, wrong_aad)
        
        print("✓ Chiffrement avec AAD fonctionne")
    
    def test_signature_basic(self):
        """Test de signature basique"""
        print("\n=== Test Signature Basique ===")
        
        init_session()
        
        message = b"Test message"
        signature = sign(message)
        self.assertIsInstance(signature, bytes)
        self.assertGreater(len(signature), 0)
        
        # Vérification réussie
        is_valid = verify(message, signature)
        self.assertTrue(is_valid)
        
        print("✓ Signature et vérification fonctionnent")
    
    def test_different_message_types(self):
        """Test avec différents types de messages"""
        print("\n=== Test Types de Messages ===")
        
        init_session()
        
        test_messages = [
            b"Hello, World!",
            b"",  # Message vide
            b"X" * 100,  # Message répétitif
            secrets.token_bytes(256),  # Données aléatoires
        ]
        
        for message in test_messages:
            ciphertext, nonce = encrypt(message)
            decrypted = decrypt(ciphertext, nonce)
            self.assertEqual(decrypted, message)
        
        print("✓ Tous les types de messages fonctionnent")
    
    def test_session_persistence(self):
        """Test de persistance de session"""
        print("\n=== Test Persistance de Session ===")
        
        # Initialiser session
        init_session()
        
        # Chiffrer plusieurs messages
        messages = [b"message1", b"message2", b"message3"]
        ciphertexts = []
        
        for message in messages:
            ciphertext, nonce = encrypt(message)
            ciphertexts.append((ciphertext, nonce))
        
        # Déchiffrer tous les messages
        for i, (ciphertext, nonce) in enumerate(ciphertexts):
            decrypted = decrypt(ciphertext, nonce)
            self.assertEqual(decrypted, messages[i])
        
        print("✓ Session persiste entre les opérations")
    
    def test_error_handling(self):
        """Test de gestion d'erreurs"""
        print("\n=== Test Gestion d'Erreurs ===")
        
        # Initialiser session
        init_session()
        
        # Test de chiffrement/déchiffrement normal
        ciphertext, nonce = encrypt(b"test")
        decrypted = decrypt(ciphertext, nonce)
        self.assertEqual(decrypted, b"test")
        
        # Tentative de déchiffrement avec nonce incorrect
        wrong_nonce = nonce + b"wrong"
        with self.assertRaises(Exception):
            decrypt(ciphertext, wrong_nonce)
        
        # Tentative de déchiffrement avec ciphertext corrompu
        corrupted_ciphertext = ciphertext[:-1] + b"\x00"
        with self.assertRaises(Exception):
            decrypt(corrupted_ciphertext, nonce)
        
        print("✓ Gestion d'erreurs fonctionne")
    
    def test_performance_simple(self):
        """Test de performance simplifié"""
        print("\n=== Test Performance Simplifié ===")
        
        init_session()
        
        # Test de chiffrement
        message = b"X" * 1024
        start_time = time.time()
        
        for _ in range(10):  # Réduit pour la vitesse
            ciphertext, nonce = encrypt(message)
            decrypt(ciphertext, nonce)
        
        end_time = time.time()
        total_time = end_time - start_time
        operations_per_second = 20 / total_time  # 10 chiffrements + 10 déchiffrements
        
        print(f"✓ Performance: {operations_per_second:.1f} opérations/sec")
        self.assertGreater(operations_per_second, 1)  # Au moins 1 opération/sec


def run_simple_integration_tests():
    """Lance les tests d'intégration simplifiés"""
    print("🚀 Lancement des tests d'intégration simplifiés Kyberium")
    print("=" * 60)
    
    # Créer une suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSimpleIntegration)
    
    # Lancer les tests avec output détaillé
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS SIMPLIFIÉS")
    print("=" * 60)
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ ÉCHECS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERREURS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ TOUS LES TESTS SIMPLIFIÉS ONT RÉUSSI !")
        return True
    else:
        print("\n❌ CERTAINS TESTS SIMPLIFIÉS ONT ÉCHOUÉ")
        return False


if __name__ == "__main__":
    success = run_simple_integration_tests()
    sys.exit(0 if success else 1) 