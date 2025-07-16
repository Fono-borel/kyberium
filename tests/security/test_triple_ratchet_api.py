import unittest
import os
import time
import kyberium.api as api
from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.api.session import SessionManager

class TestTripleRatchetAPI(unittest.TestCase):
    """
    Tests de l'API Triple Ratchet pour vérifier l'intégration complète.
    """
    
    def setUp(self):
        """Initialise les composants cryptographiques pour les tests."""
        self.kem = Kyber1024()
        self.signature = DilithiumSignature()
        
        # Générer les identités pour Alice et Bob
        self.alice_kem_pub, self.alice_kem_priv = self.kem.generate_keypair()
        self.bob_kem_pub, self.bob_kem_priv = self.kem.generate_keypair()
        self.alice_sign_pub, self.alice_sign_priv = self.signature.generate_keypair()
        self.bob_sign_pub, self.bob_sign_priv = self.signature.generate_keypair()

    def test_api_triple_ratchet_basic_flow(self):
        """
        Test du flux de base de l'API Triple Ratchet.
        """
        # Alice initialise le Triple Ratchet
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Vérifier la structure du message d'init
        self.assertIn('kem_ciphertext', alice_init_msg)
        self.assertIn('kem_signature', alice_init_msg)
        self.assertIn('sign_public_key', alice_init_msg)
        
        # Bob complète le handshake
        success = api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        self.assertTrue(success)
        
        # Alice envoie un message
        message = "Test API Triple Ratchet".encode('utf-8')
        encrypted = api.triple_encrypt(message)
        
        # Vérifier la structure du message chiffré
        self.assertIn('ciphertext', encrypted)
        self.assertIn('nonce', encrypted)
        self.assertIn('signature', encrypted)
        self.assertIn('msg_num', encrypted)
        self.assertIn('sign_public_key', encrypted)
        
        # Bob déchiffre le message
        decrypted = api.triple_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        
        self.assertEqual(decrypted, message)

    def test_api_triple_ratchet_bidirectional(self):
        """
        Test de communication bidirectionnelle via l'API.
        """
        # Initialiser les sessions
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Alice -> Bob
        alice_msg = "Alice à Bob".encode('utf-8')
        alice_encrypted = api.triple_encrypt(alice_msg)
        bob_decrypted = api.triple_decrypt(
            ciphertext=alice_encrypted['ciphertext'],
            nonce=alice_encrypted['nonce'],
            signature=alice_encrypted['signature'],
            msg_num=alice_encrypted['msg_num'],
            peer_sign_public=alice_encrypted['sign_public_key']
        )
        self.assertEqual(bob_decrypted, alice_msg)
        
        # Bob -> Alice (créer une nouvelle session pour Bob)
        bob_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.alice_kem_pub,
            peer_sign_public=self.alice_sign_pub
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=bob_init_msg['kem_ciphertext'],
            kem_signature=bob_init_msg['kem_signature'],
            peer_sign_public=bob_init_msg['sign_public_key']
        )
        
        bob_msg = "Bob à Alice".encode('utf-8')
        bob_encrypted = api.triple_encrypt(bob_msg)
        alice_decrypted = api.triple_decrypt(
            ciphertext=bob_encrypted['ciphertext'],
            nonce=bob_encrypted['nonce'],
            signature=bob_encrypted['signature'],
            msg_num=bob_encrypted['msg_num'],
            peer_sign_public=bob_encrypted['sign_public_key']
        )
        self.assertEqual(alice_decrypted, bob_msg)

    def test_api_triple_ratchet_multiple_messages(self):
        """
        Test d'envoi de plusieurs messages consécutifs via l'API.
        """
        # Initialiser
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Envoyer plusieurs messages
        messages = [
            "Message 1".encode('utf-8'),
            "Message 2".encode('utf-8'),
            "Message 3".encode('utf-8'),
            "Message 4".encode('utf-8'),
            "Message 5".encode('utf-8')
        ]
        
        for i, message in enumerate(messages):
            encrypted = api.triple_encrypt(message)
            self.assertEqual(encrypted['msg_num'], i)
            
            decrypted = api.triple_decrypt(
                ciphertext=encrypted['ciphertext'],
                nonce=encrypted['nonce'],
                signature=encrypted['signature'],
                msg_num=encrypted['msg_num'],
                peer_sign_public=encrypted['sign_public_key']
            )
            self.assertEqual(decrypted, message)

    def test_api_triple_ratchet_with_aad(self):
        """
        Test avec Associated Authenticated Data via l'API.
        """
        # Initialiser
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Message avec AAD
        message = "Message avec AAD".encode('utf-8')
        aad = "Données authentifiées".encode('utf-8')
        
        encrypted = api.triple_encrypt(message, aad=aad)
        decrypted = api.triple_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key'],
            aad=aad
        )
        
        self.assertEqual(decrypted, message)

    def test_api_triple_ratchet_different_algorithms(self):
        """
        Test avec différents algorithmes (SHAKE256, ChaCha20).
        """
        # Test avec SHAKE256
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub,
            kdf_type='shake256'
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key'],
            kdf_type='shake256'
        )
        
        message = "Test SHAKE256".encode('utf-8')
        encrypted = api.triple_encrypt(message)
        decrypted = api.triple_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        self.assertEqual(decrypted, message)
        
        # Test avec ChaCha20
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub,
            symmetric_type='chacha20'
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key'],
            symmetric_type='chacha20'
        )
        
        message = "Test ChaCha20".encode('utf-8')
        encrypted = api.triple_encrypt(message)
        decrypted = api.triple_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        self.assertEqual(decrypted, message)

    def test_api_triple_ratchet_error_handling(self):
        """
        Test de gestion des erreurs via l'API.
        """
        # Test 1: Tentative de chiffrement sans handshake
        with self.assertRaises(Exception):
            api.triple_encrypt("Test".encode('utf-8'))
        
        # Test 2: Tentative de déchiffrement sans handshake
        with self.assertRaises(Exception):
            api.triple_decrypt(
                ciphertext=b"fake",
                nonce=b"fake",
                signature=b"fake",
                msg_num=0,
                peer_sign_public=b"fake"
            )
        
        # Test 3: Signature invalide
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        encrypted = api.triple_encrypt("Test".encode('utf-8'))
        bad_signature = encrypted['signature'][:-1] + b'\x00'
        
        with self.assertRaises(Exception):
            api.triple_decrypt(
                ciphertext=encrypted['ciphertext'],
                nonce=encrypted['nonce'],
                signature=bad_signature,
                msg_num=encrypted['msg_num'],
                peer_sign_public=encrypted['sign_public_key']
            )

    def test_api_triple_ratchet_session_manager_integration(self):
        """
        Test d'intégration avec SessionManager.
        """
        # Créer un SessionManager avec Triple Ratchet
        session = api.SessionManager(use_triple_ratchet=True)
        
        # Initialiser le Triple Ratchet
        init_msg = session.triple_ratchet_init(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Vérifier que le Triple Ratchet est créé
        self.assertIsNotNone(session.triple_ratchet)
        self.assertTrue(session.use_triple_ratchet)
        
        # Compléter le handshake
        success = session.triple_ratchet_complete_handshake(
            kem_ciphertext=init_msg['kem_ciphertext'],
            kem_signature=init_msg['kem_signature'],
            peer_sign_public=init_msg['sign_public_key']
        )
        self.assertTrue(success)
        
        # Chiffrer et déchiffrer
        message = "Test SessionManager".encode('utf-8')
        encrypted = session.triple_ratchet_encrypt(message)
        decrypted = session.triple_ratchet_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        self.assertEqual(decrypted, message)

    def test_api_triple_ratchet_performance(self):
        """
        Test de performance basique pour le Triple Ratchet.
        """
        # Initialiser
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Mesurer le temps de chiffrement/déchiffrement
        message = "Test de performance".encode('utf-8')
        
        start_time = time.time()
        encrypted = api.triple_encrypt(message)
        encrypt_time = time.time() - start_time
        
        start_time = time.time()
        decrypted = api.triple_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        decrypt_time = time.time() - start_time
        
        self.assertEqual(decrypted, message)
        
        # Vérifier que les temps sont raisonnables (< 1 seconde)
        self.assertLess(encrypt_time, 1.0)
        self.assertLess(decrypt_time, 1.0)
        
        print(f"Temps de chiffrement: {encrypt_time:.4f}s")
        print(f"Temps de déchiffrement: {decrypt_time:.4f}s")

if __name__ == '__main__':
    unittest.main() 