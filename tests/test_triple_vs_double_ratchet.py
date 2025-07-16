# ============================================================================
#  Kyberium - Test Triple vs Double Ratchet
#  Copyright (C) 2025 RhaB17369
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ============================================================================

import unittest
import os
from kyberium.ratchet.triple_ratchet import TripleRatchet
from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.kdf.sha3 import SHA3KDF
from kyberium.symmetric.aesgcm import AESGCMCipher

class TestTripleVsDoubleRatchet(unittest.TestCase):
    """
    Tests spécifiques pour vérifier que nous avons bien un Triple Ratchet
    et non un simple Double Ratchet.
    
    Le Triple Ratchet = Double Ratchet + Authentification forte (signature)
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

    def test_triple_ratchet_has_signature_component(self):
        """
        Test que le Triple Ratchet inclut bien le composant de signature
        (ce qui le distingue du Double Ratchet).
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric
        )
        
        # Vérifier que le composant signature est présent
        self.assertIsNotNone(ratchet.signature)
        self.assertIsInstance(ratchet.signature, DilithiumSignature)
        
        # Vérifier que les clés de signature sont générées
        self.assertIsNotNone(ratchet.own_sign_keypair)
        self.assertEqual(len(ratchet.own_sign_keypair), 2)
        
        # Vérifier que la clé publique de signature du pair peut être définie
        self.assertIsNone(ratchet.peer_sign_public_key)  # Initialement None
        ratchet.peer_sign_public_key = self.bob_sign_pub
        self.assertEqual(ratchet.peer_sign_public_key, self.bob_sign_pub)

    def test_triple_ratchet_handshake_includes_signature(self):
        """
        Test que le handshake du Triple Ratchet inclut la signature
        (contrairement au Double Ratchet classique).
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Initialiser le handshake
        init_msg = ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Vérifier que le message d'init contient la signature (Triple Ratchet)
        self.assertIn('kem_signature', init_msg)
        self.assertIn('sign_public_key', init_msg)
        
        # Vérifier que la signature est valide
        signature_valid = self.signature.verify(
            init_msg['kem_ciphertext'],
            init_msg['kem_signature'],
            init_msg['sign_public_key']
        )
        self.assertTrue(signature_valid)

    def test_triple_ratchet_encryption_includes_signature(self):
        """
        Test que le chiffrement du Triple Ratchet inclut la signature
        (contrairement au Double Ratchet classique).
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
        
        # Chiffrer un message
        message = "Test Triple Ratchet".encode('utf-8')
        encrypted = ratchet.ratchet_encrypt(message)
        
        # Vérifier que le résultat contient la signature (Triple Ratchet)
        self.assertIn('signature', encrypted)
        self.assertIn('sign_public_key', encrypted)
        
        # Vérifier que la signature est valide
        signature_valid = self.signature.verify(
            encrypted['ciphertext'],
            encrypted['signature'],
            encrypted['sign_public_key']
        )
        self.assertTrue(signature_valid)

    def test_triple_ratchet_decryption_verifies_signature(self):
        """
        Test que le déchiffrement du Triple Ratchet vérifie la signature
        (contrairement au Double Ratchet classique).
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
        
        # Alice chiffre un message
        message = "Message avec signature".encode('utf-8')
        encrypted = alice_ratchet.ratchet_encrypt(message)
        
        # Test 1: Déchiffrement avec signature valide (doit réussir)
        decrypted = bob_ratchet.ratchet_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        self.assertEqual(decrypted, message)
        
        # Test 2: Déchiffrement avec signature invalide (doit échouer)
        bad_signature = encrypted['signature'][:-1] + b'\x00'
        with self.assertRaises(RuntimeError):
            bob_ratchet.ratchet_decrypt(
                ciphertext=encrypted['ciphertext'],
                nonce=encrypted['nonce'],
                signature=bad_signature,
                msg_num=encrypted['msg_num'],
                peer_sign_public=encrypted['sign_public_key']
            )

    def test_triple_ratchet_has_double_ratchet_features(self):
        """
        Test que le Triple Ratchet inclut bien les fonctionnalités du Double Ratchet
        (rotation des clés, Perfect Forward Secrecy).
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
        
        # Vérifier que les clés de chaîne sont présentes (Double Ratchet)
        self.assertIsNotNone(alice_ratchet.send_chain_key)
        self.assertIsNotNone(alice_ratchet.recv_chain_key)
        self.assertIsNotNone(bob_ratchet.send_chain_key)
        self.assertIsNotNone(bob_ratchet.recv_chain_key)
        
        # Vérifier que les compteurs de messages sont présents (Double Ratchet)
        self.assertEqual(alice_ratchet.send_message_number, 0)
        self.assertEqual(alice_ratchet.recv_message_number, 0)
        self.assertEqual(bob_ratchet.send_message_number, 0)
        self.assertEqual(bob_ratchet.recv_message_number, 0)
        
        # Vérifier la rotation des clés (Double Ratchet)
        alice_initial_send_key = alice_ratchet.send_chain_key
        bob_initial_recv_key = bob_ratchet.recv_chain_key
        
        # Alice envoie un message
        encrypted = alice_ratchet.ratchet_encrypt("Test".encode('utf-8'))
        
        # Vérifier que les clés ont changé (rotation)
        self.assertNotEqual(alice_ratchet.send_chain_key, alice_initial_send_key)
        self.assertEqual(alice_ratchet.send_message_number, 1)
        
        # Bob déchiffre
        bob_ratchet.ratchet_decrypt(
            ciphertext=encrypted['ciphertext'],
            nonce=encrypted['nonce'],
            signature=encrypted['signature'],
            msg_num=encrypted['msg_num'],
            peer_sign_public=encrypted['sign_public_key']
        )
        
        # Vérifier que les clés de Bob ont changé
        self.assertNotEqual(bob_ratchet.recv_chain_key, bob_initial_recv_key)
        self.assertEqual(bob_ratchet.recv_message_number, 1)

    def test_triple_ratchet_has_rekey_functionality(self):
        """
        Test que le Triple Ratchet inclut la fonctionnalité rekey du Double Ratchet.
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Initialiser
        ratchet.initialize(
            peer_kem_public=self.bob_kem_pub,
            peer_sign_public=self.bob_sign_pub
        )
        
        # Sauvegarder les clés
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

    def test_triple_ratchet_architecture_verification(self):
        """
        Test pour vérifier l'architecture complète du Triple Ratchet.
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Vérifier que nous avons TOUS les composants du Triple Ratchet
        components = {
            'kem': ratchet.kem,
            'kdf': ratchet.kdf,
            'signature': ratchet.signature,
            'symmetric': ratchet.symmetric
        }
        
        for name, component in components.items():
            self.assertIsNotNone(component, f"Composant {name} manquant")
        
        # Vérifier les états spécifiques au Triple Ratchet
        triple_ratchet_states = [
            'own_sign_keypair',
            'peer_sign_public_key',
            'handshake_done'
        ]
        
        for state in triple_ratchet_states:
            self.assertTrue(hasattr(ratchet, state), f"État {state} manquant")
        
        # Vérifier les états du Double Ratchet (inclus dans Triple Ratchet)
        double_ratchet_states = [
            'root_key',
            'send_chain_key',
            'recv_chain_key',
            'send_message_number',
            'recv_message_number',
            'skipped_message_keys'
        ]
        
        for state in double_ratchet_states:
            self.assertTrue(hasattr(ratchet, state), f"État {state} manquant")

    def test_triple_ratchet_vs_double_ratchet_summary(self):
        """
        Test de résumé pour confirmer que nous avons un Triple Ratchet.
        """
        ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=(self.alice_kem_pub, self.alice_kem_priv)
        )
        
        # Vérifier les composants du Double Ratchet
        has_double_ratchet = all([
            ratchet.kem is not None,           # Échange de clés
            ratchet.kdf is not None,           # Dérivation de clés
            ratchet.symmetric is not None,     # Chiffrement symétrique
            hasattr(ratchet, 'root_key'),      # Clé racine
            hasattr(ratchet, 'send_chain_key'), # Clés de chaîne
            hasattr(ratchet, 'recv_chain_key'),
            hasattr(ratchet, 'send_message_number'), # Compteurs
            hasattr(ratchet, 'recv_message_number'),
            hasattr(ratchet, 'rekey')          # Fonction rekey
        ])
        
        # Vérifier les composants supplémentaires du Triple Ratchet
        has_triple_ratchet_extra = all([
            ratchet.signature is not None,     # Signature
            hasattr(ratchet, 'own_sign_keypair'), # Clés de signature
            hasattr(ratchet, 'peer_sign_public_key'),
            hasattr(ratchet, 'handshake_done') # État du handshake
        ])
        
        # Confirmer que nous avons un Triple Ratchet
        self.assertTrue(has_double_ratchet, "Composants Double Ratchet manquants")
        self.assertTrue(has_triple_ratchet_extra, "Composants Triple Ratchet manquants")
        
        print("✅ Confirmation : Nous avons bien un Triple Ratchet")
        print("   - Double Ratchet : ✓ (rotation de clés + KDF)")
        print("   - Authentification forte : ✓ (signature post-quantique)")
        print("   - Gestion des identités : ✓ (clés de signature séparées)")

if __name__ == '__main__':
    unittest.main() 