/**
 * Kyberium JNI Implementation
 * 
 * Implémentation JNI pour exposer l'API Kyberium Python à Java.
 * Cette bibliothèque native permet d'utiliser les algorithmes post-quantiques
 * directement depuis des applications Java avec des performances optimales.
 * 
 * @author Kyberium Team
 * @version 1.0.0
 * @since 1.0.0
 */

#include <jni.h>
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Définitions pour la gestion des erreurs
#define KYBERIUM_JNI_SUCCESS 0
#define KYBERIUM_JNI_ERROR -1

// Structure pour les statistiques de performance
typedef struct {
    long total_encryptions;
    long total_decryptions;
    long total_signatures;
    long total_verifications;
    double avg_encryption_time;
    double avg_decryption_time;
    double avg_signature_time;
    double avg_verification_time;
} performance_stats_t;

// Variables globales pour Python
static PyObject *kyberium_module = NULL;
static PyObject *kyberium_api = NULL;
static performance_stats_t perf_stats = {0};

// ============================================================================
// UTILITAIRES JNI
// ============================================================================

/**
 * Initialise l'interpréteur Python et importe le module Kyberium.
 */
static int init_python() {
    if (Py_IsInitialized()) {
        return KYBERIUM_JNI_SUCCESS;
    }
    
    // Forcer l'utilisation du Python système en modifiant sys.path
    Py_Initialize();
    if (!Py_IsInitialized()) {
        return KYBERIUM_JNI_ERROR;
    }
    
    // Nettoyer sys.path pour éviter le venv et ajouter les chemins système
    PyObject* sys_module = PyImport_ImportModule("sys");
    if (sys_module) {
        PyObject* sys_path = PyObject_GetAttrString(sys_module, "path");
        if (sys_path && PyList_Check(sys_path)) {
            // Supprimer les chemins du venv
            Py_ssize_t size = PyList_Size(sys_path);
            for (Py_ssize_t i = size - 1; i >= 0; i--) {
                PyObject* path_item = PyList_GetItem(sys_path, i);
                if (path_item && PyUnicode_Check(path_item)) {
                    const char* path_str = PyUnicode_AsUTF8(path_item);
                    if (path_str && strstr(path_str, "venv") != NULL) {
                        PyList_SetSlice(sys_path, i, i+1, NULL);
                    }
                }
            }
            
            // Ajouter les chemins système pour pqcrypto
            PyObject* system_paths[] = {
                PyUnicode_FromString("/usr/local/lib/python3.11/dist-packages"),
                PyUnicode_FromString("/usr/lib/python3/dist-packages"),
                PyUnicode_FromString("/usr/lib/python3.11/dist-packages"),
                PyUnicode_FromString("/home/prity/Desktop/kyberium")
            };
            
            for (int i = 0; i < 4; i++) {
                PyList_Insert(sys_path, 0, system_paths[i]);
                Py_XDECREF(system_paths[i]);
            }
        }
        Py_XDECREF(sys_path);
        Py_XDECREF(sys_module);
    }
    
    // Importer le module Kyberium
    kyberium_module = PyImport_ImportModule("kyberium.api");
    if (!kyberium_module) {
        PyErr_Print();
        return KYBERIUM_JNI_ERROR;
    }
    
    // Le module kyberium.api expose directement les fonctions
    kyberium_api = kyberium_module;
    if (!kyberium_api) {
        PyErr_Print();
        return KYBERIUM_JNI_ERROR;
    }
    
    return KYBERIUM_JNI_SUCCESS;
}

/**
 * Convertit un tableau Java byte[] en objet Python bytes.
 */
static PyObject* java_byte_array_to_python(JNIEnv *env, jbyteArray java_array) {
    if (java_array == NULL) {
        return Py_None;
    }
    
    jsize length = (*env)->GetArrayLength(env, java_array);
    jbyte* elements = (*env)->GetByteArrayElements(env, java_array, NULL);
    
    PyObject* python_bytes = PyBytes_FromStringAndSize((char*)elements, length);
    
    (*env)->ReleaseByteArrayElements(env, java_array, elements, JNI_ABORT);
    
    return python_bytes;
}

/**
 * Convertit un objet Python bytes en tableau Java byte[].
 */
static jbyteArray python_to_java_byte_array(JNIEnv *env, PyObject* python_bytes) {
    if (python_bytes == NULL || python_bytes == Py_None) {
        return NULL;
    }
    
    Py_ssize_t size;
    char* buffer = NULL;
    if (PyBytes_AsStringAndSize(python_bytes, &buffer, &size) != 0) {
        // gestion d'erreur
        return NULL;
    }
    
    jbyteArray java_array = (*env)->NewByteArray(env, size);
    (*env)->SetByteArrayRegion(env, java_array, 0, size, (jbyte*)buffer);
    
    return java_array;
}

/**
 * Convertit un objet Python tuple en tableau Java byte[][].
 */
static jobjectArray python_tuple_to_java_byte_array_array(JNIEnv *env, PyObject* python_tuple) {
    if (python_tuple == NULL || !PyTuple_Check(python_tuple)) {
        return NULL;
    }
    
    Py_ssize_t size = PyTuple_Size(python_tuple);
    jclass byte_array_class = (*env)->FindClass(env, "[B");
    jobjectArray java_array = (*env)->NewObjectArray(env, size, byte_array_class, NULL);
    
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyTuple_GetItem(python_tuple, i);
        jbyteArray byte_array = python_to_java_byte_array(env, item);
        (*env)->SetObjectArrayElement(env, java_array, i, byte_array);
    }
    
    return java_array;
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
        jclass exception_class = (*env)->FindClass(env, "KyberiumJNI$KyberiumException");
        (*env)->ThrowNew(env, exception_class, error_msg);
        
        Py_XDECREF(str_value);
        Py_XDECREF(type);
        Py_XDECREF(value);
        Py_XDECREF(traceback);
    } else {
        // Erreur générique
        jclass exception_class = (*env)->FindClass(env, "KyberiumJNI$KyberiumException");
        (*env)->ThrowNew(env, exception_class, operation);
    }
}

/**
 * Mesure le temps d'exécution d'une opération.
 */
static double measure_time(clock_t start) {
    clock_t end = clock();
    return ((double)(end - start)) / CLOCKS_PER_SEC * 1000.0; // en millisecondes
}

// ============================================================================
// IMPLÉMENTATIONS JNI - SESSION CLASSIQUE
// ============================================================================

JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_initSession(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    clock_t start = clock();
    
    PyObject* result = PyObject_CallMethod(kyberium_api, "init_session", NULL);
    if (!result) {
        handle_python_error(env, "init_session failed");
        return NULL;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    perf_stats.total_encryptions++;
    perf_stats.avg_encryption_time = measure_time(start);
    
    return java_result;
}

JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_initSessionWithPeer(JNIEnv *env, jobject obj, jbyteArray peerPublicKey) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    PyObject* py_peer_key = java_byte_array_to_python(env, peerPublicKey);
    PyObject* result = PyObject_CallMethod(kyberium_api, "init_session", "(O)", py_peer_key);
    
    Py_XDECREF(py_peer_key);
    
    if (!result) {
        handle_python_error(env, "init_session_with_peer failed");
        return NULL;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

JNIEXPORT jboolean JNICALL
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

JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_encrypt(JNIEnv *env, jobject obj, jbyteArray plaintext) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    clock_t start = clock();
    
    PyObject* py_plaintext = java_byte_array_to_python(env, plaintext);
    PyObject* result = PyObject_CallMethod(kyberium_api, "encrypt", "(O)", py_plaintext);
    
    Py_XDECREF(py_plaintext);
    
    if (!result) {
        handle_python_error(env, "encrypt failed");
        return NULL;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    perf_stats.total_encryptions++;
    perf_stats.avg_encryption_time = measure_time(start);
    
    return java_result;
}

JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_encryptWithAAD(JNIEnv *env, jobject obj, jbyteArray plaintext, jbyteArray aad) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    PyObject* py_plaintext = java_byte_array_to_python(env, plaintext);
    PyObject* py_aad = java_byte_array_to_python(env, aad);
    PyObject* result = PyObject_CallMethod(kyberium_api, "encrypt", "(OO)", py_plaintext, py_aad);
    
    Py_XDECREF(py_plaintext);
    Py_XDECREF(py_aad);
    
    if (!result) {
        handle_python_error(env, "encrypt_with_aad failed");
        return NULL;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_decrypt(JNIEnv *env, jobject obj, jbyteArray ciphertext, jbyteArray nonce) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    clock_t start = clock();
    
    PyObject* py_ciphertext = java_byte_array_to_python(env, ciphertext);
    PyObject* py_nonce = java_byte_array_to_python(env, nonce);
    PyObject* result = PyObject_CallMethod(kyberium_api, "decrypt", "(OO)", py_ciphertext, py_nonce);
    
    Py_XDECREF(py_ciphertext);
    Py_XDECREF(py_nonce);
    
    if (!result) {
        handle_python_error(env, "decrypt failed");
        return NULL;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    perf_stats.total_decryptions++;
    perf_stats.avg_decryption_time = measure_time(start);
    
    return java_result;
}

JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_decryptWithAAD(JNIEnv *env, jobject obj, jbyteArray ciphertext, jbyteArray nonce, jbyteArray aad) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
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
        return NULL;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - SIGNATURE
// ============================================================================

JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_sign(JNIEnv *env, jobject obj, jbyteArray message) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    clock_t start = clock();
    
    PyObject* py_message = java_byte_array_to_python(env, message);
    PyObject* result = PyObject_CallMethod(kyberium_api, "sign", "(O)", py_message);
    
    Py_XDECREF(py_message);
    
    if (!result) {
        handle_python_error(env, "sign failed");
        return NULL;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    perf_stats.total_signatures++;
    perf_stats.avg_signature_time = measure_time(start);
    
    return java_result;
}

JNIEXPORT jboolean JNICALL
Java_KyberiumJNI_verify(JNIEnv *env, jobject obj, jbyteArray message, jbyteArray signature, jbyteArray publicKey) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return JNI_FALSE;
    }
    
    clock_t start = clock();
    
    PyObject* py_message = java_byte_array_to_python(env, message);
    PyObject* py_signature = java_byte_array_to_python(env, signature);
    PyObject* py_public_key = java_byte_array_to_python(env, publicKey);
    
    PyObject* result;
    if (publicKey == NULL) {
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
    
    perf_stats.total_verifications++;
    perf_stats.avg_verification_time = measure_time(start);
    
    return success;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - TRIPLE RATCHET
// ============================================================================

JNIEXPORT jobject JNICALL
Java_KyberiumJNI_initTripleRatchet(JNIEnv *env, jobject obj, jbyteArray peerKemPublic, jbyteArray peerSignPublic) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    PyObject* py_kem_public = java_byte_array_to_python(env, peerKemPublic);
    PyObject* py_sign_public = java_byte_array_to_python(env, peerSignPublic);
    PyObject* result = PyObject_CallMethod(kyberium_api, "init_triple_ratchet", "(OO)", py_kem_public, py_sign_public);
    
    Py_XDECREF(py_kem_public);
    Py_XDECREF(py_sign_public);
    
    if (!result) {
        handle_python_error(env, "init_triple_ratchet failed");
        return NULL;
    }
    
    // Extraire les données du dictionnaire Python
    PyObject* kem_ciphertext = PyDict_GetItemString(result, "kem_ciphertext");
    PyObject* kem_signature = PyDict_GetItemString(result, "kem_signature");
    PyObject* sign_public_key = PyDict_GetItemString(result, "sign_public_key");
    
    // Créer l'objet Java TripleRatchetInitMessage
    jclass message_class = (*env)->FindClass(env, "KyberiumJNI$TripleRatchetInitMessage");
    jmethodID constructor = (*env)->GetMethodID(env, message_class, "<init>", "([B[B[B)V");
    
    jbyteArray java_kem_ciphertext = python_to_java_byte_array(env, kem_ciphertext);
    jbyteArray java_kem_signature = python_to_java_byte_array(env, kem_signature);
    jbyteArray java_sign_public_key = python_to_java_byte_array(env, sign_public_key);
    
    jobject java_message = (*env)->NewObject(env, message_class, constructor, 
                                           java_kem_ciphertext, java_kem_signature, java_sign_public_key);
    
    Py_XDECREF(result);
    
    return java_message;
}

JNIEXPORT jboolean JNICALL
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

JNIEXPORT jobject JNICALL
Java_KyberiumJNI_tripleEncrypt(JNIEnv *env, jobject obj, jbyteArray plaintext) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    PyObject* py_plaintext = java_byte_array_to_python(env, plaintext);
    PyObject* result = PyObject_CallMethod(kyberium_api, "triple_encrypt", "(O)", py_plaintext);
    
    Py_XDECREF(py_plaintext);
    
    if (!result) {
        handle_python_error(env, "triple_encrypt failed");
        return NULL;
    }
    
    // Extraire les données du dictionnaire Python
    PyObject* ciphertext = PyDict_GetItemString(result, "ciphertext");
    PyObject* nonce = PyDict_GetItemString(result, "nonce");
    PyObject* signature = PyDict_GetItemString(result, "signature");
    PyObject* msg_num = PyDict_GetItemString(result, "msg_num");
    PyObject* sign_public_key = PyDict_GetItemString(result, "sign_public_key");
    
    // Créer l'objet Java TripleRatchetMessage
    jclass message_class = (*env)->FindClass(env, "KyberiumJNI$TripleRatchetMessage");
    jmethodID constructor = (*env)->GetMethodID(env, message_class, "<init>", "([B[B[B[B[B)V");
    
    jbyteArray java_ciphertext = python_to_java_byte_array(env, ciphertext);
    jbyteArray java_nonce = python_to_java_byte_array(env, nonce);
    jbyteArray java_signature = python_to_java_byte_array(env, signature);
    jint java_msg_num = PyLong_AsLong(msg_num);
    jbyteArray java_sign_public_key = python_to_java_byte_array(env, sign_public_key);
    
    jobject java_message = (*env)->NewObject(env, message_class, constructor, 
                                           java_ciphertext, java_nonce, java_signature, java_msg_num, java_sign_public_key);
    
    Py_XDECREF(result);
    
    return java_message;
}

JNIEXPORT jbyteArray JNICALL
Java_KyberiumJNI_tripleDecrypt(JNIEnv *env, jobject obj, jbyteArray ciphertext, jbyteArray nonce, jbyteArray signature, jint msgNum, jbyteArray peerSignPublic) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
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
        return NULL;
    }
    
    jbyteArray java_result = python_to_java_byte_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - GESTION DES CLÉS
// ============================================================================

JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_generateKemKeypair(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    // Importer le module KEM
    PyObject* kem_module = PyImport_ImportModule("kyberium.kem.kyber");
    if (!kem_module) {
        handle_python_error(env, "Failed to import KEM module");
        return NULL;
    }
    
    PyObject* kem_class = PyObject_GetAttrString(kem_module, "Kyber1024");
    PyObject* kem_instance = PyObject_CallObject(kem_class, NULL);
    PyObject* result = PyObject_CallMethod(kem_instance, "generate_keypair", NULL);
    
    Py_XDECREF(kem_module);
    Py_XDECREF(kem_class);
    Py_XDECREF(kem_instance);
    
    if (!result) {
        handle_python_error(env, "generate_kem_keypair failed");
        return NULL;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

JNIEXPORT jobjectArray JNICALL
Java_KyberiumJNI_generateSignatureKeypair(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    // Importer le module Signature
    PyObject* sig_module = PyImport_ImportModule("kyberium.signature.dilithium");
    if (!sig_module) {
        handle_python_error(env, "Failed to import Signature module");
        return NULL;
    }
    
    PyObject* sig_class = PyObject_GetAttrString(sig_module, "DilithiumSignature");
    PyObject* sig_instance = PyObject_CallObject(sig_class, NULL);
    PyObject* result = PyObject_CallMethod(sig_instance, "generate_keypair", NULL);
    
    Py_XDECREF(sig_module);
    Py_XDECREF(sig_class);
    Py_XDECREF(sig_instance);
    
    if (!result) {
        handle_python_error(env, "generate_signature_keypair failed");
        return NULL;
    }
    
    jobjectArray java_result = python_tuple_to_java_byte_array_array(env, result);
    Py_XDECREF(result);
    
    return java_result;
}

// ============================================================================
// IMPLÉMENTATIONS JNI - UTILITAIRES
// ============================================================================

JNIEXPORT jboolean JNICALL
Java_KyberiumJNI_rekey(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return JNI_FALSE;
    }
    
    PyObject* result = PyObject_CallMethod(kyberium_api, "rekey", NULL);
    if (!result) {
        handle_python_error(env, "rekey failed");
        return JNI_FALSE;
    }
    
    jboolean success = PyObject_IsTrue(result);
    Py_XDECREF(result);
    
    return success;
}

JNIEXPORT jstring JNICALL
Java_KyberiumJNI_getAlgorithmInfo(JNIEnv *env, jobject obj) {
    if (init_python() != KYBERIUM_JNI_SUCCESS) {
        handle_python_error(env, "Failed to initialize Python");
        return NULL;
    }
    
    // Retourner les informations sur les algorithmes
    const char* info = "Kyberium Post-Quantum Cryptography\n"
                      "- KEM: CRYSTALS-Kyber-1024 (ML-KEM-1024)\n"
                      "- Signature: CRYSTALS-Dilithium\n"
                      "- Symmetric: AES-256-GCM/ChaCha20-Poly1305\n"
                      "- KDF: SHA-3/SHAKE-256\n"
                      "- Security: NIST Level 5 (Post-Quantum)";
    
    return (*env)->NewStringUTF(env, info);
}

JNIEXPORT jobject JNICALL
Java_KyberiumJNI_getPerformanceStats(JNIEnv *env, jobject obj) {
    jclass stats_class = (*env)->FindClass(env, "KyberiumJNI$PerformanceStats");
    jmethodID constructor = (*env)->GetMethodID(env, stats_class, "<init>", "(JJJJDDDD)V");
    
    jobject stats = (*env)->NewObject(env, stats_class, constructor,
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

JNIEXPORT void JNICALL
Java_KyberiumJNI_cleanup(JNIEnv *env, jobject obj) {
    // Nettoyer les ressources Python
    if (kyberium_api) {
        Py_XDECREF(kyberium_api);
        kyberium_api = NULL;
    }
    
    if (kyberium_module) {
        Py_XDECREF(kyberium_module);
        kyberium_module = NULL;
    }
    
    // Finaliser Python si nécessaire
    if (Py_IsInitialized()) {
        Py_Finalize();
    }
}

// ============================================================================
// FONCTIONS D'INITIALISATION ET DE FINALISATION
// ============================================================================

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    // Initialisation de la bibliothèque JNI
    return JNI_VERSION_1_8;
}

JNIEXPORT void JNICALL JNI_OnUnload(JavaVM* vm, void* reserved) {
    // Nettoyage de la bibliothèque JNI
    if (Py_IsInitialized()) {
        Py_Finalize();
    }
} 