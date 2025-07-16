import unittest
import os
import time
from kyberium.api.session import SessionManager
from kyberium.ratchet.triple_ratchet import TripleRatchet
from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.kdf.sha3 import SHA3KDF
from kyberium.symmetric.aesgcm import AESGCMCipher

class TestTripleRatchetComprehensive(unittest.TestCase):
    """
    Tests complets pour le Triple Ratchet post-quantique.
    Vérifie que nous avons bien un Triple Ratchet (Double Ratchet + Authentification forte)
    et non un simple Double Ratchet.
    """
    
    def setUp(self):
        """Initialise les composants cryptographiques pour les tests."""
        self.kem = Kyber1024()
        self.signature = DilithiumSignature()
        self.kdf = SHA3KDF()
        self.symmetric = AESGCMCipher(key_size=32)
        
        # Générer les identités pour Alice et Bob
        self.alice_kem_pub, self.alice_kem_priv = self.kem.generate_keypair()
        self.bob_kem_pub, self.bob_kem_priv = self.kem.generate_keypair()
        self.alice_sign_pub, self.alice_sign_priv = self.signature.generate_keypair()
        self.bob_sign_pub, self.bob_sign_priv = self.signature.generate_keypair()

    def test_triple_ratchet_initialization(self):
        """
        Test que le Triple Ratchet s'initialise correctement avec tous ses composants.
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Vérifier que tous les composants sont présents
        self.assertIsNotNone(ratchet.kem)
        self.assertIsNotNone(ratchet.kdf)
        self.assertIsNotNone(ratchet.signature)
        self.assertIsNotNone(ratchet.symmetric)
        
        # Vérifier que les clés de signature sont générées
        self.assertIsNotNone(ratchet.own_sign_keypair)
        self.assertEqual(len(ratchet.own_sign_keypair), 2)  # (public, private)
        
        # Vérifier l'état initial
        self.assertFalse(ratchet.handshake_done)
        self.assertIsNone(ratchet.root_key)
        self.assertIsNone(ratchet.send_chain_key)
        self.assertIsNone(ratchet.recv_chain_key)

    def test_triple_ratchet_handshake_complete(self):
        """
        Test complet du handshake Triple Ratchet avec vérification des signatures.
        """
        # Créer deux instances de Triple Ratchet avec leurs clés KEM respectives
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.bob_kem_pub, self.bob_kem_priv)
        )
        
        # Alice initialise le handshake
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Vérifier que le message d'init contient tous les éléments nécessaires
        self.assertIn('kem_ciphertext', alice_init_msg)
        self.assertIn('kem_signature', alice_init_msg)
        self.assertIn('sign_public_key', alice_init_msg)
        
        # Vérifier que le handshake d'Alice est terminé
        self.assertTrue(alice_ratchet.handshake_done)
        self.assertIsNotNone(alice_ratchet.root_key)
        self.assertIsNotNone(alice_ratchet.send_chain_key)
        self.assertIsNotNone(alice_ratchet.recv_chain_key)
        
        # Bob complète le handshake
        bob_success = bob_ratchet.complete_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        self.assertTrue(bob_success)
        self.assertTrue(bob_ratchet.handshake_done)
        self.assertIsNotNone(bob_ratchet.root_key)
        self.assertIsNotNone(bob_ratchet.send_chain_key)
        self.assertIsNotNone(bob_ratchet.recv_chain_key)

    def test_triple_ratchet_bidirectional_communication(self):
        """
        Test de communication bidirectionnelle avec Triple Ratchet.
        Vérifie que les messages peuvent être échangés dans les deux sens.
        """
        # Initialiser les ratchets avec leurs clés KEM respectives
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.bob_kem_pub, self.bob_kem_priv)
        )
        
        # Handshake
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        bob_ratchet.complete_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Alice envoie un message à Bob
        alice_message = "Bonjour Bob, c'est Alice !".encode('utf-8')
        alice_encrypted = alice_ratchet.ratchet_encrypt(alice_message)
        
        # Bob déchiffre le message d'Alice
        bob_decrypted = bob_ratchet.ratchet_decrypt(
            ciphertext=alice_encrypted['ciphertext'],
            nonce=alice_encrypted['nonce'],
            signature=alice_encrypted['signature'],
            msg_num=alice_encrypted['msg_num'],
            peer_sign_public=alice_encrypted['sign_public_key']
        )
        self.assertEqual(bob_decrypted, alice_message)
        
        # Bob envoie une réponse à Alice
        bob_message = "Salut Alice, Bob à l'appareil !".encode('utf-8')
        bob_encrypted = bob_ratchet.ratchet_encrypt(bob_message)
        
        # Alice déchiffre la réponse de Bob
        alice_decrypted = alice_ratchet.ratchet_decrypt(
            ciphertext=bob_encrypted['ciphertext'],
            nonce=bob_encrypted['nonce'],
            signature=bob_encrypted['signature'],
            msg_num=bob_encrypted['msg_num'],
            peer_sign_public=bob_encrypted['sign_public_key']
        )
        self.assertEqual(alice_decrypted, bob_message)

    def test_triple_ratchet_key_rotation(self):
        """
        Test que les clés sont bien rotées à chaque message (aspect Double Ratchet).
        """
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.bob_kem_pub, self.bob_kem_priv)
        )
        
        # Handshake
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        bob_ratchet.complete_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Sauvegarder les clés initiales
        alice_initial_send_key = alice_ratchet.send_chain_key
        bob_initial_recv_key = bob_ratchet.recv_chain_key
        
        # Alice envoie un message
        message = "Test rotation de clés".encode('utf-8')
        encrypted = alice_ratchet.ratchet_encrypt(message)
        
        # Vérifier que la clé d'envoi d'Alice a changé
        self.assertNotEqual(alice_ratchet.send_chain_key, alice_initial_send_key)
        
        # Bob déchiffre le message
        bob_ratchet.ratchet_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        
        # Vérifier que la clé de réception de Bob a changé
        self.assertNotEqual(bob_ratchet.recv_chain_key, bob_initial_recv_key)

    def test_triple_ratchet_signature_verification(self):
        """
        Test que l'authentification forte fonctionne (aspect Triple Ratchet).
        """
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.bob_kem_pub, self.bob_kem_priv)
        )
        
        # Handshake
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        bob_ratchet.complete_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Alice envoie un message
        message = "Message authentifié".encode('utf-8')
        encrypted = alice_ratchet.ratchet_encrypt(message)
        
        # Test 1: Signature valide
        decrypted = bob_ratchet.ratchet_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        self.assertEqual(decrypted, message)
        
        # Test 2: Signature invalide
        bad_signature = encrypted['signature'][:-1] + b'\x00'
        with self.assertRaises(RuntimeError):
            bob_ratchet.ratchet_decrypt(
                ciphertext=encrypted['ciphertext'],
                nonce=encrypted['nonce'],
                signature=bad_signature,
                msg_num=encrypted['msg_num'],
                peer_sign_public=encrypted['sign_public_key']
            )
        
        # Test 3: Clé publique de signature invalide
        fake_sign_pub = os.urandom(len(encrypted['sign_public_key']))
        with self.assertRaises(RuntimeError):
            bob_ratchet.ratchet_decrypt(
                ciphertext=encrypted['ciphertext'],
                nonce=encrypted['nonce'],
                signature=encrypted['signature'],
                msg_num=encrypted['msg_num'],
                peer_sign_public=fake_sign_pub
            )

    def test_triple_ratchet_handshake_signature_failure(self):
        """
        Test d'échec de signature lors du handshake.
        """
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.bob_kem_pub, self.bob_kem_priv)
        )
        
        # Alice initialise le handshake
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Bob essaie de compléter avec une signature invalide
        bad_signature = alice_init_msg['kem_signature'][:-1] + b'\x00'
        with self.assertRaises(RuntimeError):
            bob_ratchet.complete_handshake(
                kem_ciphertext=alice_init_msg['kem_ciphertext'],
                kem_signature=bad_signature,
                peer_sign_public=alice_init_msg['sign_public_key']
            )

    def test_triple_ratchet_rekey_functionality(self):
        """
        Test de la fonction rekey() pour forcer le renouvellement des clés.
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Initialiser le ratchet
        ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Sauvegarder les clés avant rekey
        old_root_key = ratchet.root_key
        old_send_key = ratchet.send_chain_key
        old_recv_key = ratchet.recv_chain_key
        
        # Forcer le renouvellement
        success = ratchet.rekey()
        self.assertTrue(success)
        
        # Vérifier que les clés ont changé
        self.assertNotEqual(ratchet.root_key, old_root_key)
        self.assertNotEqual(ratchet.send_chain_key, old_send_key)
        self.assertNotEqual(ratchet.recv_chain_key, old_recv_key)

    def test_triple_ratchet_multiple_messages(self):
        """
        Test d'envoi de plusieurs messages consécutifs.
        """
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.bob_kem_pub, self.bob_kem_priv)
        )
        
        # Handshake
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        bob_ratchet.complete_handshake(
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
            # Alice chiffre
            encrypted = alice_ratchet.ratchet_encrypt(message)
            
            # Vérifier que le numéro de message est correct
            self.assertEqual(encrypted['msg_num'], i)
            
            # Bob déchiffre
            decrypted = bob_ratchet.ratchet_decrypt(
                ciphertext=encrypted['ciphertext'],
                nonce=encrypted['nonce'],
                signature=encrypted['signature'],
                msg_num=encrypted['msg_num'],
                peer_sign_public=encrypted['sign_public_key']
            )
            
            self.assertEqual(decrypted, message)

    def test_triple_ratchet_with_aad(self):
        """
        Test avec Associated Authenticated Data (AAD).
        """
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.bob_kem_pub, self.bob_kem_priv)
        )
        
        # Handshake
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        bob_ratchet.complete_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Message avec AAD
        message = "Message avec AAD".encode('utf-8')
        aad = "Données authentifiées".encode('utf-8')
        
        encrypted = alice_ratchet.ratchet_encrypt(message, aad=aad)
        decrypted = bob_ratchet.ratchet_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key'],
            aad=aad
        )
        
        self.assertEqual(decrypted, message)

    def test_triple_ratchet_error_handling(self):
        """
        Test de gestion des erreurs dans le Triple Ratchet.
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Test 1: Tentative de chiffrement sans handshake
        with self.assertRaises(RuntimeError):
            ratchet.ratchet_encrypt("Test".encode('utf-8'))
        
        # Test 2: Tentative de déchiffrement sans handshake
        with self.assertRaises(RuntimeError):
            ratchet.ratchet_decrypt(
                ciphertext=b"fake",
                nonce=b"fake",
                signature=b"fake",
                msg_num=0,
                peer_sign_public=b"fake"
            )

    def test_triple_ratchet_vs_double_ratchet_verification(self):
        """
        Test pour vérifier que nous avons bien un Triple Ratchet et non un Double Ratchet.
        Le Triple Ratchet doit inclure l'authentification forte en plus du Double Ratchet.
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Vérifier que nous avons les composants du Triple Ratchet
        self.assertIsNotNone(ratchet.signature)  # Authentification forte
        self.assertIsNotNone(ratchet.own_sign_keypair)  # Clés de signature
        # Correction : initialiser le ratchet avant de vérifier la clé publique du pair
        ratchet.initialize(peer_kem_public=self.bob_kem_pub, peer_sign_public=self.bob_sign_pub)
        self.assertIsNotNone(ratchet.peer_sign_public_key)  # Clé publique du pair
        
        # Vérifier que les méthodes incluent la signature
        alice_init_msg = ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Le message d'init doit contenir la signature (Triple Ratchet)
        self.assertIn('kem_signature', alice_init_msg)
        self.assertIn('sign_public_key', alice_init_msg)
        
        # Le chiffrement doit retourner la signature (Triple Ratchet)
        ratchet.handshake_done = True  # Simuler un handshake terminé
        encrypted = ratchet.ratchet_encrypt("Test".encode('utf-8'))
        self.assertIn('signature', encrypted)
        self.assertIn('sign_public_key', encrypted)

if __name__ == '__main__':
    unittest.main() 