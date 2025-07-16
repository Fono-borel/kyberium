<?php
use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../kyberium_php.php';

class KyberiumPHPTest extends TestCase {
    private $kyberium;

    protected function setUp(): void {
        $this->kyberium = new KyberiumPHP();
    }

    protected function tearDown(): void {
        if ($this->kyberium) {
            $this->kyberium->cleanup();
        }
    }

    public function testSessionHandshake() {
        $publicKey = $this->kyberium->initSession();
        $this->assertNotNull($publicKey);
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->assertNotNull($ciphertext);
        $success = $this->kyberium->completeHandshake($ciphertext);
        $this->assertTrue($success);
    }

    public function testEncryptionDecryption() {
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        $message = "Test message";
        $encrypted = $this->kyberium->encrypt($message);
        $this->assertNotNull($encrypted);
        $this->assertCount(2, $encrypted);
        $decrypted = $this->kyberium->decrypt($encrypted[0], $encrypted[1]);
        $this->assertNotNull($decrypted);
        $this->assertEquals($message, $decrypted);
    }

    public function testTripleRatchet() {
        $kemPublic = random_bytes(1184);
        $signPublic = random_bytes(1952);
        $initMsg = $this->kyberium->initTripleRatchet($kemPublic, $signPublic);
        $this->assertNotNull($initMsg);
        $success = $this->kyberium->completeTripleRatchetHandshake($initMsg['kem_ciphertext'], $initMsg['kem_signature'], $initMsg['sign_public_key']);
        $this->assertTrue($success);
        $msg = "Triple ratchet test";
        $encrypted = $this->kyberium->tripleEncrypt($msg);
        $this->assertNotNull($encrypted);
        $decrypted = $this->kyberium->tripleDecrypt($encrypted['ciphertext'], $encrypted['nonce'], $encrypted['signature'], $encrypted['msg_num'], $encrypted['sign_public_key']);
        $this->assertEquals($msg, $decrypted);
    }

    public function testSignatureVerification() {
        $message = "Message to sign";
        $signature = $this->kyberium->sign($message);
        $this->assertNotNull($signature);
        $isValid = $this->kyberium->verify($message, $signature);
        $this->assertTrue($isValid);
        $signature[0] = chr(ord($signature[0]) ^ 0xFF); // Corrompre la signature
        $isInvalid = $this->kyberium->verify($message, $signature);
        $this->assertFalse($isInvalid);
    }

    public function testPerformanceStats() {
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        $encrypted = $this->kyberium->encrypt("Test");
        $this->kyberium->decrypt($encrypted[0], $encrypted[1]);
        $stats = $this->kyberium->getPerformanceStats();
        $this->assertNotNull($stats);
        $this->assertGreaterThan(0, $stats['total_encryptions']);
    }

    public function testErrorHandling() {
        $this->expectException(Exception::class);
        $this->kyberium->decrypt(null, null); // Doit lever une exception
    }

    public function testEmptyMessage() {
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        $plaintext = '';
        $encrypted = $this->kyberium->encrypt($plaintext);
        $this->assertNotNull($encrypted);
        $this->assertCount(2, $encrypted);
        $decrypted = $this->kyberium->decrypt($encrypted[0], $encrypted[1]);
        $this->assertEquals('', $decrypted);
    }

    public function testLongMessage() {
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        $plaintext = str_repeat('A', 10000);
        $encrypted = $this->kyberium->encrypt($plaintext);
        $this->assertNotNull($encrypted);
        $this->assertCount(2, $encrypted);
        $decrypted = $this->kyberium->decrypt($encrypted[0], $encrypted[1]);
        $this->assertEquals($plaintext, $decrypted);
    }

    public function testCorruptedNonce() {
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        $plaintext = 'corrupt nonce';
        $encrypted = $this->kyberium->encrypt($plaintext);
        $nonce = $encrypted[1];
        $nonce[0] = chr(ord($nonce[0]) ^ 0xFF); // Corrompre le nonce
        $this->expectException(Exception::class);
        $this->kyberium->decrypt($encrypted[0], $nonce);
    }

    public function testEncryptWithAAD() {
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        $message = 'AAD test';
        $aad = 'context-info';
        $encrypted = $this->kyberium->encryptWithAAD($message, $aad);
        $this->assertNotNull($encrypted);
        $decrypted = $this->kyberium->decryptWithAAD($encrypted[0], $encrypted[1], $aad);
        $this->assertEquals($message, $decrypted);
    }

    public function testStressEncryption() {
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        for ($i = 0; $i < 100; $i++) {
            $msg = 'stress-' . $i;
            $encrypted = $this->kyberium->encrypt($msg);
            $decrypted = $this->kyberium->decrypt($encrypted[0], $encrypted[1]);
            $this->assertEquals($msg, $decrypted);
        }
    }
} 