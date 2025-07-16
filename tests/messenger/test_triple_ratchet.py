#!/usr/bin/env python3
"""
Test du Triple Ratchet pour vérifier la synchronisation des clés
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kyberium.api.session import SessionManager
from kyberium.kem.kyber import Kyber1024
from kyberium.signature.dilithium import DilithiumSignature

def test_triple_ratchet_synchronization():
    """Test de synchronisation du Triple Ratchet entre deux parties"""
    print("🔬 Test de synchronisation Triple Ratchet")
    print("=" * 50)
    
    # Générer les clés pour Alice et Bob
    kem = Kyber1024()
    signature = DilithiumSignature()
    
    alice_kem_pub, alice_kem_priv = kem.generate_keypair()
    bob_kem_pub, bob_kem_priv = kem.generate_keypair()
    alice_sign_pub, alice_sign_priv = signature.generate_keypair()
    bob_sign_pub, bob_sign_priv = signature.generate_keypair()
    
    print(f"✅ Clés générées:")
    print(f"   Alice KEM: {len(alice_kem_pub)} bytes")
    print(f"   Bob KEM: {len(bob_kem_pub)} bytes")
    print(f"   Alice Sign: {len(alice_sign_pub)} bytes")
    print(f"   Bob Sign: {len(bob_sign_pub)} bytes")
    
    # Créer les sessions
    alice_session = SessionManager(use_triple_ratchet=True)
    bob_session = SessionManager(use_triple_ratchet=True)
    
    # Injecter explicitement les paires de clés dans chaque session
    alice_session.own_keypair = (alice_kem_pub, alice_kem_priv)
    alice_session.own_sign_keypair = (alice_sign_pub, alice_sign_priv)
    bob_session.own_keypair = (bob_kem_pub, bob_kem_priv)
    bob_session.own_sign_keypair = (bob_sign_pub, bob_sign_priv)
    
    # Alice initie le handshake
    print("\n🔄 Alice initie le handshake...")
    alice_handshake = alice_session.triple_ratchet_init(bob_kem_pub, bob_sign_pub)
    print(f"   ✅ Handshake Alice généré: {len(alice_handshake['kem_ciphertext'])} bytes")
    
    # Bob complète le handshake
    print("🔄 Bob complète le handshake...")
    bob_success = bob_session.triple_ratchet_complete_handshake(
        alice_handshake['kem_ciphertext'],
        alice_handshake['kem_signature'],
        alice_handshake['sign_public_key']
    )
    print(f"   ✅ Handshake Bob: {'Succès' if bob_success else 'Échec'}")
    
    # Vérifier la synchronisation
    print("\n🔍 Vérification de la synchronisation...")
    print(f"   Alice handshake_done: {alice_session.triple_ratchet.handshake_done}")
    print(f"   Bob handshake_done: {bob_session.triple_ratchet.handshake_done}")
    print(f"   Alice root_key: {len(alice_session.triple_ratchet.root_key) if alice_session.triple_ratchet.root_key else 'None'} bytes")
    print(f"   Bob root_key: {len(bob_session.triple_ratchet.root_key) if bob_session.triple_ratchet.root_key else 'None'} bytes")
    
    # Test de chiffrement/déchiffrement
    print("\n📝 Test de chiffrement/déchiffrement...")
    test_message = "Salut Bob, c'est Alice !".encode('utf-8')
    
    # Alice chiffre
    alice_encrypted = alice_session.triple_ratchet_encrypt(test_message)
    print(f"   ✅ Alice chiffré: {len(alice_encrypted['ciphertext'])} bytes")
    
    # Bob déchiffre
    try:
        bob_decrypted = bob_session.triple_ratchet_decrypt(
            alice_encrypted['ciphertext'],
            alice_encrypted['nonce'],
            alice_encrypted['signature'],
            alice_encrypted['msg_num'],
            alice_encrypted['sign_public_key']
        )
        print(f"   ✅ Bob déchiffré: {bob_decrypted.decode()}")
        
        assert bob_decrypted == test_message
        print("🎉 SUCCÈS: Le Triple Ratchet fonctionne correctement !")
        return True
    except Exception as e:
        print(f"❌ ÉCHEC: Erreur de déchiffrement: {e}")
        return False

def test_message_exchange():
    """Test d'échange de messages bidirectionnel"""
    print("\n🔄 Test d'échange de messages bidirectionnel")
    print("=" * 50)
    
    # Générer les clés
    kem = Kyber1024()
    signature = DilithiumSignature()
    
    alice_kem_pub, alice_kem_priv = kem.generate_keypair()
    bob_kem_pub, bob_kem_priv = kem.generate_keypair()
    alice_sign_pub, alice_sign_priv = signature.generate_keypair()
    bob_sign_pub, bob_sign_priv = signature.generate_keypair()
    
    # Créer les sessions
    alice_session = SessionManager(use_triple_ratchet=True)
    bob_session = SessionManager(use_triple_ratchet=True)
    
    # Injecter explicitement les paires de clés dans chaque session
    alice_session.own_keypair = (alice_kem_pub, alice_kem_priv)
    alice_session.own_sign_keypair = (alice_sign_pub, alice_sign_priv)
    bob_session.own_keypair = (bob_kem_pub, bob_kem_priv)
    bob_session.own_sign_keypair = (bob_sign_pub, bob_sign_priv)
    
    # Handshake
    alice_handshake = alice_session.triple_ratchet_init(bob_kem_pub, bob_sign_pub)
    bob_session.triple_ratchet_complete_handshake(
        alice_handshake['kem_ciphertext'],
        alice_handshake['kem_signature'],
        alice_handshake['sign_public_key']
    )
    
    # Alice → Bob
    alice_msg = "Salut Bob !".encode('utf-8')
    alice_enc = alice_session.triple_ratchet_encrypt(alice_msg)
    bob_dec = bob_session.triple_ratchet_decrypt(
        alice_enc['ciphertext'],
        alice_enc['nonce'],
        alice_enc['signature'],
        alice_enc['msg_num'],
        alice_enc['sign_public_key']
    )
    print(f"✅ Alice → Bob: {bob_dec.decode()}")
    
    # Bob → Alice
    bob_msg = "Salut Alice !".encode('utf-8')
    bob_enc = bob_session.triple_ratchet_encrypt(bob_msg)
    alice_dec = alice_session.triple_ratchet_decrypt(
        bob_enc['ciphertext'],
        bob_enc['nonce'],
        bob_enc['signature'],
        bob_enc['msg_num'],
        bob_enc['sign_public_key']
    )
    print(f"✅ Bob → Alice: {alice_dec.decode()}")
    
    print("🎉 Échange bidirectionnel réussi !")

if __name__ == "__main__":
    print("🧪 Tests du Triple Ratchet Kyberium")
    print("=" * 50)
    
    # Test de synchronisation
    if test_triple_ratchet_synchronization():
        # Test d'échange de messages
        test_message_exchange()
        print("\n🎉 Tous les tests sont passés avec succès !")
    else:
        print("\n❌ Les tests ont échoué. Vérifiez l'implémentation du Triple Ratchet.")
        sys.exit(1) 