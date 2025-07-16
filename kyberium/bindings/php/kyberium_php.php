<?php
/**
 * Kyberium PHP Integration via FFI
 * 
 * Cette classe expose l'API Kyberium Python à PHP via FFI (Foreign Function Interface),
 * permettant d'utiliser les algorithmes post-quantiques directement depuis des
 * applications PHP avec des performances optimales.
 * 
 * @author Kyberium Team
 * @version 1.0.0
 * @since 1.0.0
 */

class KyberiumPHP {
    
    private $ffi;
    private $python_handle;
    private $kyberium_module;
    private $kyberium_api;
    private $performance_stats;
    
    /**
     * Constructeur - Initialise FFI et l'interpréteur Python
     */
    public function __construct() {
        // Vérifier que FFI est disponible
        if (!extension_loaded('ffi')) {
            throw new Exception('FFI extension is required for Kyberium PHP integration');
        }
        
        // Initialiser les statistiques de performance
        $this->performance_stats = [
            'total_encryptions' => 0,
            'total_decryptions' => 0,
            'total_signatures' => 0,
            'total_verifications' => 0,
            'avg_encryption_time' => 0.0,
            'avg_decryption_time' => 0.0,
            'avg_signature_time' => 0.0,
            'avg_verification_time' => 0.0
        ];
        
        // Charger la bibliothèque native
        $this->loadNativeLibrary();
        
        // Initialiser Python
        $this->initPython();
    }
    
    /**
     * Charge la bibliothèque native via FFI
     */
    private function loadNativeLibrary() {
        $ffi_def = '
        typedef void* PyObject;
        typedef void* PyInterpreterState;
        
        // Fonctions Python C API
        int Py_IsInitialized(void);
        void Py_Initialize(void);
        void Py_Finalize(void);
        PyObject* PyImport_ImportModule(const char* name);
        PyObject* PyObject_GetAttrString(PyObject* obj, const char* attr_name);
        PyObject* PyObject_CallMethod(PyObject* obj, const char* method, const char* format, ...);
        PyObject* PyObject_CallObject(PyObject* callable, PyObject* args);
        int PyObject_IsTrue(PyObject* obj);
        void Py_XDECREF(PyObject* obj);
        void Py_DECREF(PyObject* obj);
        
        // Fonctions pour la gestion des erreurs
        int PyErr_Occurred(void);
        void PyErr_Fetch(PyObject** type, PyObject** value, PyObject** traceback);
        PyObject* PyObject_Str(PyObject* obj);
        const char* PyUnicode_AsUTF8(PyObject* obj);
        
        // Fonctions pour les bytes
        PyObject* PyBytes_FromStringAndSize(const char* str, Py_ssize_t size);
        Py_ssize_t PyBytes_Size(PyObject* bytes);
        const char* PyBytes_AsString(PyObject* bytes);
        
        // Fonctions pour les tuples
        Py_ssize_t PyTuple_Size(PyObject* tuple);
        PyObject* PyTuple_GetItem(PyObject* tuple, Py_ssize_t index);
        
        // Fonctions pour les dictionnaires
        PyObject* PyDict_GetItemString(PyObject* dict, const char* key);
        
        // Fonctions pour les entiers
        long PyLong_AsLong(PyObject* obj);
        PyObject* PyLong_FromLong(long value);
        
        // Constantes
        PyObject* Py_None;
        int PyTuple_Check(PyObject* obj);
        int PyDict_Check(PyObject* obj);
        int PyBytes_Check(PyObject* obj);
        int PyLong_Check(PyObject* obj);
        ';
        
        $this->ffi = \FFI::cdef($ffi_def, 'libpython3.11.so');
    }
    
    /**
     * Initialise l'interpréteur Python et importe Kyberium
     */
    private function initPython() {
        // Initialiser Python si nécessaire
        if (!$this->ffi->Py_IsInitialized()) {
            $this->ffi->Py_Initialize();
        }
        
        // Importer le module Kyberium
        $this->kyberium_module = $this->ffi->PyImport_ImportModule('kyberium.api');
        if ($this->kyberium_module === null) {
            throw new Exception('Failed to import kyberium.api module');
        }
        
        // Récupérer l'objet API
        $this->kyberium_api = $this->ffi->PyObject_GetAttrString($this->kyberium_module, 'api');
        if ($this->kyberium_api === null) {
            throw new Exception('Failed to get kyberium.api.api object');
        }
    }
    
    /**
     * Convertit une chaîne PHP en objet Python bytes
     */
    private function stringToPythonBytes($string) {
        if ($string === null) {
            return $this->ffi->Py_None;
        }
        
        $length = strlen($string);
        return $this->ffi->PyBytes_FromStringAndSize($string, $length);
    }
    
    /**
     * Convertit un objet Python bytes en chaîne PHP
     */
    private function pythonBytesToString($pyBytes) {
        if ($pyBytes === null || $pyBytes === $this->ffi->Py_None) {
            return null;
        }
        
        $size = $this->ffi->PyBytes_Size($pyBytes);
        $data = $this->ffi->PyBytes_AsString($pyBytes);
        
        return \FFI::string($data, $size);
    }
    
    /**
     * Convertit un tuple Python en tableau PHP
     */
    private function pythonTupleToArray($pyTuple) {
        if ($pyTuple === null || !$this->ffi->PyTuple_Check($pyTuple)) {
            return null;
        }
        
        $size = $this->ffi->PyTuple_Size($pyTuple);
        $result = [];
        
        for ($i = 0; $i < $size; $i++) {
            $item = $this->ffi->PyTuple_GetItem($pyTuple, $i);
            $result[] = $this->pythonBytesToString($item);
        }
        
        return $result;
    }
    
    /**
     * Gère les erreurs Python et les convertit en exceptions PHP
     */
    private function handlePythonError($operation) {
        if ($this->ffi->PyErr_Occurred()) {
            $type = \FFI::addr($this->ffi->new('PyObject*'));
            $value = \FFI::addr($this->ffi->new('PyObject*'));
            $traceback = \FFI::addr($this->ffi->new('PyObject*'));
            
            $this->ffi->PyErr_Fetch($type, $value, $traceback);
            
            if ($value !== null) {
                $strValue = $this->ffi->PyObject_Str($value);
                $errorMsg = $this->ffi->PyUnicode_AsUTF8($strValue);
                $message = \FFI::string($errorMsg);
            } else {
                $message = $operation . ' failed';
            }
            
            $this->ffi->Py_XDECREF($type);
            $this->ffi->Py_XDECREF($value);
            $this->ffi->Py_XDECREF($traceback);
            
            throw new Exception('Kyberium error: ' . $message);
        }
    }
    
    /**
     * Mesure le temps d'exécution d'une opération
     */
    private function measureTime($startTime) {
        $endTime = microtime(true);
        return ($endTime - $startTime) * 1000.0; // en millisecondes
    }
    
    // ============================================================================
    // MÉTHODES PUBLIQUES - SESSION CLASSIQUE
    // ============================================================================
    
    /**
     * Initialise une nouvelle session cryptographique
     * 
     * @return string Clé publique générée pour cette session
     * @throws Exception si l'initialisation échoue
     */
    public function initSession() {
        $startTime = microtime(true);
        
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'init_session', null);
        if ($result === null) {
            $this->handlePythonError('init_session');
            return null;
        }
        
        $publicKey = $this->pythonBytesToString($result);
        $this->ffi->Py_XDECREF($result);
        
        $this->performance_stats['total_encryptions']++;
        $this->performance_stats['avg_encryption_time'] = $this->measureTime($startTime);
        
        return $publicKey;
    }
    
    /**
     * Initialise une session avec la clé publique d'un pair
     * 
     * @param string $peerPublicKey Clé publique du pair
     * @return string Ciphertext pour le handshake
     * @throws Exception si l'initialisation échoue
     */
    public function initSessionWithPeer($peerPublicKey) {
        $pyPeerKey = $this->stringToPythonBytes($peerPublicKey);
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'init_session', '(O)', $pyPeerKey);
        
        $this->ffi->Py_XDECREF($pyPeerKey);
        
        if ($result === null) {
            $this->handlePythonError('init_session_with_peer');
            return null;
        }
        
        $ciphertext = $this->pythonBytesToString($result);
        $this->ffi->Py_XDECREF($result);
        
        return $ciphertext;
    }
    
    /**
     * Complète le handshake côté répondeur
     * 
     * @param string $ciphertext Ciphertext reçu de l'initiateur
     * @return bool true si le handshake réussit
     * @throws Exception si le handshake échoue
     */
    public function completeHandshake($ciphertext) {
        $pyCiphertext = $this->stringToPythonBytes($ciphertext);
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'complete_handshake', '(O)', $pyCiphertext);
        
        $this->ffi->Py_XDECREF($pyCiphertext);
        
        if ($result === null) {
            $this->handlePythonError('complete_handshake');
            return false;
        }
        
        $success = $this->ffi->PyObject_IsTrue($result);
        $this->ffi->Py_XDECREF($result);
        
        return $success;
    }
    
    /**
     * Chiffre un message avec la session active
     * 
     * @param string $plaintext Message à chiffrer
     * @return array [ciphertext, nonce]
     * @throws Exception si le chiffrement échoue
     */
    public function encrypt($plaintext) {
        $startTime = microtime(true);
        
        $pyPlaintext = $this->stringToPythonBytes($plaintext);
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'encrypt', '(O)', $pyPlaintext);
        
        $this->ffi->Py_XDECREF($pyPlaintext);
        
        if ($result === null) {
            $this->handlePythonError('encrypt');
            return null;
        }
        
        $encrypted = $this->pythonTupleToArray($result);
        $this->ffi->Py_XDECREF($result);
        
        $this->performance_stats['total_encryptions']++;
        $this->performance_stats['avg_encryption_time'] = $this->measureTime($startTime);
        
        return $encrypted;
    }
    
    /**
     * Chiffre un message avec des données authentifiées associées
     * 
     * @param string $plaintext Message à chiffrer
     * @param string|null $aad Données authentifiées associées
     * @return array [ciphertext, nonce]
     * @throws Exception si le chiffrement échoue
     */
    public function encryptWithAAD($plaintext, $aad = null) {
        $pyPlaintext = $this->stringToPythonBytes($plaintext);
        $pyAAD = $this->stringToPythonBytes($aad);
        
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'encrypt', '(OO)', $pyPlaintext, $pyAAD);
        
        $this->ffi->Py_XDECREF($pyPlaintext);
        $this->ffi->Py_XDECREF($pyAAD);
        
        if ($result === null) {
            $this->handlePythonError('encrypt_with_aad');
            return null;
        }
        
        $encrypted = $this->pythonTupleToArray($result);
        $this->ffi->Py_XDECREF($result);
        
        return $encrypted;
    }
    
    /**
     * Déchiffre un message avec la session active
     * 
     * @param string $ciphertext Message chiffré
     * @param string $nonce Nonce utilisé pour le chiffrement
     * @return string Message déchiffré
     * @throws Exception si le déchiffrement échoue
     */
    public function decrypt($ciphertext, $nonce) {
        $startTime = microtime(true);
        
        $pyCiphertext = $this->stringToPythonBytes($ciphertext);
        $pyNonce = $this->stringToPythonBytes($nonce);
        
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'decrypt', '(OO)', $pyCiphertext, $pyNonce);
        
        $this->ffi->Py_XDECREF($pyCiphertext);
        $this->ffi->Py_XDECREF($pyNonce);
        
        if ($result === null) {
            $this->handlePythonError('decrypt');
            return null;
        }
        
        $decrypted = $this->pythonBytesToString($result);
        $this->ffi->Py_XDECREF($result);
        
        $this->performance_stats['total_decryptions']++;
        $this->performance_stats['avg_decryption_time'] = $this->measureTime($startTime);
        
        return $decrypted;
    }
    
    /**
     * Déchiffre un message avec des données authentifiées associées
     * 
     * @param string $ciphertext Message chiffré
     * @param string $nonce Nonce utilisé pour le chiffrement
     * @param string|null $aad Données authentifiées associées
     * @return string Message déchiffré
     * @throws Exception si le déchiffrement échoue
     */
    public function decryptWithAAD($ciphertext, $nonce, $aad = null) {
        $pyCiphertext = $this->stringToPythonBytes($ciphertext);
        $pyNonce = $this->stringToPythonBytes($nonce);
        $pyAAD = $this->stringToPythonBytes($aad);
        
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'decrypt', '(OOO)', $pyCiphertext, $pyNonce, $pyAAD);
        
        $this->ffi->Py_XDECREF($pyCiphertext);
        $this->ffi->Py_XDECREF($pyNonce);
        $this->ffi->Py_XDECREF($pyAAD);
        
        if ($result === null) {
            $this->handlePythonError('decrypt_with_aad');
            return null;
        }
        
        $decrypted = $this->pythonBytesToString($result);
        $this->ffi->Py_XDECREF($result);
        
        return $decrypted;
    }
    
    // ============================================================================
    // MÉTHODES PUBLIQUES - SIGNATURE
    // ============================================================================
    
    /**
     * Signe un message avec la clé privée locale
     * 
     * @param string $message Message à signer
     * @return string Signature du message
     * @throws Exception si la signature échoue
     */
    public function sign($message) {
        $startTime = microtime(true);
        
        $pyMessage = $this->stringToPythonBytes($message);
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'sign', '(O)', $pyMessage);
        
        $this->ffi->Py_XDECREF($pyMessage);
        
        if ($result === null) {
            $this->handlePythonError('sign');
            return null;
        }
        
        $signature = $this->pythonBytesToString($result);
        $this->ffi->Py_XDECREF($result);
        
        $this->performance_stats['total_signatures']++;
        $this->performance_stats['avg_signature_time'] = $this->measureTime($startTime);
        
        return $signature;
    }
    
    /**
     * Vérifie une signature avec la clé publique du pair
     * 
     * @param string $message Message original
     * @param string $signature Signature à vérifier
     * @param string|null $publicKey Clé publique pour la vérification
     * @return bool true si la signature est valide
     * @throws Exception si la vérification échoue
     */
    public function verify($message, $signature, $publicKey = null) {
        $startTime = microtime(true);
        
        $pyMessage = $this->stringToPythonBytes($message);
        $pySignature = $this->stringToPythonBytes($signature);
        $pyPublicKey = $this->stringToPythonBytes($publicKey);
        
        if ($publicKey === null) {
            $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'verify', '(OO)', $pyMessage, $pySignature);
        } else {
            $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'verify', '(OOO)', $pyMessage, $pySignature, $pyPublicKey);
        }
        
        $this->ffi->Py_XDECREF($pyMessage);
        $this->ffi->Py_XDECREF($pySignature);
        $this->ffi->Py_XDECREF($pyPublicKey);
        
        if ($result === null) {
            $this->handlePythonError('verify');
            return false;
        }
        
        $success = $this->ffi->PyObject_IsTrue($result);
        $this->ffi->Py_XDECREF($result);
        
        $this->performance_stats['total_verifications']++;
        $this->performance_stats['avg_verification_time'] = $this->measureTime($startTime);
        
        return $success;
    }
    
    // ============================================================================
    // MÉTHODES PUBLIQUES - TRIPLE RATCHET
    // ============================================================================
    
    /**
     * Initialise le Triple Ratchet côté initiateur
     * 
     * @param string $peerKemPublic Clé publique KEM du pair
     * @param string $peerSignPublic Clé publique de signature du pair
     * @return array Message d'initialisation
     * @throws Exception si l'initialisation échoue
     */
    public function initTripleRatchet($peerKemPublic, $peerSignPublic) {
        $pyKemPublic = $this->stringToPythonBytes($peerKemPublic);
        $pySignPublic = $this->stringToPythonBytes($peerSignPublic);
        
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'init_triple_ratchet', '(OO)', $pyKemPublic, $pySignPublic);
        
        $this->ffi->Py_XDECREF($pyKemPublic);
        $this->ffi->Py_XDECREF($pySignPublic);
        
        if ($result === null) {
            $this->handlePythonError('init_triple_ratchet');
            return null;
        }
        
        // Extraire les données du dictionnaire Python
        $kemCiphertext = $this->ffi->PyDict_GetItemString($result, 'kem_ciphertext');
        $kemSignature = $this->ffi->PyDict_GetItemString($result, 'kem_signature');
        $signPublicKey = $this->ffi->PyDict_GetItemString($result, 'sign_public_key');
        
        $initMessage = [
            'kem_ciphertext' => $this->pythonBytesToString($kemCiphertext),
            'kem_signature' => $this->pythonBytesToString($kemSignature),
            'sign_public_key' => $this->pythonBytesToString($signPublicKey)
        ];
        
        $this->ffi->Py_XDECREF($result);
        
        return $initMessage;
    }
    
    /**
     * Complète le Triple Ratchet côté répondeur
     * 
     * @param string $kemCiphertext Ciphertext KEM reçu
     * @param string $kemSignature Signature reçue
     * @param string $peerSignPublic Clé publique de signature du pair
     * @return bool true si le handshake Triple Ratchet réussit
     * @throws Exception si le handshake échoue
     */
    public function completeTripleRatchetHandshake($kemCiphertext, $kemSignature, $peerSignPublic) {
        $pyKemCiphertext = $this->stringToPythonBytes($kemCiphertext);
        $pyKemSignature = $this->stringToPythonBytes($kemSignature);
        $pyPeerSignPublic = $this->stringToPythonBytes($peerSignPublic);
        
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'complete_triple_ratchet_handshake', '(OOO)', 
                                                 $pyKemCiphertext, $pyKemSignature, $pyPeerSignPublic);
        
        $this->ffi->Py_XDECREF($pyKemCiphertext);
        $this->ffi->Py_XDECREF($pyKemSignature);
        $this->ffi->Py_XDECREF($pyPeerSignPublic);
        
        if ($result === null) {
            $this->handlePythonError('complete_triple_ratchet_handshake');
            return false;
        }
        
        $success = $this->ffi->PyObject_IsTrue($result);
        $this->ffi->Py_XDECREF($result);
        
        return $success;
    }
    
    /**
     * Chiffre un message avec le Triple Ratchet
     * 
     * @param string $plaintext Message à chiffrer
     * @return array Message chiffré avec métadonnées
     * @throws Exception si le chiffrement échoue
     */
    public function tripleEncrypt($plaintext) {
        $pyPlaintext = $this->stringToPythonBytes($plaintext);
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'triple_encrypt', '(O)', $pyPlaintext);
        
        $this->ffi->Py_XDECREF($pyPlaintext);
        
        if ($result === null) {
            $this->handlePythonError('triple_encrypt');
            return null;
        }
        
        // Extraire les données du dictionnaire Python
        $ciphertext = $this->ffi->PyDict_GetItemString($result, 'ciphertext');
        $nonce = $this->ffi->PyDict_GetItemString($result, 'nonce');
        $signature = $this->ffi->PyDict_GetItemString($result, 'signature');
        $msgNum = $this->ffi->PyDict_GetItemString($result, 'msg_num');
        $signPublicKey = $this->ffi->PyDict_GetItemString($result, 'sign_public_key');
        
        $encryptedMessage = [
            'ciphertext' => $this->pythonBytesToString($ciphertext),
            'nonce' => $this->pythonBytesToString($nonce),
            'signature' => $this->pythonBytesToString($signature),
            'msg_num' => $this->ffi->PyLong_AsLong($msgNum),
            'sign_public_key' => $this->pythonBytesToString($signPublicKey)
        ];
        
        $this->ffi->Py_XDECREF($result);
        
        return $encryptedMessage;
    }
    
    /**
     * Déchiffre un message avec le Triple Ratchet
     * 
     * @param string $ciphertext Message chiffré
     * @param string $nonce Nonce utilisé
     * @param string $signature Signature du message
     * @param int $msgNum Numéro du message
     * @param string $peerSignPublic Clé publique de signature du pair
     * @return string Message déchiffré
     * @throws Exception si le déchiffrement échoue
     */
    public function tripleDecrypt($ciphertext, $nonce, $signature, $msgNum, $peerSignPublic) {
        $pyCiphertext = $this->stringToPythonBytes($ciphertext);
        $pyNonce = $this->stringToPythonBytes($nonce);
        $pySignature = $this->stringToPythonBytes($signature);
        $pyMsgNum = $this->ffi->PyLong_FromLong($msgNum);
        $pyPeerSignPublic = $this->stringToPythonBytes($peerSignPublic);
        
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'triple_decrypt', '(OOOOO)', 
                                                 $pyCiphertext, $pyNonce, $pySignature, $pyMsgNum, $pyPeerSignPublic);
        
        $this->ffi->Py_XDECREF($pyCiphertext);
        $this->ffi->Py_XDECREF($pyNonce);
        $this->ffi->Py_XDECREF($pySignature);
        $this->ffi->Py_XDECREF($pyMsgNum);
        $this->ffi->Py_XDECREF($pyPeerSignPublic);
        
        if ($result === null) {
            $this->handlePythonError('triple_decrypt');
            return null;
        }
        
        $decrypted = $this->pythonBytesToString($result);
        $this->ffi->Py_XDECREF($result);
        
        return $decrypted;
    }
    
    // ============================================================================
    // MÉTHODES PUBLIQUES - UTILITAIRES
    // ============================================================================
    
    /**
     * Force le renouvellement des clés de session
     * 
     * @return bool true si le renouvellement réussit
     * @throws Exception si le renouvellement échoue
     */
    public function rekey() {
        $result = $this->ffi->PyObject_CallMethod($this->kyberium_api, 'rekey', null);
        if ($result === null) {
            $this->handlePythonError('rekey');
            return false;
        }
        
        $success = $this->ffi->PyObject_IsTrue($result);
        $this->ffi->Py_XDECREF($result);
        
        return $success;
    }
    
    /**
     * Récupère les informations sur l'algorithme utilisé
     * 
     * @return string Informations sur l'algorithme
     */
    public function getAlgorithmInfo() {
        return "Kyberium Post-Quantum Cryptography\n" .
               "- KEM: CRYSTALS-Kyber-1024 (ML-KEM-1024)\n" .
               "- Signature: CRYSTALS-Dilithium\n" .
               "- Symmetric: AES-256-GCM/ChaCha20-Poly1305\n" .
               "- KDF: SHA-3/SHAKE-256\n" .
               "- Security: NIST Level 5 (Post-Quantum)";
    }
    
    /**
     * Récupère les statistiques de performance
     * 
     * @return array Statistiques de performance
     */
    public function getPerformanceStats() {
        return $this->performance_stats;
    }
    
    /**
     * Nettoie les ressources utilisées par la session
     */
    public function cleanup() {
        // Nettoyer les ressources Python
        if ($this->kyberium_api !== null) {
            $this->ffi->Py_XDECREF($this->kyberium_api);
            $this->kyberium_api = null;
        }
        
        if ($this->kyberium_module !== null) {
            $this->ffi->Py_XDECREF($this->kyberium_module);
            $this->kyberium_module = null;
        }
        
        // Finaliser Python si nécessaire
        if ($this->ffi->Py_IsInitialized()) {
            $this->ffi->Py_Finalize();
        }
    }
    
    /**
     * Destructeur - Nettoie automatiquement les ressources
     */
    public function __destruct() {
        $this->cleanup();
    }
}

// ============================================================================
// EXCEPTION PERSONNALISÉE
// ============================================================================

/**
 * Exception Kyberium pour les erreurs PHP
 */
class KyberiumException extends Exception {
    public function __construct($message = "", $code = 0, Exception $previous = null) {
        parent::__construct($message, $code, $previous);
    }
}
?> 