/**
 * Kyberium C++ JNI Implementation
 * 
 * Implémentation JNI C++ pour exposer l'API Kyberium Python à Java.
 * Cette bibliothèque native permet d'utiliser les algorithmes post-quantiques
 * directement depuis des applications Java avec des performances optimales.
 * 
 * @author Kyberium Team
 * @version 1.0.0
 * @since 1.0.0
 */

#include <jni.h>
#include <Python.h>
#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <memory>
#include <mutex>
#include <unordered_map>

// Définitions pour la gestion des erreurs
#define KYBERIUM_JNI_SUCCESS 0
#define KYBERIUM_JNI_ERROR -1

// Structure pour les statistiques de performance
struct PerformanceStats {
    long total_encryptions = 0;
    long total_decryptions = 0;
    long total_signatures = 0;
    long total_verifications = 0;
    double avg_encryption_time = 0.0;
    double avg_decryption_time = 0.0;
    double avg_signature_time = 0.0;
    double avg_verification_time = 0.0;
};

// Variables globales pour Python et thread safety
static PyObject* kyberium_module = nullptr;
static PyObject* kyberium_api = nullptr;
static PerformanceStats perf_stats;
static std::mutex python_mutex;
static std::mutex stats_mutex;
static bool python_initialized = false;

// ============================================================================
// UTILITAIRES JNI
// ============================================================================

/**
 * Initialise l'interpréteur Python et importe le module Kyberium.
 */
static int init_python() {
    std::lock_guard<std::mutex> lock(python_mutex);
    
    if (python_initialized) {
        return KYBERIUM_JNI_SUCCESS;
    }
    
    if (!Py_IsInitialized()) {
        Py_Initialize();
        if (!Py_IsInitialized()) {
            std::cerr << "Failed to initialize Python interpreter" << std::endl;
            return KYBERIUM_JNI_ERROR;
        }
    }
    
    // Importer le module Kyberium
    kyberium_module = PyImport_ImportModule("kyberium.api");
    if (!kyberium_module) {
        PyErr_Print();
        std::cerr << "Failed to import kyberium.api module" << std::endl;
        return KYBERIUM_JNI_ERROR;
    }
    
    // Récupérer l'objet API
    kyberium_api = PyObject_GetAttrString(kyberium_module, "api");
    if (!kyberium_api) {
        PyErr_Print();
        std::cerr << "Failed to get kyberium.api.api object" << std::endl;
        return KYBERIUM_JNI_ERROR;
    }
    
    python_initialized = true;
    return KYBERIUM_JNI_SUCCESS;
}

/**
 * Convertit un tableau Java byte[] en objet Python bytes.
 */
static PyObject* java_byte_array_to_python(JNIEnv *env, jbyteArray java_array) {
    if (java_array == nullptr) {
        Py_RETURN_NONE;
    }
    
    jsize length = env->GetArrayLength(java_array);
    jbyte* elements = env->GetByteArrayElements(java_array, nullptr);
    
    PyObject* python_bytes = PyBytes_FromStringAndSize(reinterpret_cast<const char*>(elements), length);
    
    env->ReleaseByteArrayElements(java_array, elements, JNI_ABORT);
    
    return python_bytes;
}

/**
 * Convertit un objet Python bytes en tableau Java byte[].
 */
static jbyteArray python_to_java_byte_array(JNIEnv *env, PyObject* python_bytes) {
    if (python_bytes == nullptr || python_bytes == Py_None) {
        return nullptr;
    }
    
    Py_ssize_t size;
    const char* data = PyBytes_AsStringAndSize(python_bytes, &size);
    
    jbyteArray java_array = env->NewByteArray(size);
    env->SetByteArrayRegion(java_array, 0, size, reinterpret_cast<const jbyte*>(data));
    
    return java_array;
}

/**
 * Convertit un objet Python tuple en tableau Java byte[][].
 */
static jobjectArray python_tuple_to_java_byte_array_array(JNIEnv *env, PyObject* python_tuple) {
    if (python_tuple == nullptr || !PyTuple_Check(python_tuple)) {
        return nullptr;
    }
    
    Py_ssize_t size = PyTuple_Size(python_tuple);
    jclass byte_array_class = env->FindClass("[B");
    jobjectArray java_array = env->NewObjectArray(size, byte_array_class, nullptr);
    
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyTuple_GetItem(python_tuple, i);
        jbyteArray byte_array = python_to_java_byte_array(env, item);
        env->SetObjectArrayElement(java_array, i, byte_array);
    }
    
    return java_array;
}

/**
 * Convertit un objet Python dict en objet Java TripleRatchetInitMessage.
 */
static jobject python_dict_to_triple_ratchet_init_message(JNIEnv *env, PyObject* python_dict) {
    if (python_dict == nullptr || !PyDict_Check(python_dict)) {
        return nullptr;
    }
    
    // Extraire les valeurs du dictionnaire
    PyObject* kem_ciphertext = PyDict_GetItemString(python_dict, "kem_ciphertext");
    PyObject* kem_signature = PyDict_GetItemString(python_dict, "kem_signature");
    PyObject* sign_public_key = PyDict_GetItemString(python_dict, "sign_public_key");
    
    // Convertir en tableaux Java
    jbyteArray java_kem_ciphertext = python_to_java_byte_array(env, kem_ciphertext);
    jbyteArray java_kem_signature = python_to_java_byte_array(env, kem_signature);
    jbyteArray java_sign_public_key = python_to_java_byte_array(env, sign_public_key);
    
    // Créer l'objet Java
    jclass message_class = env->FindClass("KyberiumJNI$TripleRatchetInitMessage");
    jmethodID constructor = env->GetMethodID(message_class, "<init>", "([B[B[B)V");
    
    jobject java_message = env->NewObject(message_class, constructor, 
                                         java_kem_ciphertext, java_kem_signature, java_sign_public_key);
    
    return java_message;
}

/**
 * Convertit un objet Python dict en objet Java TripleRatchetMessage.
 */
static jobject python_dict_to_triple_ratchet_message(JNIEnv *env, PyObject* python_dict) {
    if (python_dict == nullptr || !PyDict_Check(python_dict)) {
        return nullptr;
    }
    
    // Extraire les valeurs du dictionnaire
    PyObject* ciphertext = PyDict_GetItemString(python_dict, "ciphertext");
    PyObject* nonce = PyDict_GetItemString(python_dict, "nonce");
    PyObject* signature = PyDict_GetItemString(python_dict, "signature");
    PyObject* msg_num = PyDict_GetItemString(python_dict, "msg_num");
    PyObject* sign_public_key = PyDict_GetItemString(python_dict, "sign_public_key");
    
    // Convertir en types Java
    jbyteArray java_ciphertext = python_to_java_byte_array(env, ciphertext);
    jbyteArray java_nonce = python_to_java_byte_array(env, nonce);
    jbyteArray java_signature = python_to_java_byte_array(env, signature);
    jint java_msg_num = PyLong_AsLong(msg_num);
    jbyteArray java_sign_public_key = python_to_java_byte_array(env, sign_public_key);
    
    // Créer l'objet Java
    jclass message_class = env->FindClass("KyberiumJNI$TripleRatchetMessage");
    jmethodID constructor = env->GetMethodID(message_class, "<init>", "([B[B[B[B[B)V");
    
    jobject java_message = env->NewObject(message_class, constructor, 
                                         java_ciphertext, java_nonce, java_signature, java_msg_num, java_sign_public_key);
    
    return java_message;
}

/**
 * Gère les erreurs Python et les convertit en exceptions Java.
 */
static void handle_python_error(JNIEnv *env, const char* operation) {
    if (PyErr_Occurred()) {
        PyObject *type, *value, *traceback;
        PyErr_Fetch(&type, &value, &traceback);
        
        // Convertir l'erreur Python en message Java
        PyObject* str_value = PyObject_Str(value);
        const char* error_msg = PyUnicode_AsUTF8(str_value);
        
        // Créer l'exception Java
        jclass exception_class = env->FindClass("KyberiumJNI$KyberiumException");
        env->ThrowNew(exception_class, error_msg);
        
        Py_XDECREF(str_value);
        Py_XDECREF(type);
        Py_XDECREF(value);
        Py_XDECREF(traceback);
    } else {
        // Erreur générique
        jclass exception_class = env->FindClass("KyberiumJNI$KyberiumException");
        env->ThrowNew(exception_class, operation);
    }
}

/**
 * Mesure le temps d'exécution d'une opération.
 */
static double measure_time(std::chrono::high_resolution_clock::time_point start) {
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    return duration.count() / 1000.0; // en millisecondes
}

/**
 * Met à jour les statistiques de performance.
 */
static void update_performance_stats(const std::string& operation, double time_ms) {
    std::lock_guard<std::mutex> lock(stats_mutex);
    
    if (operation == "encryption") {
        perf_stats.total_encryptions++;
        perf_stats.avg_encryption_time = 
            (perf_stats.avg_encryption_time * (perf_stats.total_encryptions - 1) + time_ms) / perf_stats.total_encryptions;
    } else if (operation == "decryption") {
        perf_stats.total_decryptions++;
        perf_stats.avg_decryption_time = 
            (perf_stats.avg_decryption_time * (perf_stats.total_decryptions - 1) + time_ms) / perf_stats.total_decryptions;
    } else if (operation == "signature") {
        perf_stats.total_signatures++;
        perf_stats.avg_signature_time = 
            (perf_stats.avg_signature_time * (perf_stats.total_signatures - 1) + time_ms) / perf_stats.total_signatures;
    } else if (operation == "verification") {
        perf_stats.total_verifications++;
        perf_stats.avg_verification_time = 
            (perf_stats.avg_verification_time * (perf_stats.total_verifications - 1) + time_ms) / perf_stats.total_verifications;
    }
}

// ============================================================================
// IMPLÉMENTATIONS JNI - SESSION CLASSIQUE
// ============================================================================

extern "C" JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_initSession(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    PyObject* result = PyObject_CallMethod(kyberium_api, "init_session", nullptr);
    if (!result) {
        handle_python_error(env, "init_session failed");
        return nullptr;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    update_performance_stats("encryption", measure_time(start));
    
    return java_result;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_initSessionWithPeer(JNIEnv *env, jobject obj, jbyteArray peerPublicKey) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    PyObject* py_peer_key = java_byte_array_to_python(env, peerPublicKey);
    PyObject* result = PyObject_CallMethod(kyberium_api, "init_session", "(O)", py_peer_key);
    
    Py_XDECREF(py_peer_key);
    
    if (!result) {
        handle_python_error(env, "init_session_with_peer failed");
        return nullptr;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_KyberiumJNI_completeHandshake(JNIEnv *env, jobject obj, jbyteArray ciphertext) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return JNI_FALSE;
    }
    
    PyObject* py_ciphertext = java_byte_array_to_python(env, ciphertext);
    PyObject* result = PyObject_CallMethod(kyberium_api, "complete_handshake", "(O)", py_ciphertext);
    
    Py_XDECREF(py_ciphertext);
    
    if (!result) {
        handle_python_error(env, "complete_handshake failed");
        return JNI_FALSE;
    }
    
    jboolean success = PyObject_IsTrue(result);
    Py_XDECREF(result);
    
    return success;
}

extern "C" JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_encrypt(JNIEnv *env, jobject obj, jbyteArray plaintext) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    PyObject* py_plaintext = java_byte_array_to_python(env, plaintext);
    PyObject* result = PyObject_CallMethod(kyberium_api, "encrypt", "(O)", py_plaintext);
    
    Py_XDECREF(py_plaintext);
    
    if (!result) {
        handle_python_error(env, "encrypt failed");
        return nullptr;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    update_performance_stats("encryption", measure_time(start));
    
    return java_result;
}

extern "C" JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_encryptWithAAD(JNIEnv *env, jobject obj, jbyteArray plaintext, jbyteArray aad) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    PyObject* py_plaintext = java_byte_array_to_python(env, plaintext);
    PyObject* py_aad = java_byte_array_to_python(env, aad);
    PyObject* result = PyObject_CallMethod(kyberium_api, "encrypt", "(OO)", py_plaintext, py_aad);
    
    Py_XDECREF(py_plaintext);
    Py_XDECREF(py_aad);
    
    if (!result) {
        handle_python_error(env, "encrypt_with_aad failed");
        return nullptr;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_decrypt(JNIEnv *env, jobject obj, jbyteArray ciphertext, jbyteArray nonce) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    PyObject* py_ciphertext = java_byte_array_to_python(env, ciphertext);
    PyObject* py_nonce = java_byte_array_to_python(env, nonce);
    PyObject* result = PyObject_CallMethod(kyberium_api, "decrypt", "(OO)", py_ciphertext, py_nonce);
    
    Py_XDECREF(py_ciphertext);
    Py_XDECREF(py_nonce);
    
    if (!result) {
        handle_python_error(env, "decrypt failed");
        return nullptr;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    update_performance_stats("decryption", measure_time(start));
    
    return java_result;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_decryptWithAAD(JNIEnv *env, jobject obj, jbyteArray ciphertext, jbyteArray nonce, jbyteArray aad) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    PyObject* py_ciphertext = java_byte_array_to_python(env, ciphertext);
    PyObject* py_nonce = java_byte_array_to_python(env, nonce);
    PyObject* py_aad = java_byte_array_to_python(env, aad);
    PyObject* result = PyObject_CallMethod(kyberium_api, "decrypt", "(OOO)", py_ciphertext, py_nonce, py_aad);
    
    Py_XDECREF(py_ciphertext);
    Py_XDECREF(py_nonce);
    Py_XDECREF(py_aad);
    
    if (!result) {
        handle_python_error(env, "decrypt_with_aad failed");
        return nullptr;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - SIGNATURE
// ============================================================================

extern "C" JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_sign(JNIEnv *env, jobject obj, jbyteArray message) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    PyObject* py_message = java_byte_array_to_python(env, message);
    PyObject* result = PyObject_CallMethod(kyberium_api, "sign", "(O)", py_message);
    
    Py_XDECREF(py_message);
    
    if (!result) {
        handle_python_error(env, "sign failed");
        return nullptr;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    update_performance_stats("signature", measure_time(start));
    
    return java_result;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_KyberiumJNI_verify(JNIEnv *env, jobject obj, jbyteArray message, jbyteArray signature, jbyteArray publicKey) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return JNI_FALSE;
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    PyObject* py_message = java_byte_array_to_python(env, message);
    PyObject* py_signature = java_byte_array_to_python(env, signature);
    PyObject* py_public_key = java_byte_array_to_python(env, publicKey);
    
    PyObject* result;
    if (publicKey == nullptr) {
        result = PyObject_CallMethod(kyberium_api, "verify", "(OO)", py_message, py_signature);
    } else {
        result = PyObject_CallMethod(kyberium_api, "verify", "(OOO)", py_message, py_signature, py_public_key);
    }
    
    Py_XDECREF(py_message);
    Py_XDECREF(py_signature);
    Py_XDECREF(py_public_key);
    
    if (!result) {
        handle_python_error(env, "verify failed");
        return JNI_FALSE;
    }
    
    jboolean success = PyObject_IsTrue(result);
    Py_XDECREF(result);
    
    update_performance_stats("verification", measure_time(start));
    
    return success;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - TRIPLE RATCHET
// ============================================================================

extern "C" JNIEXPORT jobject JNICALL
Java_KyberiumJNI_initTripleRatchet(JNIEnv *env, jobject obj, jbyteArray peerKemPublic, jbyteArray peerSignPublic) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    PyObject* py_kem_public = java_byte_array_to_python(env, peerKemPublic);
    PyObject* py_sign_public = java_byte_array_to_python(env, peerSignPublic);
    PyObject* result = PyObject_CallMethod(kyberium_api, "init_triple_ratchet", "(OO)", py_kem_public, py_sign_public);
    
    Py_XDECREF(py_kem_public);
    Py_XDECREF(py_sign_public);
    
    if (!result) {
        handle_python_error(env, "init_triple_ratchet failed");
        return nullptr;
    }
    
    jobject java_message = python_dict_to_triple_ratchet_init_message(env, result);
    Py_XDECREF(result);
    
    return java_message;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_KyberiumJNI_completeTripleRatchetHandshake(JNIEnv *env, jobject obj, jbyteArray kemCiphertext, jbyteArray kemSignature, jbyteArray peerSignPublic) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return JNI_FALSE;
    }
    
    PyObject* py_kem_ciphertext = java_byte_array_to_python(env, kemCiphertext);
    PyObject* py_kem_signature = java_byte_array_to_python(env, kemSignature);
    PyObject* py_peer_sign_public = java_byte_array_to_python(env, peerSignPublic);
    
    PyObject* result = PyObject_CallMethod(kyberium_api, "complete_triple_ratchet_handshake", "(OOO)", 
                                         py_kem_ciphertext, py_kem_signature, py_peer_sign_public);
    
    Py_XDECREF(py_kem_ciphertext);
    Py_XDECREF(py_kem_signature);
    Py_XDECREF(py_peer_sign_public);
    
    if (!result) {
        handle_python_error(env, "complete_triple_ratchet_handshake failed");
        return JNI_FALSE;
    }
    
    jboolean success = PyObject_IsTrue(result);
    Py_XDECREF(result);
    
    return success;
}

extern "C" JNIEXPORT jobject JNICALL
Java_KyberiumJNI_tripleEncrypt(JNIEnv *env, jobject obj, jbyteArray plaintext) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    PyObject* py_plaintext = java_byte_array_to_python(env, plaintext);
    PyObject* result = PyObject_CallMethod(kyberium_api, "triple_encrypt", "(O)", py_plaintext);
    
    Py_XDECREF(py_plaintext);
    
    if (!result) {
        handle_python_error(env, "triple_encrypt failed");
        return nullptr;
    }
    
    jobject java_message = python_dict_to_triple_ratchet_message(env, result);
    Py_XDECREF(result);
    
    return java_message;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_tripleDecrypt(JNIEnv *env, jobject obj, jbyteArray ciphertext, jbyteArray nonce, jbyteArray signature, jint msgNum, jbyteArray peerSignPublic) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    PyObject* py_ciphertext = java_byte_array_to_python(env, ciphertext);
    PyObject* py_nonce = java_byte_array_to_python(env, nonce);
    PyObject* py_signature = java_byte_array_to_python(env, signature);
    PyObject* py_msg_num = PyLong_FromLong(msgNum);
    PyObject* py_peer_sign_public = java_byte_array_to_python(env, peerSignPublic);
    
    PyObject* result = PyObject_CallMethod(kyberium_api, "triple_decrypt", "(OOOOO)", 
                                         py_ciphertext, py_nonce, py_signature, py_msg_num, py_peer_sign_public);
    
    Py_XDECREF(py_ciphertext);
    Py_XDECREF(py_nonce);
    Py_XDECREF(py_signature);
    Py_XDECREF(py_msg_num);
    Py_XDECREF(py_peer_sign_public);
    
    if (!result) {
        handle_python_error(env, "triple_decrypt failed");
        return nullptr;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - GESTION DES CLÉS
// ============================================================================

extern "C" JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_generateKemKeypair(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    // Importer le module KEM
    PyObject* kem_module = PyImport_ImportModule("kyberium.kem.kyber");
    if (!kem_module) {
        handle_python_error(env, "Failed to import KEM module");
        return nullptr;
    }
    
    PyObject* kem_class = PyObject_GetAttrString(kem_module, "Kyber1024");
    PyObject* kem_instance = PyObject_CallObject(kem_class, nullptr);
    PyObject* result = PyObject_CallMethod(kem_instance, "generate_keypair", nullptr);
    
    Py_XDECREF(kem_module);
    Py_XDECREF(kem_class);
    Py_XDECREF(kem_instance);
    
    if (!result) {
        handle_python_error(env, "generate_kem_keypair failed");
        return nullptr;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

extern "C" JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_generateSignatureKeypair(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return nullptr;
    }
    
    // Importer le module Signature
    PyObject* sig_module = PyImport_ImportModule("kyberium.signature.dilithium");
    if (!sig_module) {
        handle_python_error(env, "Failed to import Signature module");
        return nullptr;
    }
    
    PyObject* sig_class = PyObject_GetAttrString(sig_module, "DilithiumSignature");
    PyObject* sig_instance = PyObject_CallObject(sig_class, nullptr);
    PyObject* result = PyObject_CallMethod(sig_instance, "generate_keypair", nullptr);
    
    Py_XDECREF(sig_module);
    Py_XDECREF(sig_class);
    Py_XDECREF(sig_instance);
    
    if (!result) {
        handle_python_error(env, "generate_signature_keypair failed");
        return nullptr;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - UTILITAIRES
// ============================================================================

extern "C" JNIEXPORT jboolean JNICALL
Java_KyberiumJNI_rekey(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return JNI_FALSE;
    }
    
    PyObject* result = PyObject_CallMethod(kyberium_api, "rekey", nullptr);
    if (!result) {
        handle_python_error(env, "rekey failed");
        return JNI_FALSE;
    }
    
    jboolean success = PyObject_IsTrue(result);
    Py_XDECREF(result);
    
    return success;
}

extern "C" JNIEXPORT jstring JNICALL
Java_KyberiumJNI_getAlgorithmInfo(JNIEnv *env, jobject obj) {
    const char* info = "Kyberium Post-Quantum Cryptography\n"
                      "- KEM: CRYSTALS-Kyber-1024 (ML-KEM-1024)\n"
                      "- Signature: CRYSTALS-Dilithium\n"
                      "- Symmetric: AES-256-GCM/ChaCha20-Poly1305\n"
                      "- KDF: SHA-3/SHAKE-256\n"
                      "- Security: NIST Level 5 (Post-Quantum)";
    
    return env->NewStringUTF(info);
}

extern "C" JNIEXPORT jobject JNICALL
Java_KyberiumJNI_getPerformanceStats(JNIEnv *env, jobject obj) {
    std::lock_guard<std::mutex> lock(stats_mutex);
    
    jclass stats_class = env->FindClass("KyberiumJNI$PerformanceStats");
    jmethodID constructor = env->GetMethodID(stats_class, "<init>", "(JJJJDDDD)V");
    
    jobject stats = env->NewObject(stats_class, constructor,
                                  perf_stats.total_encryptions,
                                  perf_stats.total_decryptions,
                                  perf_stats.total_signatures,
                                  perf_stats.total_verifications,
                                  perf_stats.avg_encryption_time,
                                  perf_stats.avg_decryption_time,
                                  perf_stats.avg_signature_time,
                                  perf_stats.avg_verification_time);
    
    return stats;
}

extern "C" JNIEXPORT void JNICALL
Java_KyberiumJNI_cleanup(JNIEnv *env, jobject obj) {
    std::lock_guard<std::mutex> lock(python_mutex);
    
    // Nettoyer les ressources Python
    if (kyberium_api) {
        Py_XDECREF(kyberium_api);
        kyberium_api = nullptr;
    }
    
    if (kyberium_module) {
        Py_XDECREF(kyberium_module);
        kyberium_module = nullptr;
    }
    
    // Finaliser Python si nécessaire
    if (Py_IsInitialized()) {
        Py_Finalize();
    }
    
    python_initialized = false;
}

// ============================================================================
// FONCTIONS D'INITIALISATION ET DE FINALISATION
// ============================================================================

extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    // Initialisation de la bibliothèque JNI
    return JNI_VERSION_1_8;
}

extern "C" JNIEXPORT void JNICALL JNI_OnUnload(JavaVM* vm, void* reserved) {
    // Nettoyage de la bibliothèque JNI
    std::lock_guard<std::mutex> lock(python_mutex);
    
    if (Py_IsInitialized()) {
        Py_Finalize();
    }
    
    python_initialized = false;
} 