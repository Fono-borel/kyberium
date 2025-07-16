import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;
import java.nio.charset.StandardCharsets;

public class KyberiumJNITest {
    private KyberiumJNI kyberium;

    @Before
    public void setUp() {
        kyberium = new KyberiumJNI();
    }

    @After
    public void tearDown() {
        if (kyberium != null) {
            kyberium.cleanup();
        }
    }

    @Test
    public void testSessionHandshake() {
        byte[] publicKey = kyberium.initSession();
        assertNotNull(publicKey);
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        assertNotNull(ciphertext);
        boolean success = kyberium.completeHandshake(ciphertext);
        assertTrue(success);
    }

    @Test
    public void testEncryptionDecryption() {
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        String message = "Test message";
        byte[] plaintext = message.getBytes(StandardCharsets.UTF_8);
        byte[][] encrypted = kyberium.encrypt(plaintext);
        assertNotNull(encrypted);
        assertEquals(2, encrypted.length);
        byte[] decrypted = kyberium.decrypt(encrypted[0], encrypted[1]);
        assertNotNull(decrypted);
        assertEquals(message, new String(decrypted, StandardCharsets.UTF_8));
    }

    @Test
    public void testTripleRatchet() {
        byte[][] kemKeys = kyberium.generateKemKeypair();
        byte[][] signKeys = kyberium.generateSignatureKeypair();
        KyberiumJNI.TripleRatchetInitMessage initMsg = kyberium.initTripleRatchet(kemKeys[0], signKeys[0]);
        assertNotNull(initMsg);
        boolean success = kyberium.completeTripleRatchetHandshake(initMsg.kemCiphertext, initMsg.kemSignature, initMsg.signPublicKey);
        assertTrue(success);
        String msg = "Triple ratchet test";
        KyberiumJNI.TripleRatchetMessage encrypted = kyberium.tripleEncrypt(msg.getBytes(StandardCharsets.UTF_8));
        assertNotNull(encrypted);
        byte[] decrypted = kyberium.tripleDecrypt(encrypted.ciphertext, encrypted.nonce, encrypted.signature, encrypted.msgNum, encrypted.signPublicKey);
        assertEquals(msg, new String(decrypted, StandardCharsets.UTF_8));
    }

    @Test
    public void testSignatureVerification() {
        String message = "Message to sign";
        byte[] plaintext = message.getBytes(StandardCharsets.UTF_8);
        byte[] signature = kyberium.sign(plaintext);
        assertNotNull(signature);
        boolean isValid = kyberium.verify(plaintext, signature, null);
        assertTrue(isValid);
        signature[0] = (byte) (signature[0] ^ 0xFF); // Corrompre la signature
        boolean isInvalid = kyberium.verify(plaintext, signature, null);
        assertFalse(isInvalid);
    }

    @Test
    public void testPerformanceStats() {
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        byte[] plaintext = "Test".getBytes(StandardCharsets.UTF_8);
        byte[][] encrypted = kyberium.encrypt(plaintext);
        kyberium.decrypt(encrypted[0], encrypted[1]);
        KyberiumJNI.PerformanceStats stats = kyberium.getPerformanceStats();
        assertNotNull(stats);
        assertTrue(stats.totalEncryptions > 0);
    }

    @Test(expected = KyberiumJNI.KyberiumException.class)
    public void testErrorHandling() {
        kyberium.decrypt(null, null); // Doit lever une exception
    }

    @Test
    public void testEmptyMessage() {
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        byte[] plaintext = new byte[0];
        byte[][] encrypted = kyberium.encrypt(plaintext);
        assertNotNull(encrypted);
        assertEquals(2, encrypted.length);
        byte[] decrypted = kyberium.decrypt(encrypted[0], encrypted[1]);
        assertNotNull(decrypted);
        assertEquals(0, decrypted.length);
    }

    @Test
    public void testLongMessage() {
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        byte[] plaintext = new byte[10_000];
        for (int i = 0; i < plaintext.length; i++) plaintext[i] = (byte) (i % 256);
        byte[][] encrypted = kyberium.encrypt(plaintext);
        assertNotNull(encrypted);
        assertEquals(2, encrypted.length);
        byte[] decrypted = kyberium.decrypt(encrypted[0], encrypted[1]);
        assertNotNull(decrypted);
        assertArrayEquals(plaintext, decrypted);
    }

    @Test
    public void testCorruptedNonce() {
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        byte[] plaintext = "corrupt nonce".getBytes(StandardCharsets.UTF_8);
        byte[][] encrypted = kyberium.encrypt(plaintext);
        encrypted[1][0] ^= 0xFF; // Corrompre le nonce
        try {
            kyberium.decrypt(encrypted[0], encrypted[1]);
            fail("Should throw KyberiumException on corrupted nonce");
        } catch (KyberiumJNI.KyberiumException e) {
            // OK
        }
    }

    @Test
    public void testEncryptWithAAD() {
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        String message = "AAD test";
        String aad = "context-info";
        byte[][] encrypted = kyberium.encryptWithAAD(message.getBytes(StandardCharsets.UTF_8), aad.getBytes(StandardCharsets.UTF_8));
        assertNotNull(encrypted);
        byte[] decrypted = kyberium.decryptWithAAD(encrypted[0], encrypted[1], aad.getBytes(StandardCharsets.UTF_8));
        assertEquals(message, new String(decrypted, StandardCharsets.UTF_8));
    }

    @Test(timeout = 5000)
    public void testStressEncryption() {
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        for (int i = 0; i < 100; i++) {
            String msg = "stress-" + i;
            byte[][] encrypted = kyberium.encrypt(msg.getBytes(StandardCharsets.UTF_8));
            byte[] decrypted = kyberium.decrypt(encrypted[0], encrypted[1]);
            assertEquals(msg, new String(decrypted, StandardCharsets.UTF_8));
        }
    }
} 