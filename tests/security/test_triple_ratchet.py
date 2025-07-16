import unittest
import kyberium.api as api
from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature

class TestTripleRatchetIntegration(unittest.TestCase):
    def setUp(self):
        # Générer les identités KEM et Signature pour Alice et Bob
        self.kem = Kyber1024()
        self.sig = DilithiumSignature()
        self.alice_kem_pub, self.alice_kem_priv = self.kem.generate_keypair()
        self.bob_kem_pub, self.bob_kem_priv = self.kem.generate_keypair()
        self.alice_sign_pub, self.alice_sign_priv = self.sig.generate_keypair()
        self.bob_sign_pub, self.bob_sign_priv = self.sig.generate_keypair()

    def test_triple_ratchet_exchange(self):
        """
        Test d'un échange complet Triple Ratchet entre Alice (initiatrice) et Bob (répondeur).
        """
        # --- Handshake initiateur (Alice) ---
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        # --- Handshake répondeur (Bob) ---
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        # --- Alice envoie un message sécurisé ---
        message = "Coucou Bob, Triple Ratchet !".encode('utf-8')
        encrypted = api.triple_encrypt(message)
        # --- Bob reçoit et déchiffre le message ---
        decrypted = api.triple_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        self.assertEqual(decrypted, message)

    def test_triple_ratchet_auth_failure(self):
        """
        Test d'échec de vérification de signature dans Triple Ratchet.
        """
        alice_init_msg = api.init_triple_ratchet(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        api.complete_triple_ratchet_handshake(
            kem_ciphertext=alice_init_msg['kem_ciphertext'],
            kem_signature=alice_init_msg['kem_signature'],
            peer_sign_public=alice_init_msg['sign_public_key']
        )
        message = "Message sécurisé".encode('utf-8')
        encrypted = api.triple_encrypt(message)
        # On modifie la signature pour provoquer un échec
        bad_signature = encrypted['signature'][:-1] + b'\x00'
        with self.assertRaises(Exception):
            api.triple_decrypt(
                ciphertext=encrypted['ciphertext'],
                nonce=encrypted['nonce'],
                signature=bad_signature,
                msg_num=encrypted['msg_num'],
                peer_sign_public=encrypted['sign_public_key']
            )

if __name__ == '__main__':
    unittest.main() 