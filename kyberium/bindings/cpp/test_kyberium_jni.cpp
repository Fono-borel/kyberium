#include <gtest/gtest.h>
#include <jni.h>
#include <string>
#include <vector>
#include <cstring>

// Hypothèse : Les headers KyberiumJNI sont générés et accessibles
#include "KyberiumJNI.h"

class KyberiumJNITest : public ::testing::Test {
protected:
    KyberiumJNI* kyberium;

    void SetUp() override {
        kyberium = new KyberiumJNI();
    }
    void TearDown() override {
        if (kyberium) kyberium->cleanup();
        delete kyberium;
    }
};

TEST_F(KyberiumJNITest, SessionHandshake) {
    auto publicKey = kyberium->initSession();
    ASSERT_FALSE(publicKey.empty());
    auto ciphertext = kyberium->initSessionWithPeer(publicKey);
    ASSERT_FALSE(ciphertext.empty());
    bool success = kyberium->completeHandshake(ciphertext);
    ASSERT_TRUE(success);
}

TEST_F(KyberiumJNITest, EncryptionDecryption) {
    auto publicKey = kyberium->initSession();
    auto ciphertext = kyberium->initSessionWithPeer(publicKey);
    kyberium->completeHandshake(ciphertext);
    std::string message = "Test message";
    auto encrypted = kyberium->encrypt(std::vector<uint8_t>(message.begin(), message.end()));
    ASSERT_EQ(encrypted.size(), 2);
    auto decrypted = kyberium->decrypt(encrypted[0], encrypted[1]);
    ASSERT_EQ(std::string(decrypted.begin(), decrypted.end()), message);
}

TEST_F(KyberiumJNITest, TripleRatchet) {
    auto kemKeys = kyberium->generateKemKeypair();
    auto signKeys = kyberium->generateSignatureKeypair();
    auto initMsg = kyberium->initTripleRatchet(kemKeys[0], signKeys[0]);
    ASSERT_FALSE(initMsg.kemCiphertext.empty());
    bool success = kyberium->completeTripleRatchetHandshake(initMsg.kemCiphertext, initMsg.kemSignature, initMsg.signPublicKey);
    ASSERT_TRUE(success);
    std::string msg = "Triple ratchet test";
    auto encrypted = kyberium->tripleEncrypt(std::vector<uint8_t>(msg.begin(), msg.end()));
    ASSERT_FALSE(encrypted.ciphertext.empty());
    auto decrypted = kyberium->tripleDecrypt(encrypted.ciphertext, encrypted.nonce, encrypted.signature, encrypted.msgNum, encrypted.signPublicKey);
    ASSERT_EQ(std::string(decrypted.begin(), decrypted.end()), msg);
}

TEST_F(KyberiumJNITest, SignatureVerification) {
    std::string message = "Message to sign";
    auto signature = kyberium->sign(std::vector<uint8_t>(message.begin(), message.end()));
    ASSERT_FALSE(signature.empty());
    bool isValid = kyberium->verify(std::vector<uint8_t>(message.begin(), message.end()), signature, {});
    ASSERT_TRUE(isValid);
    signature[0] ^= 0xFF; // Corrompre la signature
    bool isInvalid = kyberium->verify(std::vector<uint8_t>(message.begin(), message.end()), signature, {});
    ASSERT_FALSE(isInvalid);
}

TEST_F(KyberiumJNITest, PerformanceStats) {
    auto publicKey = kyberium->initSession();
    auto ciphertext = kyberium->initSessionWithPeer(publicKey);
    kyberium->completeHandshake(ciphertext);
    auto encrypted = kyberium->encrypt({'T','e','s','t'});
    kyberium->decrypt(encrypted[0], encrypted[1]);
    auto stats = kyberium->getPerformanceStats();
    ASSERT_GT(stats.totalEncryptions, 0);
}

TEST_F(KyberiumJNITest, ErrorHandling) {
    ASSERT_THROW(kyberium->decrypt({}, {}), std::exception);
} 