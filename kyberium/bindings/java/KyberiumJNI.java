/**
 * KyberiumJNI - Interface Java Native Interface pour Kyberium
 * 
 * Cette classe expose l'API Kyberium via JNI pour une intégration native
 * en Java, permettant d'utiliser les algorithmes post-quantiques directement
 * depuis des applications Java.
 * 
 * @author Kyberium Team
 * @version 1.0.0
 * @since 1.0.0
 */

public class KyberiumJNI {
    
    // Chargement de la bibliothèque native
    static {
        try {
            System.loadLibrary("kyberium_jni");
            System.out.println("Kyberium JNI library loaded successfully");
        } catch (UnsatisfiedLinkError e) {
            System.err.println("Failed to load Kyberium JNI library: " + e.getMessage());
            System.err.println("Please ensure the library is in the library path");
            throw e;
        }
    }
    
    // ============================================================================
    // MÉTHODES NATIVES - SESSION CLASSIQUE
    // ============================================================================
    
    /**
     * Initialise une nouvelle session cryptographique.
     * 
     * @return Clé publique générée pour cette session
     * @throws KyberiumException si l'initialisation échoue
     */
    public native byte[] initSession();
    
    /**
     * Initialise une session avec la clé publique d'un pair.
     * 
     * @param peerPublicKey Clé publique du pair
     * @return Ciphertext pour le handshake
     * @throws KyberiumException si l'initialisation échoue
     */
    public native byte[] initSessionWithPeer(byte[] peerPublicKey);
    
    /**
     * Complète le handshake côté répondeur.
     * 
     * @param ciphertext Ciphertext reçu de l'initiateur
     * @return true si le handshake réussit
     * @throws KyberiumException si le handshake échoue
     */
    public native boolean completeHandshake(byte[] ciphertext);
    
    /**
     * Chiffre un message avec la session active.
     * 
     * @param plaintext Message à chiffrer
     * @return Tableau contenant [ciphertext, nonce]
     * @throws KyberiumException si le chiffrement échoue
     */
    public native byte[][] encrypt(byte[] plaintext);
    
    /**
     * Chiffre un message avec des données authentifiées associées.
     * 
     * @param plaintext Message à chiffrer
     * @param aad Données authentifiées associées (peut être null)
     * @return Tableau contenant [ciphertext, nonce]
     * @throws KyberiumException si le chiffrement échoue
     */
    public native byte[][] encryptWithAAD(byte[] plaintext, byte[] aad);
    
    /**
     * Déchiffre un message avec la session active.
     * 
     * @param ciphertext Message chiffré
     * @param nonce Nonce utilisé pour le chiffrement
     * @return Message déchiffré
     * @throws KyberiumException si le déchiffrement échoue
     */
    public native byte[] decrypt(byte[] ciphertext, byte[] nonce);
    
    /**
     * Déchiffre un message avec des données authentifiées associées.
     * 
     * @param ciphertext Message chiffré
     * @param nonce Nonce utilisé pour le chiffrement
     * @param aad Données authentifiées associées (peut être null)
     * @return Message déchiffré
     * @throws KyberiumException si le déchiffrement échoue
     */
    public native byte[] decryptWithAAD(byte[] ciphertext, byte[] nonce, byte[] aad);
    
    // ============================================================================
    // MÉTHODES NATIVES - SIGNATURE
    // ============================================================================
    
    /**
     * Signe un message avec la clé privée locale.
     * 
     * @param message Message à signer
     * @return Signature du message
     * @throws KyberiumException si la signature échoue
     */
    public native byte[] sign(byte[] message);
    
    /**
     * Vérifie une signature avec la clé publique du pair.
     * 
     * @param message Message original
     * @param signature Signature à vérifier
     * @param publicKey Clé publique pour la vérification (null pour utiliser la clé du pair)
     * @return true si la signature est valide
     * @throws KyberiumException si la vérification échoue
     */
    public native boolean verify(byte[] message, byte[] signature, byte[] publicKey);
    
    // ============================================================================
    // MÉTHODES NATIVES - TRIPLE RATCHET
    // ============================================================================
    
    /**
     * Initialise le Triple Ratchet côté initiateur.
     * 
     * @param peerKemPublic Clé publique KEM du pair
     * @param peerSignPublic Clé publique de signature du pair
     * @return Message d'initialisation contenant les données nécessaires
     * @throws KyberiumException si l'initialisation échoue
     */
    public native TripleRatchetInitMessage initTripleRatchet(byte[] peerKemPublic, byte[] peerSignPublic);
    
    /**
     * Complète le Triple Ratchet côté répondeur.
     * 
     * @param kemCiphertext Ciphertext KEM reçu
     * @param kemSignature Signature reçue
     * @param peerSignPublic Clé publique de signature du pair
     * @return true si le handshake Triple Ratchet réussit
     * @throws KyberiumException si le handshake échoue
     */
    public native boolean completeTripleRatchetHandshake(byte[] kemCiphertext, byte[] kemSignature, byte[] peerSignPublic);
    
    /**
     * Chiffre un message avec le Triple Ratchet.
     * 
     * @param plaintext Message à chiffrer
     * @return Message chiffré avec métadonnées Triple Ratchet
     * @throws KyberiumException si le chiffrement échoue
     */
    public native TripleRatchetMessage tripleEncrypt(byte[] plaintext);
    
    /**
     * Chiffre un message avec le Triple Ratchet et des données authentifiées.
     * 
     * @param plaintext Message à chiffrer
     * @param aad Données authentifiées associées (peut être null)
     * @return Message chiffré avec métadonnées Triple Ratchet
     * @throws KyberiumException si le chiffrement échoue
     */
    public native TripleRatchetMessage tripleEncryptWithAAD(byte[] plaintext, byte[] aad);
    
    /**
     * Déchiffre un message avec le Triple Ratchet.
     * 
     * @param ciphertext Message chiffré
     * @param nonce Nonce utilisé
     * @param signature Signature du message
     * @param msgNum Numéro du message
     * @param peerSignPublic Clé publique de signature du pair
     * @return Message déchiffré
     * @throws KyberiumException si le déchiffrement échoue
     */
    public native byte[] tripleDecrypt(byte[] ciphertext, byte[] nonce, byte[] signature, int msgNum, byte[] peerSignPublic);
    
    /**
     * Déchiffre un message avec le Triple Ratchet et des données authentifiées.
     * 
     * @param ciphertext Message chiffré
     * @param nonce Nonce utilisé
     * @param signature Signature du message
     * @param msgNum Numéro du message
     * @param peerSignPublic Clé publique de signature du pair
     * @param aad Données authentifiées associées (peut être null)
     * @return Message déchiffré
     * @throws KyberiumException si le déchiffrement échoue
     */
    public native byte[] tripleDecryptWithAAD(byte[] ciphertext, byte[] nonce, byte[] signature, int msgNum, byte[] peerSignPublic, byte[] aad);
    
    // ============================================================================
    // MÉTHODES NATIVES - GESTION DES CLÉS
    // ============================================================================
    
    /**
     * Génère une nouvelle paire de clés KEM.
     * 
     * @return Paire de clés [publicKey, privateKey]
     * @throws KyberiumException si la génération échoue
     */
    public native byte[][] generateKemKeypair();
    
    /**
     * Génère une nouvelle paire de clés de signature.
     * 
     * @return Paire de clés [publicKey, privateKey]
     * @throws KyberiumException si la génération échoue
     */
    public native byte[][] generateSignatureKeypair();
    
    /**
     * Récupère la clé publique KEM locale.
     * 
     * @return Clé publique KEM
     * @throws KyberiumException si la clé n'est pas disponible
     */
    public native byte[] getKemPublicKey();
    
    /**
     * Récupère la clé publique de signature locale.
     * 
     * @return Clé publique de signature
     * @throws KyberiumException si la clé n'est pas disponible
     */
    public native byte[] getSignaturePublicKey();
    
    // ============================================================================
    // MÉTHODES NATIVES - UTILITAIRES
    // ============================================================================
    
    /**
     * Force le renouvellement des clés de session.
     * 
     * @return true si le renouvellement réussit
     * @throws KyberiumException si le renouvellement échoue
     */
    public native boolean rekey();
    
    /**
     * Récupère les informations sur l'algorithme utilisé.
     * 
     * @return Informations sur l'algorithme
     */
    public native String getAlgorithmInfo();
    
    /**
     * Récupère les statistiques de performance.
     * 
     * @return Statistiques de performance
     */
    public native PerformanceStats getPerformanceStats();
    
    /**
     * Nettoie les ressources utilisées par la session.
     */
    public native void cleanup();
    
    // ============================================================================
    // CLASSES INTERNES POUR LES STRUCTURES DE DONNÉES
    // ============================================================================
    
    /**
     * Message d'initialisation du Triple Ratchet.
     */
    public static class TripleRatchetInitMessage {
        public byte[] kemCiphertext;
        public byte[] kemSignature;
        public byte[] signPublicKey;
        
        public TripleRatchetInitMessage(byte[] kemCiphertext, byte[] kemSignature, byte[] signPublicKey) {
            this.kemCiphertext = kemCiphertext;
            this.kemSignature = kemSignature;
            this.signPublicKey = signPublicKey;
        }
    }
    
    /**
     * Message Triple Ratchet avec métadonnées.
     */
    public static class TripleRatchetMessage {
        public byte[] ciphertext;
        public byte[] nonce;
        public byte[] signature;
        public int msgNum;
        public byte[] signPublicKey;
        
        public TripleRatchetMessage(byte[] ciphertext, byte[] nonce, byte[] signature, int msgNum, byte[] signPublicKey) {
            this.ciphertext = ciphertext;
            this.nonce = nonce;
            this.signature = signature;
            this.msgNum = msgNum;
            this.signPublicKey = signPublicKey;
        }
    }
    
    /**
     * Statistiques de performance.
     */
    public static class PerformanceStats {
        public long totalEncryptions;
        public long totalDecryptions;
        public long totalSignatures;
        public long totalVerifications;
        public double avgEncryptionTime;
        public double avgDecryptionTime;
        public double avgSignatureTime;
        public double avgVerificationTime;
        
        public PerformanceStats(long totalEncryptions, long totalDecryptions, long totalSignatures, long totalVerifications,
                               double avgEncryptionTime, double avgDecryptionTime, double avgSignatureTime, double avgVerificationTime) {
            this.totalEncryptions = totalEncryptions;
            this.totalDecryptions = totalDecryptions;
            this.totalSignatures = totalSignatures;
            this.totalVerifications = totalVerifications;
            this.avgEncryptionTime = avgEncryptionTime;
            this.avgDecryptionTime = avgDecryptionTime;
            this.avgSignatureTime = avgSignatureTime;
            this.avgVerificationTime = avgVerificationTime;
        }
    }
    
    /**
     * Exception Kyberium pour les erreurs JNI.
     */
    public static class KyberiumException extends RuntimeException {
        public KyberiumException(String message) {
            super(message);
        }
        
        public KyberiumException(String message, Throwable cause) {
            super(message, cause);
        }
    }
} 