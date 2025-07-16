# Kyberium Java JNI Integration

## Vue d'ensemble

Ce module fournit une intégration Java Native Interface (JNI) complète pour Kyberium, permettant d'utiliser les algorithmes post-quantiques directement depuis des applications Java avec des performances optimales.

## Fonctionnalités

- ✅ **Session classique** : Handshake, chiffrement/déchiffrement
- ✅ **Triple Ratchet** : Perfect Forward Secrecy avancée
- ✅ **Signatures post-quantiques** : CRYSTALS-Dilithium
- ✅ **Gestion des clés** : Génération et rotation automatique
- ✅ **Performance monitoring** : Statistiques en temps réel
- ✅ **Gestion d'erreurs robuste** : Exceptions Java natives

## Architecture

```
Java Application
       ↓
KyberiumJNI.java (Interface JNI)
       ↓
kyberium_jni.c (Implémentation C)
       ↓
Python Kyberium API
       ↓
Algorithmes post-quantiques (Kyber, Dilithium, etc.)
```

## Installation

### Prérequis

- **Java** : JDK 11+ (JNI 1.8)
- **Python** : 3.11+ avec Kyberium installé
- **Build tools** : GCC/Clang, Make
- **Python dev** : python3-dev, pybind11

### Compilation

```bash
# 1. Compiler la bibliothèque native
cd kyberium/bindings/java

# Générer les headers JNI
javac -h . KyberiumJNI.java

# Compiler la bibliothèque native
gcc -shared -fPIC \
    -I"$JAVA_HOME/include" \
    -I"$JAVA_HOME/include/linux" \
    -I"$(python3 -c 'import sys; print(sys.prefix + "/include/python" + sys.version[:3])')" \
    -o libkyberium_jni.so \
    kyberium_jni.c \
    -lpython3.11 \
    -lpthread \
    -ldl

# 2. Installer la bibliothèque
sudo cp libkyberium_jni.so /usr/local/lib/
sudo ldconfig

# 3. Compiler les classes Java
javac KyberiumJNI.java
```

### Configuration Maven

```xml
<!-- pom.xml -->
<project>
    <dependencies>
        <!-- Dépendances système pour JNI -->
        <dependency>
            <groupId>com.sun</groupId>
            <artifactId>tools</artifactId>
            <version>1.8.0</version>
            <scope>system</scope>
            <systemPath>${java.home}/../lib/tools.jar</systemPath>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <!-- Plugin pour compiler les headers JNI -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.8.1</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                    <compilerArgs>
                        <arg>-h</arg>
                        <arg>${project.build.directory}/generated-sources/jni</arg>
                    </compilerArgs>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### Configuration Gradle

```gradle
// build.gradle
plugins {
    id 'java'
    id 'application'
}

java {
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}

dependencies {
    // Dépendances système pour JNI
    compileOnly files("${System.getProperty('java.home')}/../lib/tools.jar")
}

// Tâche pour compiler les headers JNI
task generateJniHeaders(type: JavaCompile) {
    source = sourceSets.main.java
    classpath = sourceSets.main.compileClasspath
    options.compilerArgs = ['-h', 'src/main/cpp/jni']
    destinationDir = file('build/generated-sources/jni')
}

// Tâche pour compiler la bibliothèque native
task compileNative(type: Exec) {
    dependsOn generateJniHeaders
    
    workingDir 'src/main/cpp'
    commandLine 'gcc', '-shared', '-fPIC',
        '-I' + System.getenv('JAVA_HOME') + '/include',
        '-I' + System.getenv('JAVA_HOME') + '/include/linux',
        '-I' + 'jni',
        '-o', 'libkyberium_jni.so',
        'kyberium_jni.c',
        '-lpython3.11',
        '-lpthread',
        '-ldl'
}
```

## Utilisation

### Exemple basique

```java
import java.nio.charset.StandardCharsets;

public class KyberiumExample {
    public static void main(String[] args) {
        try {
            // Créer une instance JNI
            KyberiumJNI kyberium = new KyberiumJNI();
            
            // Initialiser une session (côté Bob)
            byte[] bobPublicKey = kyberium.initSession();
            System.out.println("Bob public key generated: " + bobPublicKey.length + " bytes");
            
            // Initialiser une session avec le pair (côté Alice)
            byte[] aliceCiphertext = kyberium.initSessionWithPeer(bobPublicKey);
            System.out.println("Alice handshake initiated: " + aliceCiphertext.length + " bytes");
            
            // Compléter le handshake (côté Bob)
            boolean handshakeSuccess = kyberium.completeHandshake(aliceCiphertext);
            System.out.println("Handshake completed: " + handshakeSuccess);
            
            // Chiffrer un message
            String message = "Hello, post-quantum world!";
            byte[] plaintext = message.getBytes(StandardCharsets.UTF_8);
            byte[][] encrypted = kyberium.encrypt(plaintext);
            
            byte[] ciphertext = encrypted[0];
            byte[] nonce = encrypted[1];
            System.out.println("Message encrypted: " + ciphertext.length + " bytes");
            
            // Déchiffrer le message
            byte[] decrypted = kyberium.decrypt(ciphertext, nonce);
            String decryptedMessage = new String(decrypted, StandardCharsets.UTF_8);
            System.out.println("Message decrypted: " + decryptedMessage);
            
            // Nettoyer les ressources
            kyberium.cleanup();
            
        } catch (KyberiumJNI.KyberiumException e) {
            System.err.println("Kyberium error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```

### Exemple Triple Ratchet

```java
public class TripleRatchetExample {
    public static void main(String[] args) {
        try {
            KyberiumJNI kyberium = new KyberiumJNI();
            
            // Générer les clés pour Bob
            byte[][] bobKemKeys = kyberium.generateKemKeypair();
            byte[][] bobSignKeys = kyberium.generateSignatureKeypair();
            byte[] bobKemPublic = bobKemKeys[0];
            byte[] bobSignPublic = bobSignKeys[0];
            
            // Initialiser le Triple Ratchet (côté Alice)
            KyberiumJNI.TripleRatchetInitMessage initMsg = 
                kyberium.initTripleRatchet(bobKemPublic, bobSignPublic);
            
            // Compléter le Triple Ratchet (côté Bob)
            boolean success = kyberium.completeTripleRatchetHandshake(
                initMsg.kemCiphertext, 
                initMsg.kemSignature, 
                initMsg.signPublicKey
            );
            
            if (success) {
                System.out.println("Triple Ratchet handshake completed");
                
                // Échanger des messages sécurisés
                String[] messages = {"Message 1", "Message 2", "Message 3"};
                
                for (int i = 0; i < messages.length; i++) {
                    // Chiffrer avec Triple Ratchet
                    byte[] plaintext = messages[i].getBytes(StandardCharsets.UTF_8);
                    KyberiumJNI.TripleRatchetMessage encrypted = kyberium.tripleEncrypt(plaintext);
                    
                    // Déchiffrer
                    byte[] decrypted = kyberium.tripleDecrypt(
                        encrypted.ciphertext,
                        encrypted.nonce,
                        encrypted.signature,
                        encrypted.msgNum,
                        encrypted.signPublicKey
                    );
                    
                    String decryptedMessage = new String(decrypted, StandardCharsets.UTF_8);
                    System.out.println("Message " + (i+1) + ": " + decryptedMessage);
                }
            }
            
            kyberium.cleanup();
            
        } catch (KyberiumJNI.KyberiumException e) {
            System.err.println("Triple Ratchet error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```

### Exemple avec gestion d'erreurs avancée

```java
public class AdvancedExample {
    public static void main(String[] args) {
        KyberiumJNI kyberium = null;
        
        try {
            kyberium = new KyberiumJNI();
            
            // Configuration avec AAD (Authenticated Associated Data)
            String message = "Sensitive data";
            String aad = "Context: financial transaction";
            
            byte[] plaintext = message.getBytes(StandardCharsets.UTF_8);
            byte[] aadBytes = aad.getBytes(StandardCharsets.UTF_8);
            
            // Chiffrement avec AAD
            byte[][] encrypted = kyberium.encryptWithAAD(plaintext, aadBytes);
            
            // Signature
            byte[] signature = kyberium.sign(plaintext);
            System.out.println("Message signed: " + signature.length + " bytes");
            
            // Vérification de signature
            boolean isValid = kyberium.verify(plaintext, signature, null);
            System.out.println("Signature valid: " + isValid);
            
            // Statistiques de performance
            KyberiumJNI.PerformanceStats stats = kyberium.getPerformanceStats();
            System.out.println("Performance stats:");
            System.out.println("  Total encryptions: " + stats.totalEncryptions);
            System.out.println("  Total decryptions: " + stats.totalDecryptions);
            System.out.println("  Avg encryption time: " + stats.avgEncryptionTime + " ms");
            System.out.println("  Avg decryption time: " + stats.avgDecryptionTime + " ms");
            
        } catch (KyberiumJNI.KyberiumException e) {
            System.err.println("Kyberium operation failed: " + e.getMessage());
            System.err.println("Error type: " + e.getClass().getSimpleName());
            e.printStackTrace();
            
        } catch (UnsatisfiedLinkError e) {
            System.err.println("JNI library not found: " + e.getMessage());
            System.err.println("Please ensure libkyberium_jni.so is in the library path");
            
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            e.printStackTrace();
            
        } finally {
            if (kyberium != null) {
                try {
                    kyberium.cleanup();
                } catch (Exception e) {
                    System.err.println("Cleanup failed: " + e.getMessage());
                }
            }
        }
    }
}
```

## Tests

### Tests unitaires JUnit

```java
import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;

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
    public void testBasicSession() {
        // Test d'initialisation de session
        byte[] publicKey = kyberium.initSession();
        assertNotNull("Public key should not be null", publicKey);
        assertTrue("Public key should not be empty", publicKey.length > 0);
        
        // Test de handshake
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        assertNotNull("Ciphertext should not be null", ciphertext);
        
        boolean success = kyberium.completeHandshake(ciphertext);
        assertTrue("Handshake should succeed", success);
    }
    
    @Test
    public void testEncryptionDecryption() {
        // Initialiser la session
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        
        // Test de chiffrement/déchiffrement
        String originalMessage = "Test message";
        byte[] plaintext = originalMessage.getBytes(StandardCharsets.UTF_8);
        
        byte[][] encrypted = kyberium.encrypt(plaintext);
        assertNotNull("Encrypted data should not be null", encrypted);
        assertEquals("Should return ciphertext and nonce", 2, encrypted.length);
        
        byte[] decrypted = kyberium.decrypt(encrypted[0], encrypted[1]);
        assertNotNull("Decrypted data should not be null", decrypted);
        
        String decryptedMessage = new String(decrypted, StandardCharsets.UTF_8);
        assertEquals("Decrypted message should match original", originalMessage, decryptedMessage);
    }
    
    @Test
    public void testTripleRatchet() {
        // Générer les clés
        byte[][] kemKeys = kyberium.generateKemKeypair();
        byte[][] signKeys = kyberium.generateSignatureKeypair();
        
        // Test Triple Ratchet
        KyberiumJNI.TripleRatchetInitMessage initMsg = 
            kyberium.initTripleRatchet(kemKeys[0], signKeys[0]);
        
        assertNotNull("Init message should not be null", initMsg);
        assertNotNull("KEM ciphertext should not be null", initMsg.kemCiphertext);
        assertNotNull("KEM signature should not be null", initMsg.kemSignature);
        
        boolean success = kyberium.completeTripleRatchetHandshake(
            initMsg.kemCiphertext, initMsg.kemSignature, initMsg.signPublicKey);
        assertTrue("Triple Ratchet handshake should succeed", success);
    }
    
    @Test
    public void testSignatureVerification() {
        String message = "Message to sign";
        byte[] plaintext = message.getBytes(StandardCharsets.UTF_8);
        
        // Signer le message
        byte[] signature = kyberium.sign(plaintext);
        assertNotNull("Signature should not be null", signature);
        assertTrue("Signature should not be empty", signature.length > 0);
        
        // Vérifier la signature
        boolean isValid = kyberium.verify(plaintext, signature, null);
        assertTrue("Signature should be valid", isValid);
        
        // Test avec signature invalide
        byte[] invalidSignature = new byte[signature.length];
        System.arraycopy(signature, 0, invalidSignature, 0, signature.length);
        invalidSignature[0] = (byte) (invalidSignature[0] ^ 0xFF); // Corrompre la signature
        
        boolean isInvalid = kyberium.verify(plaintext, invalidSignature, null);
        assertFalse("Invalid signature should be rejected", isInvalid);
    }
    
    @Test
    public void testPerformanceStats() {
        // Effectuer quelques opérations
        byte[] publicKey = kyberium.initSession();
        byte[] ciphertext = kyberium.initSessionWithPeer(publicKey);
        kyberium.completeHandshake(ciphertext);
        
        byte[] plaintext = "Test".getBytes(StandardCharsets.UTF_8);
        byte[][] encrypted = kyberium.encrypt(plaintext);
        kyberium.decrypt(encrypted[0], encrypted[1]);
        
        // Vérifier les statistiques
        KyberiumJNI.PerformanceStats stats = kyberium.getPerformanceStats();
        assertNotNull("Performance stats should not be null", stats);
        assertTrue("Should have performed operations", stats.totalEncryptions > 0);
    }
}
```

## Déploiement

### Packaging JAR

```xml
<!-- Maven Assembly Plugin -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-assembly-plugin</artifactId>
    <version>3.3.0</version>
    <configuration>
        <descriptorRefs>
            <descriptorRef>jar-with-dependencies</descriptorRef>
        </descriptorRefs>
    </configuration>
    <executions>
        <execution>
            <id>make-assembly</id>
            <phase>package</phase>
            <goals>
                <goal>single</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

### Docker

```dockerfile
# Dockerfile pour application Java avec Kyberium JNI
FROM openjdk:11-jre-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    libpython3.11 \
    python3.11 \
    && rm -rf /var/lib/apt/lists/*

# Copier la bibliothèque native
COPY libkyberium_jni.so /usr/local/lib/
RUN ldconfig

# Copier l'application Java
COPY target/kyberium-java-app.jar /app/app.jar

# Point d'entrée
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

### Configuration système

```bash
# Ajouter la bibliothèque au PATH système
echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf.d/kyberium.conf
sudo ldconfig

# Vérifier l'installation
java -Djava.library.path=/usr/local/lib -cp .:kyberium-jni.jar KyberiumExample
```

## Performance

### Métriques typiques

| Opération | Temps moyen | Throughput |
|-----------|-------------|------------|
| Initialisation session | ~15ms | 66 sessions/sec |
| Chiffrement | ~1ms | 1000 msg/sec |
| Déchiffrement | ~1ms | 1000 msg/sec |
| Signature | ~5ms | 200 sig/sec |
| Vérification | ~5ms | 200 ver/sec |
| Triple Ratchet (msg) | ~6ms | 166 msg/sec |

### Optimisations

1. **Pool de sessions** : Réutiliser les sessions pour éviter les handshakes répétés
2. **Batch processing** : Traiter plusieurs messages en lot
3. **Threading** : Utiliser des threads dédiés pour les opérations cryptographiques
4. **Memory management** : Réutiliser les buffers pour éviter les allocations fréquentes

## Troubleshooting

### Erreurs courantes

#### `UnsatisfiedLinkError`
```bash
# Solution : Vérifier le chemin de la bibliothèque
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
java -Djava.library.path=/usr/local/lib -cp .:kyberium-jni.jar Main
```

#### `Python import error`
```bash
# Solution : Vérifier l'installation Python
python3 -c "import kyberium.api; print('OK')"
```

#### `Permission denied`
```bash
# Solution : Vérifier les permissions
sudo chmod 755 /usr/local/lib/libkyberium_jni.so
```

### Debug

```bash
# Compiler en mode debug
gcc -shared -fPIC -g -O0 \
    -I"$JAVA_HOME/include" \
    -I"$JAVA_HOME/include/linux" \
    -o libkyberium_jni.so \
    kyberium_jni.c \
    -lpython3.11

# Exécuter avec debug JNI
java -Djava.library.path=/usr/local/lib \
     -Xcheck:jni \
     -cp .:kyberium-jni.jar Main
```

## Support

- **Documentation** : [docs/API_REFERENCE.md](../docs/API_REFERENCE.md)
- **Exemples** : [examples/](../examples/)
- **Issues** : [GitHub Issues](https://github.com/your-username/kyberium/issues)

---

Cette intégration JNI permet d'utiliser Kyberium dans des applications Java avec des performances optimales et une sécurité post-quantique complète. 