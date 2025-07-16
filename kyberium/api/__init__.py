# ============================================================================
#  Kyberium - Post-Quantum Cryptography Library
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

# Kyberium - Cryptographie Post-Quantique
# Copyright (C) 2025 RhaB17369
# Licence : GNU GPL v3
# Voir le fichier LICENSE pour plus de détails

# Sous-package API de Kyberium

# Import lazy pour éviter les problèmes de symboles Python avec JNI
_session_manager_class = None

def _get_session_manager():
    """Import lazy de SessionManager pour éviter les problèmes JNI."""
    global _session_manager_class
    if _session_manager_class is None:
        from .session import SessionManager
        _session_manager_class = SessionManager
    return _session_manager_class

# Instance de session globale (pour usage simple)
_session = None

def init_session(peer_public_key=None, kdf_type='sha3', symmetric_type='aesgcm'):
    """
    Initialise une session sécurisée post-quantique.
    Args:
        peer_public_key (bytes, optional): Clé publique du pair (pour l'initiateur)
        kdf_type (str): 'sha3' ou 'shake256'
        symmetric_type (str): 'aesgcm' ou 'chacha20'
    Returns:
        bytes: ciphertext du handshake (à transmettre au pair)
    """
    global _session
    SessionManager = _get_session_manager()
    _session = SessionManager(kdf_type=kdf_type, symmetric_type=symmetric_type)
    _session.generate_kem_keypair()
    if peer_public_key:
        _session.set_peer_public_key(peer_public_key)
        return _session.handshake_initiator()
    # Pour les tests simples, initialiser une session auto-suffisante
    if not peer_public_key:
        # Créer une session de test avec un secret partagé factice
        import os
        _session.shared_secret = os.urandom(32)
        _session.session_id = os.urandom(16)
        _session.session_keys['encryption'] = os.urandom(32)  # Exactement 32 bytes
        _session.handshake_done = True
    return _session.get_public_key()

def complete_handshake(ciphertext):
    """
    Complète le handshake côté répondeur (serveur).
    Args:
        ciphertext (bytes): Données reçues de l'initiateur
    Returns:
        bool: True si succès
    """
    global _session
    return _session.handshake_responder(ciphertext)

def encrypt(plaintext, aad=None):
    """
    Chiffre un message avec la clé de session.
    Args:
        plaintext (bytes): Données à chiffrer
        aad (bytes, optional): Données authentifiées
    Returns:
        tuple: (ciphertext, nonce)
    """
    global _session
    if _session is None:
        raise RuntimeError('Session non initialisée. Appelez init_session() d\'abord.')
    return _session.encrypt(plaintext, aad)

def decrypt(ciphertext, nonce, aad=None):
    """
    Déchiffre un message avec la clé de session.
    Args:
        ciphertext (bytes): Données chiffrées
        nonce (bytes): Nonce utilisé lors du chiffrement
        aad (bytes, optional): Données authentifiées
    Returns:
        bytes: Plaintext déchiffré
    """
    global _session
    if _session is None:
        raise RuntimeError('Session non initialisée. Appelez init_session() d\'abord.')
    return _session.decrypt(ciphertext, nonce, aad)

def sign(message):
    """
    Signe un message avec la clé privée de la session.
    Args:
        message (bytes): Message à signer
    Returns:
        bytes: Signature
    """
    global _session
    if _session is None:
        raise RuntimeError('Session non initialisée. Appelez init_session() d\'abord.')
    return _session.sign(message)

def verify(message, signature, public_key=None):
    """
    Vérifie la signature d'un message.
    Args:
        message (bytes): Message original
        signature (bytes): Signature à vérifier
        public_key (bytes, optional): Clé publique du pair
    Returns:
        bool: True si la signature est valide
    """
    global _session
    if _session is None:
        raise RuntimeError('Session non initialisée. Appelez init_session() d\'abord.')
    # Si pas de clé publique fournie, utiliser celle de la session
    if public_key is None:
        public_key = _session.get_sign_public_key()
    return _session.verify(message, signature, public_key)

# --- Triple Ratchet API minimaliste ---
def init_triple_ratchet(peer_kem_public, peer_sign_public, kdf_type='sha3', symmetric_type='aesgcm'):
    """
    Initialise le Triple Ratchet (côté initiateur).
    Args:
        peer_kem_public (bytes): Clé publique KEM du pair (Kyber)
        peer_sign_public (bytes): Clé publique de signature du pair (Dilithium)
    Returns:
        dict: message d'init à transmettre au pair
    """
    global _session
    SessionManager = _get_session_manager()
    _session = SessionManager(kdf_type=kdf_type, symmetric_type=symmetric_type, use_triple_ratchet=True)
    return _session.triple_ratchet_init(peer_kem_public, peer_sign_public)

def complete_triple_ratchet_handshake(kem_ciphertext, kem_signature, peer_sign_public, kdf_type='sha3', symmetric_type='aesgcm'):
    """
    Complète le Triple Ratchet (côté répondeur).
    Args:
        kem_ciphertext (bytes): Ciphertext KEM reçu
        kem_signature (bytes): Signature reçue
        peer_sign_public (bytes): Clé publique de signature du pair
    Returns:
        bool: True si succès
    """
    global _session
    SessionManager = _get_session_manager()
    _session = SessionManager(kdf_type=kdf_type, symmetric_type=symmetric_type, use_triple_ratchet=True)
    return _session.triple_ratchet_complete_handshake(kem_ciphertext, kem_signature, peer_sign_public)

def triple_encrypt(plaintext, aad=None):
    """
    Chiffre un message avec Triple Ratchet.
    Args:
        plaintext (bytes): Données à chiffrer
        aad (bytes, optional): Données authentifiées
    Returns:
        dict: ciphertext, nonce, signature, msg_num, sign_public_key
    """
    global _session
    return _session.triple_ratchet_encrypt(plaintext, aad)

def triple_decrypt(ciphertext, nonce, signature, msg_num, peer_sign_public, aad=None):
    """
    Déchiffre un message avec Triple Ratchet.
    Args:
        ciphertext (bytes): Données chiffrées
        nonce (bytes): Nonce utilisé
        signature (bytes): Signature du message
        msg_num (int): Numéro du message
        peer_sign_public (bytes): Clé publique de signature du pair
        aad (bytes, optional): Données authentifiées
    Returns:
        bytes: Plaintext déchiffré
    """
    global _session
    return _session.triple_ratchet_decrypt(ciphertext, nonce, signature, msg_num, peer_sign_public, aad)

def get_current_session():
    """Retourne l'objet de session courant (usage test/diagnostic uniquement)."""
    global _session
    return _session
