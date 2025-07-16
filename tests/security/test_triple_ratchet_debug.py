import unittest
from kyberium.ratchet.triple_ratchet import TripleRatchet
from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.kdf.sha3 import SHA3KDF
from kyberium.symmetric.aesgcm import AESGCMCipher

class TestTripleRatchetDebug(unittest.TestCase):
    """
    Test de débogage pour identifier les problèmes de synchronisation.
    """
    
    def setUp(self):
        """Initialise les composants cryptographiques."""
        self.kem = Kyber1024()
        self.signature = DilithiumSignature()
        self.kdf = SHA3KDF()
        self.symmetric = AESGCMCipher(key_size=32)
        
        # Générer les identités
        self.alice_kem_pub, self.alice_kem_priv = self.kem.generate_keypair()
        self.bob_kem_pub, self.bob_kem_priv = self.kem.generate_keypair()
        self.alice_sign_pub, self.alice_sign_priv = self.signature.generate_keypair()
        self.bob_sign_pub, self.bob_sign_priv = self.signature.generate_keypair()

    def test_kem_exchange_simple(self):
        """
        Test simple de l'échange KEM pour vérifier que le problème n'est pas là.
        """
        # Alice encapsule avec la clé publique de Bob
        ciphertext, alice_shared_secret = self.kem.encapsulate(self.bob_kem_pub)
        
        # Bob décapsule avec sa clé privée
        bob_shared_secret = self.kem.decapsulate(ciphertext, self.bob_kem_priv)
        
        # Les secrets doivent être identiques
        self.assertEqual(alice_shared_secret, bob_shared_secret)
        print("✅ Échange KEM fonctionne correctement")

    def test_triple_ratchet_handshake_debug(self):
        """
        Test de débogage du handshake Triple Ratchet.
        """
        # Créer les ratchets
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric
        )
        
        print("=== Début du handshake ===")
        
        # Alice initialise
        print("Alice initialise avec la clé publique de Bob:", len(self.bob_kem_pub), "bytes")
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        print("Alice - root_key:", len(alice_ratchet.root_key) if alice_ratchet.root_key else "None")
        print("Alice - send_chain_key:", len(alice_ratchet.send_chain_key) if alice_ratchet.send_chain_key else "None")
        
        # Bob complète
        print("Bob complète le handshake")
        print("Bob - clé privée KEM:", len(self.bob_kem_priv), "bytes")
        print("Bob - ciphertext reçu:", len(alice_init_msg['kem_ciphertext']), "bytes")
        
        # Forcer Bob à utiliser la bonne clé privée
        bob_ratchet.DHs = (self.bob_kem_pub, self.bob_kem_priv)
        
        bob_success = bob_ratchet.complete_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        print("Bob - root_key:", len(bob_ratchet.root_key) if bob_ratchet.root_key else "None")
        print("Bob - recv_chain_key:", len(bob_ratchet.recv_chain_key) if bob_ratchet.recv_chain_key else "None")
        
        # Vérifier que les clés sont synchronisées
        if alice_ratchet.root_key and bob_ratchet.root_key:
            print("Alice root_key == Bob root_key:", alice_ratchet.root_key == bob_ratchet.root_key)
            print("Alice send_chain_key == Bob recv_chain_key:", alice_ratchet.send_chain_key == bob_ratchet.recv_chain_key)
        
        self.assertTrue(bob_success)

    def test_triple_ratchet_simple_encryption(self):
        """
        Test simple de chiffrement/déchiffrement après handshake corrigé.
        """
        # Créer les ratchets
        alice_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric
        )
        bob_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric
        )
        
        # Handshake avec correction
        alice_init_msg = alice_ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Forcer Bob à utiliser la bonne clé privée
        bob_ratchet.DHs = (self.bob_kem_pub, self.bob_kem_priv)
        
        bob_ratchet.complete_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        
        # Test de chiffrement/déchiffrement
        message = "Test simple".encode('utf-8')
        encrypted = alice_ratchet.ratchet_encrypt(message)
        
        decrypted = bob_ratchet.ratchet_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        
        self.assertEqual(decrypted, message)
        print("✅ Chiffrement/déchiffrement fonctionne après correction")

if __name__ == '__main__':
    unittest.main() 