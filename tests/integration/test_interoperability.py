#!/usr/bin/env python3
"""
Test d'interopérabilité pour Kyberium
Vérifie que tous les modules fonctionnent ensemble
"""

import unittest
import os
import sys
import secrets

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.symmetric.aesgcm import AESGCM
from kyberium.symmetric.chacha20 import ChaCha20Poly1305
from kyberium.kdf.sha3 import SHA3KDF, SHAKE256KDF
from kyberium.ratchet.triple_ratchet import TripleRatchet


class TestInteroperability(unittest.TestCase):
    """Test d'interopérabilité entre tous les modules"""
    
    def test_kem_signature_integration(self):
        """Test d'intégration KEM + Signature"""
        print("\n=== Test KEM + Signature ===")
        
        # Générer clés KEM
        kem = Kyber1024()
        kem_public, kem_private = kem.generate_keypair()
        print(f"✓ Clés KEM générées ({len(kem_public)} bytes)")
        
        # Générer clés de signature
        sign = DilithiumSignature()
        sign_public, sign_private = sign.generate_keypair()
        print(f"✓ Clés de signature générées ({len(sign_public)} bytes)")
        
        # Encapsuler et signer
        ciphertext, shared_secret = kem.encapsulate(kem_public)
        signature = sign.sign(b"test message", sign_private)
        
        # Vérifier
        decapsulated = kem.decapsulate(ciphertext, kem_private)
        is_valid = sign.verify(b"test message", signature, sign_public)
        
        self.assertEqual(shared_secret, decapsulated)
        self.assertTrue(is_valid)
        print("✓ KEM + Signature fonctionnent ensemble")
    
    def test_symmetric_ciphers(self):
        """Test des chiffrements symétriques"""
        print("\n=== Test Chiffrements Symétriques ===")
        
        # Test AES-GCM
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        message = b"Test AES-GCM"
        
        aes = AESGCM(key)
        ciphertext = aes.encrypt(nonce, message, None)
        decrypted = aes.decrypt(nonce, ciphertext, None)
        
        self.assertEqual(decrypted, message)
        print("✓ AES-GCM fonctionne")
        
        # Test ChaCha20-Poly1305
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        message = b"Test ChaCha20"
        chacha = ChaCha20Poly1305(key)
        ciphertext = chacha.encrypt(nonce, message, None)
        decrypted = chacha.decrypt(nonce, ciphertext, None)
        
        self.assertEqual(decrypted, message)
        print("✓ ChaCha20-Poly1305 fonctionne")
    
    def test_kdf_integration(self):
        """Test d'intégration KDF"""
        print("\n=== Test KDF ===")
        
        # Test SHA3-KDF
        sha3_kdf = SHA3KDF()
        salt = secrets.token_bytes(32)
        info = b"test info"
        key_material = secrets.token_bytes(64)
        
        derived_key = sha3_kdf.derive_key(key_material, 32, salt, info)
        self.assertEqual(len(derived_key), 32)
        print("✓ SHA3-KDF fonctionne")
        
        # Test SHAKE256-KDF
        shake_kdf = SHAKE256KDF()
        derived_key = shake_kdf.derive_key(key_material, 32, salt, info)
        self.assertEqual(len(derived_key), 32)
        print("✓ SHAKE256-KDF fonctionne")
    
    def test_triple_ratchet(self):
        """Test du Triple Ratchet"""
        print("\n=== Test Triple Ratchet ===")
        
        # Initialiser deux ratchets avec leurs clés KEM et signature
        kem = Kyber1024()
        sign = DilithiumSignature()
        alice_kem_pub, alice_kem_priv = kem.generate_keypair()
        alice_sign_pub, alice_sign_priv = sign.generate_keypair()
        bob_kem_pub, bob_kem_priv = kem.generate_keypair()
        bob_sign_pub, bob_sign_priv = sign.generate_keypair()
        
        ratchet1 = TripleRatchet(own_kem_keypair=(alice_kem_pub, alice_kem_priv))
        ratchet1.initialize(bob_kem_pub, bob_sign_pub)
        ratchet2 = TripleRatchet(own_kem_keypair=(bob_kem_pub, bob_kem_priv))
        ratchet2.initialize(alice_kem_pub, alice_sign_pub)
        
        # Chiffrer avec ratchet1
        message = b"Test Triple Ratchet"
        encrypted = ratchet1.ratchet_encrypt(message)
        # Déchiffrer avec ratchet2
        decrypted = ratchet2.ratchet_decrypt(
            encrypted['ciphertext'],
            encrypted['nonce'],
            encrypted['signature'],
            encrypted['msg_num'],
            encrypted['sign_public_key']
        )
        self.assertEqual(decrypted, message)
        print("✓ Triple Ratchet fonctionne")
    
    def test_full_stack_integration(self):
        """Test d'intégration complète de la stack"""
        print("\n=== Test Stack Complète ===")
        
        # 1. Générer clés KEM et signature
        kem = Kyber1024()
        sign = DilithiumSignature()
        
        alice_kem_pub, alice_kem_priv = kem.generate_keypair()
        alice_sign_pub, alice_sign_priv = sign.generate_keypair()
        
        bob_kem_pub, bob_kem_priv = kem.generate_keypair()
        bob_sign_pub, bob_sign_priv = sign.generate_keypair()
        
        # 2. Échange de clés
        ciphertext, shared_secret = kem.encapsulate(bob_kem_pub)
        signature = sign.sign(ciphertext, alice_sign_priv)
        
        # 3. Vérification côté Bob
        decapsulated = kem.decapsulate(ciphertext, bob_kem_priv)
        is_valid = sign.verify(ciphertext, signature, alice_sign_pub)
        
        self.assertEqual(shared_secret, decapsulated)
        self.assertTrue(is_valid)
        
        # 4. Dérivation de clés
        kdf = SHA3KDF()
        encryption_key = kdf.derive_key(shared_secret, 32, b"salt", b"encryption")
        
        # 5. Chiffrement symétrique
        aes = AESGCM(encryption_key)
        nonce = secrets.token_bytes(12)
        message = b"Message secret"
        
        ciphertext = aes.encrypt(nonce, message, None)
        decrypted = aes.decrypt(nonce, ciphertext, None)
        
        self.assertEqual(decrypted, message)
        print("✓ Stack complète fonctionne")
    
    def test_error_handling_across_modules(self):
        """Test de gestion d'erreurs entre modules"""
        print("\n=== Test Gestion d'Erreurs ===")
        # Test avec clés incorrectes
        kem = Kyber1024()
        sign = DilithiumSignature()
        pub1, priv1 = kem.generate_keypair()
        pub2, priv2 = kem.generate_keypair()
        # Encapsuler avec une clé, décapsuler avec une autre
        ciphertext, secret1 = kem.encapsulate(pub1)
        # Kyber ne lève pas d'exception sur corruption, mais retourne un secret faux (fail-closed, NIST spec)
        secret2 = kem.decapsulate(ciphertext, priv2)
        self.assertNotEqual(secret1, secret2, "La décapsulation avec une mauvaise clé privée doit retourner un secret différent (fail-closed)")
        
        print("✓ Gestion d'erreurs fonctionne")


def run_interoperability_tests():
    """Lance les tests d'interopérabilité"""
    print("🔗 Lancement des tests d'interopérabilité Kyberium")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInteroperability)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ INTEROPÉRABILITÉ")
    print("=" * 60)
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ TOUS LES MODULES SONT INTEROPÉRABLES !")
        return True
    else:
        print("\n❌ PROBLÈMES D'INTEROPÉRABILITÉ DÉTECTÉS")
        return False


if __name__ == "__main__":
    success = run_interoperability_tests()
    sys.exit(0 if success else 1) 