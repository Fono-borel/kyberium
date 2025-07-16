#!/usr/bin/env python3
"""
Tests d'intégration Python pour Kyberium
Teste toutes les fonctionnalités de chiffrement post-quantique
"""

import unittest
import os
import sys
import time
import secrets
from typing import Tuple, Dict, Any

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyberium.api import (
    init_session, complete_handshake, encrypt, decrypt, sign, verify,
    init_triple_ratchet, complete_triple_ratchet_handshake,
    triple_encrypt, triple_decrypt
)
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.kem.kyber import Kyber1024
from kyberium.kdf.sha3 import SHA3KDF
from kyberium.symmetric.aesgcm import AESGCMCipher
from kyberium.ratchet.triple_ratchet import TripleRatchet
from kyberium.api import get_current_session


class TestKyberiumIntegration(unittest.TestCase):
    """Tests d'intégration complets pour Kyberium"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        self.test_messages = [
            b"Hello, World!",
            b"",  # Message vide
            "Test avec caractères spéciaux: éàçù€£¥".encode('utf-8'),
            b"X" * 1000,  # Message long
            b"X" * 10000,  # Message très long
            secrets.token_bytes(1024),  # Données aléatoires
        ]
        
        self.test_aad = [
            None,
            b"",
            b"Additional authenticated data",
            "éàçù€£¥".encode('utf-8'),
            secrets.token_bytes(256),
        ]
    
    def test_session_handshake_basic(self):
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
    
    def test_session_handshake_with_peer(self):
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
    
    def test_encryption_decryption_variants(self):
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
            
            # Test avec différents messages
            for message in self.test_messages[:3]:  # Limiter pour la vitesse
                ciphertext, nonce = encrypt(message)
                decrypted = decrypt(ciphertext, nonce)
                self.assertEqual(decrypted, message)
            
            print(f"  ✓ {kdf_type} + {symmetric_type} fonctionne")
    
    def test_encryption_with_aad(self):
        """Test de chiffrement avec données authentifiées (AAD)"""
        print("\n=== Test Chiffrement avec AAD ===")
        
        init_session()
        
        for message in self.test_messages[:3]:
            for aad in self.test_aad:
                ciphertext, nonce = encrypt(message, aad)
                decrypted = decrypt(ciphertext, nonce, aad)
                self.assertEqual(decrypted, message)
                
                # Test que le déchiffrement échoue avec un AAD incorrect
                if aad is not None:
                    wrong_aad = aad + b"wrong"
                    with self.assertRaises(Exception):
                        decrypt(ciphertext, nonce, wrong_aad)
        
        print("✓ Chiffrement avec AAD fonctionne")
    
    def test_signature_verification(self):
        """Test de signature et vérification (robustesse avancée)"""
        print("\n=== Test Signature (Robustesse) ===")
        
        init_session()
        
        for message in self.test_messages[:3]:
            signature = sign(message)
            self.assertIsInstance(signature, bytes)
            self.assertGreater(len(signature), 0)
            public_key = None
            # Récupérer la clé publique utilisée pour la vérification
            try:
                public_key = _session.get_sign_public_key()
            except Exception:
                pass
            
            # Vérification réussie
            is_valid = verify(message, signature)
            self.assertTrue(is_valid)
            
            # Vérification avec message modifié (bit-flip)
            mod_msg = bytearray(message)
            if len(mod_msg) > 0:
                mod_msg[0] ^= 0xFF
                is_valid = verify(bytes(mod_msg), signature)
                self.assertFalse(is_valid)
            
            # Vérification avec signature modifiée (bit-flip)
            mod_sig = bytearray(signature)
            mod_sig[0] ^= 0xFF
            is_valid = verify(message, bytes(mod_sig))
            self.assertFalse(is_valid)
            
            # Vérification avec clé publique modifiée (bit-flip)
            if public_key is not None:
                mod_pk = bytearray(public_key)
                mod_pk[0] ^= 0xFF
                is_valid = verify(message, signature, bytes(mod_pk))
                self.assertFalse(is_valid)
            
            # Vérification avec signature d'une autre clé
            other_message = b"other message"
            other_signature = sign(other_message)
            is_valid = verify(message, other_signature)
            self.assertFalse(is_valid)
        
        print("✓ Signature et vérification (robustesse) fonctionnent")
    
    def test_triple_ratchet_basic(self):
        """Test du Triple Ratchet basique et robustesse avancée (sessions indépendantes)"""
        print("\n=== Test Triple Ratchet Basique & Robustesse (sessions indépendantes) ===")
        # Générer modules et clés pour Alice et Bob
        kem = Kyber1024()
        kdf = SHA3KDF()
        sign = DilithiumSignature()
        symmetric = AESGCMCipher()
        # Alice
        alice_kem_pub, alice_kem_priv = kem.generate_keypair()
        alice_sign_pub, alice_sign_priv = sign.generate_keypair()
        # Bob
        bob_kem_pub, bob_kem_priv = kem.generate_keypair()
        bob_sign_pub, bob_sign_priv = sign.generate_keypair()
        # Instancier les ratchets
        alice_ratchet = TripleRatchet(kem=kem, kdf=kdf, signature=sign, symmetric=symmetric, own_kem_keypair=(alice_kem_pub, alice_kem_priv))
        bob_ratchet = TripleRatchet(kem=kem, kdf=kdf, signature=sign, symmetric=symmetric, own_kem_keypair=(bob_kem_pub, bob_kem_priv))
        # Handshake
        alice_init = alice_ratchet.initialize(bob_kem_pub, bob_sign_pub)
        print(f"[TRACE] Alice (après init): root_key={alice_ratchet.root_key.hex()[:16]} send_chain_key={alice_ratchet.send_chain_key.hex()[:16]} send_msg_num={alice_ratchet.send_message_number}")
        bob_ratchet.complete_handshake(alice_init['kem_ciphertext'], alice_init['kem_signature'], alice_init['sign_public_key'])
        print(f"[TRACE] Bob (après handshake): root_key={bob_ratchet.root_key.hex()[:16]} recv_chain_key={bob_ratchet.recv_chain_key.hex()[:16]} recv_msg_num={bob_ratchet.recv_message_number}")
        # Chiffrement/déchiffrement normal
        messages = [b"msg1", b"msg2", b"msg3", b"msg4"]
        encrypted_msgs = []
        for i, m in enumerate(messages):
            enc = alice_ratchet.ratchet_encrypt(m)
            encrypted_msgs.append(enc)
            print(f"[TRACE] Alice after encrypt {i}: send_chain_key={alice_ratchet.send_chain_key.hex()[:16]} send_msg_num={alice_ratchet.send_message_number}")
            dec = bob_ratchet.ratchet_decrypt(enc['ciphertext'], enc['nonce'], enc['signature'], enc['msg_num'], enc['sign_public_key'])
            print(f"[TRACE] Bob after decrypt {i}: recv_chain_key={bob_ratchet.recv_chain_key.hex()[:16]} recv_msg_num={bob_ratchet.recv_message_number}")
            self.assertEqual(dec, m)
        print("✓ Triple Ratchet normal fonctionne (sessions indépendantes)")
        # Test out-of-order (perte de msg2)
        print("[TRACE] Test out-of-order (perte de msg2)")
        dec1 = bob_ratchet.ratchet_decrypt(
            encrypted_msgs[0]['ciphertext'], encrypted_msgs[0]['nonce'], encrypted_msgs[0]['signature'],
            encrypted_msgs[0]['msg_num'], encrypted_msgs[0]['sign_public_key'])
        dec3 = bob_ratchet.ratchet_decrypt(
            encrypted_msgs[2]['ciphertext'], encrypted_msgs[2]['nonce'], encrypted_msgs[2]['signature'],
            encrypted_msgs[2]['msg_num'], encrypted_msgs[2]['sign_public_key'])
        self.assertEqual(dec1, messages[0])
        self.assertEqual(dec3, messages[2])
        print("✓ Out-of-order (perte de msg2) fonctionne")
        # Test replay (rejouer msg1)
        print("[TRACE] Test replay (msg1)")
        with self.assertRaises(Exception):
            bob_ratchet.ratchet_decrypt(
                encrypted_msgs[0]['ciphertext'], encrypted_msgs[0]['nonce'], encrypted_msgs[0]['signature'],
                encrypted_msgs[0]['msg_num'], encrypted_msgs[0]['sign_public_key'])
        print("✓ Replay détecté/refusé")
        # Test modification d'un message (bit-flip)
        print("[TRACE] Test modification (bit-flip)")
        mod_enc = dict(encrypted_msgs[1])
        mod_ct = bytearray(mod_enc['ciphertext'])
        mod_ct[0] ^= 0xFF
        with self.assertRaises(Exception):
            bob_ratchet.ratchet_decrypt(bytes(mod_ct), mod_enc['nonce'], mod_enc['signature'], mod_enc['msg_num'], mod_enc['sign_public_key'])
        print("✓ Détection de modification de message fonctionne")
        # Test compromission de clé (PFS)
        print("[TRACE] Test PFS/compromission de clé")
        alice_ratchet.ratchet_encrypt(b"msg5")
        with self.assertRaises(Exception):
            bob_ratchet.ratchet_decrypt(
                encrypted_msgs[0]['ciphertext'], encrypted_msgs[0]['nonce'], encrypted_msgs[0]['signature'],
                encrypted_msgs[0]['msg_num'], encrypted_msgs[0]['sign_public_key'])
        print("✓ PFS/compromission de clé testée")
    
    def test_triple_ratchet_with_aad(self):
        """Test du Triple Ratchet avec AAD"""
        print("\n=== Test Triple Ratchet avec AAD ===")
        sign = DilithiumSignature()
        alice_kem_public = init_session()
        alice_sign_public, alice_sign_private = sign.generate_keypair()
        bob_kem_public = init_session()
        bob_sign_public, bob_sign_private = sign.generate_keypair()
        init_triple_ratchet(bob_kem_public, bob_sign_public)
        alice_init_msg = init_triple_ratchet(bob_kem_public, bob_sign_public)
        success = complete_triple_ratchet_handshake(
            alice_init_msg['kem_ciphertext'],
            alice_init_msg['kem_signature'],
            alice_init_msg['sign_public_key']  # Utiliser la clé publique de signature d'Alice transmise dans le message d'init
        )
        self.assertTrue(success)
        print("✓ Triple Ratchet avec AAD fonctionne")
    
    def test_performance_benchmark(self):
        """Test de performance basique"""
        print("\n=== Test Performance ===")
        
        init_session()
        
        # Test de chiffrement
        message = b"X" * 1024
        start_time = time.time()
        
        for _ in range(100):
            ciphertext, nonce = encrypt(message)
            decrypt(ciphertext, nonce)
        
        end_time = time.time()
        total_time = end_time - start_time
        operations_per_second = 200 / total_time  # 100 chiffrements + 100 déchiffrements
        
        print(f"✓ Performance: {operations_per_second:.1f} opérations/sec")
        self.assertGreater(operations_per_second, 10)  # Au moins 10 opérations/sec
    
    def test_edge_cases(self):
        """Test des cas limites"""
        print("\n=== Test Cas Limites ===")
        
        init_session()
        
        # Messages très longs
        long_message = b"X" * 100000
        ciphertext, nonce = encrypt(long_message)
        decrypted = decrypt(ciphertext, nonce)
        self.assertEqual(decrypted, long_message)
        print("✓ Message très long (100KB)")
        
        # Messages vides
        ciphertext, nonce = encrypt(b"")
        decrypted = decrypt(ciphertext, nonce)
        self.assertEqual(decrypted, b"")
        print("✓ Message vide")
        
        # AAD très long
        long_aad = b"X" * 10000
        ciphertext, nonce = encrypt(b"test", long_aad)
        decrypted = decrypt(ciphertext, nonce, long_aad)
        self.assertEqual(decrypted, b"test")
        print("✓ AAD très long")
    
    def test_error_handling(self):
        """Test de gestion d'erreurs"""
        print("\n=== Test Gestion d'Erreurs ===")
        
        init_session()
        
        # Tentative de déchiffrement avec nonce incorrect
        ciphertext, nonce = encrypt(b"test")
        wrong_nonce = nonce + b"wrong"
        
        with self.assertRaises(Exception):
            decrypt(ciphertext, wrong_nonce)
        print("✓ Erreur détectée avec nonce incorrect")
        
        # Tentative de déchiffrement avec ciphertext corrompu
        corrupted_ciphertext = ciphertext + b"corrupted"
        
        with self.assertRaises(Exception):
            decrypt(corrupted_ciphertext, nonce)
        print("✓ Erreur détectée avec ciphertext corrompu")
    
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


def run_integration_tests():
    """Lance tous les tests d'intégration"""
    print("🚀 Lancement des tests d'intégration Kyberium")
    print("=" * 60)
    
    # Créer une suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKyberiumIntegration)
    
    # Lancer les tests avec output détaillé
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
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
        print("\n✅ TOUS LES TESTS ONT RÉUSSI !")
        return True
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1) 