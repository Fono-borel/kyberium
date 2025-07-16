# ============================================================================
#  Kyberium Secure Messenger - Debug Triple Ratchet
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

#!/usr/bin/env python3
"""
Débogage détaillé du Triple Ratchet pour identifier le problème de synchronisation
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kyberium.api.session import SessionManager
from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature

def debug_triple_ratchet():
    """Débogage détaillé du Triple Ratchet"""
    print("🔍 DÉBOGAGE DÉTAILLÉ DU TRIPLE RATCHET")
    print("=" * 60)
    
    # Générer les clés pour Alice et Bob
    kem = Kyber1024()
    signature = DilithiumSignature()
    
    alice_kem_pub, alice_kem_priv = kem.generate_keypair()
    bob_kem_pub, bob_kem_priv = kem.generate_keypair()
    alice_sign_pub, alice_sign_priv = signature.generate_keypair()
    bob_sign_pub, bob_sign_priv = signature.generate_keypair()
    
    print(f"✅ Clés générées:")
    print(f"   Alice KEM public: {len(alice_kem_pub)} bytes")
    print(f"   Alice KEM private: {len(alice_kem_priv)} bytes")
    print(f"   Bob KEM public: {len(bob_kem_pub)} bytes")
    print(f"   Bob KEM private: {len(bob_kem_priv)} bytes")
    
    # Créer les sessions
    alice_session = SessionManager(use_triple_ratchet=True)
    bob_session = SessionManager(use_triple_ratchet=True)
    
    # Configurer les clés
    alice_session.own_keypair = (alice_kem_pub, alice_kem_priv)
    alice_session.own_sign_keypair = (alice_sign_pub, alice_sign_priv)
    bob_session.own_keypair = (bob_kem_pub, bob_kem_priv)
    bob_session.own_sign_keypair = (bob_sign_pub, bob_sign_priv)
    
    print(f"\n🔍 Vérification des clés dans les sessions:")
    print(f"   Alice own_keypair: {alice_session.own_keypair is not None}")
    print(f"   Bob own_keypair: {bob_session.own_keypair is not None}")
    
    # Alice initie le handshake
    print(f"\n🔄 Alice initie le handshake...")
    alice_handshake = alice_session.triple_ratchet_init(bob_kem_pub, bob_sign_pub)
    print(f"   ✅ Handshake Alice généré: {len(alice_handshake['kem_ciphertext'])} bytes")
    
    # Vérifier l'état d'Alice après handshake
    print(f"\n🔍 État d'Alice après handshake:")
    print(f"   handshake_done: {alice_session.triple_ratchet.handshake_done}")
    print(f"   root_key: {len(alice_session.triple_ratchet.root_key) if alice_session.triple_ratchet.root_key else 'None'} bytes")
    print(f"   send_chain_key: {len(alice_session.triple_ratchet.send_chain_key) if alice_session.triple_ratchet.send_chain_key else 'None'} bytes")
    print(f"   recv_chain_key: {len(alice_session.triple_ratchet.recv_chain_key) if alice_session.triple_ratchet.recv_chain_key else 'None'} bytes")
    print(f"   DHs: {alice_session.triple_ratchet.DHs is not None}")
    print(f"   DHr: {alice_session.triple_ratchet.DHr is not None}")
    
    # Bob complète le handshake
    print(f"\n🔄 Bob complète le handshake...")
    bob_success = bob_session.triple_ratchet_complete_handshake(
        alice_handshake['kem_ciphertext'],
        alice_handshake['kem_signature'],
        alice_handshake['sign_public_key']
    )
    print(f"   ✅ Handshake Bob: {'Succès' if bob_success else 'Échec'}")
    
    # Vérifier l'état de Bob après handshake
    print(f"\n🔍 État de Bob après handshake:")
    print(f"   handshake_done: {bob_session.triple_ratchet.handshake_done}")
    print(f"   root_key: {len(bob_session.triple_ratchet.root_key) if bob_session.triple_ratchet.root_key else 'None'} bytes")
    print(f"   send_chain_key: {len(bob_session.triple_ratchet.send_chain_key) if bob_session.triple_ratchet.send_chain_key else 'None'} bytes")
    print(f"   recv_chain_key: {len(bob_session.triple_ratchet.recv_chain_key) if bob_session.triple_ratchet.recv_chain_key else 'None'} bytes")
    print(f"   DHs: {bob_session.triple_ratchet.DHs is not None}")
    print(f"   DHr: {bob_session.triple_ratchet.DHr is not None}")
    
    # Vérifier la synchronisation des clés
    print(f"\n🔍 Vérification de la synchronisation:")
    alice_root = alice_session.triple_ratchet.root_key
    bob_root = bob_session.triple_ratchet.root_key
    print(f"   root_key identique: {alice_root == bob_root}")
    print(f"   Alice root_key: {alice_root.hex()[:16]}..." if alice_root else "None")
    print(f"   Bob root_key: {bob_root.hex()[:16]}..." if bob_root else "None")
    
    # Test de chiffrement/déchiffrement avec débogage
    print(f"\n📝 Test de chiffrement/déchiffrement avec débogage...")
    test_message = "Salut Bob, c'est Alice !".encode('utf-8')
    
    # Alice chiffre
    print(f"   🔐 Alice chiffre le message...")
    alice_encrypted = alice_session.triple_ratchet_encrypt(test_message)
    print(f"   ✅ Alice chiffré: {len(alice_encrypted['ciphertext'])} bytes")
    print(f"   ✅ Alice nonce: {len(alice_encrypted['nonce'])} bytes")
    print(f"   ✅ Alice signature: {len(alice_encrypted['signature'])} bytes")
    print(f"   ✅ Alice msg_num: {alice_encrypted['msg_num']}")
    
    # Vérifier l'état d'Alice après chiffrement
    print(f"\n🔍 État d'Alice après chiffrement:")
    print(f"   send_chain_key: {len(alice_session.triple_ratchet.send_chain_key) if alice_session.triple_ratchet.send_chain_key else 'None'} bytes")
    print(f"   send_message_number: {alice_session.triple_ratchet.send_message_number}")
    
    # Bob déchiffre
    print(f"\n🔓 Bob déchiffre le message...")
    try:
        bob_decrypted = bob_session.triple_ratchet_decrypt(
            alice_encrypted['ciphertext'],
            alice_encrypted['nonce'],
            alice_encrypted['signature'],
            alice_encrypted['msg_num'],
            alice_encrypted['sign_public_key']
        )
        print(f"   ✅ Bob déchiffré: {bob_decrypted.decode()}")
        
        # Vérifier l'état de Bob après déchiffrement
        print(f"\n🔍 État de Bob après déchiffrement:")
        print(f"   recv_chain_key: {len(bob_session.triple_ratchet.recv_chain_key) if bob_session.triple_ratchet.recv_chain_key else 'None'} bytes")
        print(f"   recv_message_number: {bob_session.triple_ratchet.recv_message_number}")
        
        if bob_decrypted == test_message:
            print("🎉 SUCCÈS: Le Triple Ratchet fonctionne correctement !")
            return True
        else:
            print("❌ ÉCHEC: Les messages ne correspondent pas")
            return False
            
    except Exception as e:
        print(f"❌ ÉCHEC: Erreur de déchiffrement: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_triple_ratchet() 