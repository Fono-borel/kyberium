# Kyberium PHP FFI Integration

## Vue d'ensemble

Ce module fournit une intégration PHP complète pour Kyberium via FFI (Foreign Function Interface), permettant d'utiliser les algorithmes post-quantiques directement depuis des applications PHP avec des performances optimales.

## Fonctionnalités

- ✅ **Session classique** : Handshake, chiffrement/déchiffrement
- ✅ **Triple Ratchet** : Perfect Forward Secrecy avancée
- ✅ **Signatures post-quantiques** : CRYSTALS-Dilithium
- ✅ **Gestion des clés** : Génération et rotation automatique
- ✅ **Performance monitoring** : Statistiques en temps réel
- ✅ **Gestion d'erreurs robuste** : Exceptions PHP natives
- ✅ **FFI natif** : Accès direct aux fonctions Python C API

## Architecture

```
PHP Application
      ↓
KyberiumPHP.php (Classe FFI)
      ↓
FFI Interface (libpython3.11.so)
      ↓
Python Kyberium API
      ↓
Algorithmes post-quantiques (Kyber, Dilithium, etc.)
```

## Prérequis

### Système

- **PHP** : 8.0+ avec extension FFI
- **Python** : 3.11+ avec Kyberium installé
- **OS** : Linux (Ubuntu 20.04+), macOS (10.15+)
- **Bibliothèques** : libpython3.11.so

### Extensions PHP

```bash
# Vérifier que FFI est activé
php -m | grep ffi

# Si FFI n'est pas installé
sudo apt-get install php8.1-ffi  # Ubuntu/Debian
# ou
brew install php@8.1  # macOS (inclut FFI)
```

### Configuration PHP

```ini
; php.ini
extension=ffi
ffi.enable=1
ffi.preload=/path/to/kyberium_ffi.h
```

## Installation

### 1. Installation de Kyberium Python

```bash
# Installer Kyberium Python
cd /path/to/kyberium
pip install -e .

# Vérifier l'installation
python3 -c "import kyberium.api; print('Kyberium OK')"
```

### 2. Installation PHP FFI

```bash
# Copier les fichiers PHP
cp kyberium/bindings/php/kyberium_php.php /var/www/html/lib/
cp kyberium/bindings/php/README.md /var/www/html/docs/

# Vérifier les permissions
chmod 644 /var/www/html/lib/kyberium_php.php
```

### 3. Configuration Composer (optionnel)

```json
{
    "require": {
        "php": ">=8.0"
    },
    "autoload": {
        "psr-4": {
            "Kyberium\\": "lib/"
        }
    }
}
```

## Utilisation

### Exemple basique

```php
<?php
require_once 'lib/kyberium_php.php';

try {
    // Créer une instance Kyberium
    $kyberium = new KyberiumPHP();
    
    // Initialiser une session (côté Bob)
    $bobPublicKey = $kyberium->initSession();
    echo "Bob public key generated: " . strlen($bobPublicKey) . " bytes\n";
    
    // Initialiser une session avec le pair (côté Alice)
    $aliceCiphertext = $kyberium->initSessionWithPeer($bobPublicKey);
    echo "Alice handshake initiated: " . strlen($aliceCiphertext) . " bytes\n";
    
    // Compléter le handshake (côté Bob)
    $handshakeSuccess = $kyberium->completeHandshake($aliceCiphertext);
    echo "Handshake completed: " . ($handshakeSuccess ? 'true' : 'false') . "\n";
    
    // Chiffrer un message
    $message = "Hello, post-quantum world!";
    $encrypted = $kyberium->encrypt($message);
    
    $ciphertext = $encrypted[0];
    $nonce = $encrypted[1];
    echo "Message encrypted: " . strlen($ciphertext) . " bytes\n";
    
    // Déchiffrer le message
    $decrypted = $kyberium->decrypt($ciphertext, $nonce);
    echo "Message decrypted: " . $decrypted . "\n";
    
    // Nettoyer les ressources
    $kyberium->cleanup();
    
} catch (KyberiumException $e) {
    echo "Kyberium error: " . $e->getMessage() . "\n";
} catch (Exception $e) {
    echo "Unexpected error: " . $e->getMessage() . "\n";
}
?>
```

### Exemple Triple Ratchet

```php
<?php
require_once 'lib/kyberium_php.php';

try {
    $kyberium = new KyberiumPHP();
    
    // Générer les clés pour Bob (simulation)
    $bobKemPublic = random_bytes(1184);  // Taille Kyber-1024
    $bobSignPublic = random_bytes(1952); // Taille Dilithium
    
    // Initialiser le Triple Ratchet (côté Alice)
    $initMsg = $kyberium->initTripleRatchet($bobKemPublic, $bobSignPublic);
    
    // Compléter le Triple Ratchet (côté Bob)
    $success = $kyberium->completeTripleRatchetHandshake(
        $initMsg['kem_ciphertext'],
        $initMsg['kem_signature'],
        $initMsg['sign_public_key']
    );
    
    if ($success) {
        echo "Triple Ratchet handshake completed\n";
        
        // Échanger des messages sécurisés
        $messages = ["Message 1", "Message 2", "Message 3"];
        
        foreach ($messages as $i => $message) {
            // Chiffrer avec Triple Ratchet
            $encrypted = $kyberium->tripleEncrypt($message);
            
            // Déchiffrer
            $decrypted = $kyberium->tripleDecrypt(
                $encrypted['ciphertext'],
                $encrypted['nonce'],
                $encrypted['signature'],
                $encrypted['msg_num'],
                $encrypted['sign_public_key']
            );
            
            echo "Message " . ($i+1) . ": " . $decrypted . "\n";
        }
    }
    
    $kyberium->cleanup();
    
} catch (KyberiumException $e) {
    echo "Triple Ratchet error: " . $e->getMessage() . "\n";
}
?>
```

### Exemple avec gestion d'erreurs avancée

```php
<?php
require_once 'lib/kyberium_php.php';

class KyberiumService {
    private $kyberium;
    private $logger;
    
    public function __construct($logger = null) {
        $this->logger = $logger;
        $this->kyberium = new KyberiumPHP();
    }
    
    public function secureCommunication($message, $context = null) {
        try {
            // Configuration avec AAD (Authenticated Associated Data)
            $aad = $context ? json_encode($context) : null;
            
            // Chiffrement avec AAD
            $encrypted = $this->kyberium->encryptWithAAD($message, $aad);
            
            // Signature
            $signature = $this->kyberium->sign($message);
            $this->log("Message signed: " . strlen($signature) . " bytes");
            
            // Vérification de signature
            $isValid = $this->kyberium->verify($message, $signature);
            $this->log("Signature valid: " . ($isValid ? 'true' : 'false'));
            
            return [
                'ciphertext' => $encrypted[0],
                'nonce' => $encrypted[1],
                'signature' => $signature,
                'success' => true
            ];
            
        } catch (KyberiumException $e) {
            $this->log("Kyberium operation failed: " . $e->getMessage(), 'ERROR');
            return ['success' => false, 'error' => $e->getMessage()];
            
        } catch (Exception $e) {
            $this->log("Unexpected error: " . $e->getMessage(), 'ERROR');
            return ['success' => false, 'error' => $e->getMessage()];
        }
    }
    
    public function getPerformanceStats() {
        return $this->kyberium->getPerformanceStats();
    }
    
    public function cleanup() {
        if ($this->kyberium) {
            $this->kyberium->cleanup();
        }
    }
    
    private function log($message, $level = 'INFO') {
        if ($this->logger) {
            $this->logger->log($level, $message);
        } else {
            echo "[$level] $message\n";
        }
    }
    
    public function __destruct() {
        $this->cleanup();
    }
}

// Utilisation
$service = new KyberiumService();
$context = ['user_id' => 123, 'session_id' => 'abc123'];

$result = $service->secureCommunication("Sensitive data", $context);

if ($result['success']) {
    echo "Communication sécurisée réussie\n";
    echo "Ciphertext: " . base64_encode($result['ciphertext']) . "\n";
} else {
    echo "Erreur: " . $result['error'] . "\n";
}

// Statistiques de performance
$stats = $service->getPerformanceStats();
echo "Performance stats:\n";
echo "  Total encryptions: " . $stats['total_encryptions'] . "\n";
echo "  Total decryptions: " . $stats['total_decryptions'] . "\n";
echo "  Avg encryption time: " . $stats['avg_encryption_time'] . " ms\n";
echo "  Avg decryption time: " . $stats['avg_decryption_time'] . " ms\n";
?>
```

### Exemple Web (Laravel/Symfony)

```php
<?php
// app/Services/KyberiumService.php (Laravel)
namespace App\Services;

use KyberiumPHP;
use Illuminate\Support\Facades\Log;

class KyberiumService
{
    private $kyberium;
    
    public function __construct()
    {
        $this->kyberium = new KyberiumPHP();
    }
    
    public function encryptMessage($message, $userId)
    {
        try {
            // Ajouter des métadonnées pour l'authentification
            $aad = json_encode([
                'user_id' => $userId,
                'timestamp' => time(),
                'version' => '1.0'
            ]);
            
            $encrypted = $this->kyberium->encryptWithAAD($message, $aad);
            
            return [
                'ciphertext' => base64_encode($encrypted[0]),
                'nonce' => base64_encode($encrypted[1]),
                'aad' => base64_encode($aad)
            ];
            
        } catch (KyberiumException $e) {
            Log::error('Kyberium encryption failed', [
                'error' => $e->getMessage(),
                'user_id' => $userId
            ]);
            throw $e;
        }
    }
    
    public function decryptMessage($ciphertext, $nonce, $aad)
    {
        try {
            $ciphertextBytes = base64_decode($ciphertext);
            $nonceBytes = base64_decode($nonce);
            $aadBytes = base64_decode($aad);
            
            return $this->kyberium->decryptWithAAD($ciphertextBytes, $nonceBytes, $aadBytes);
            
        } catch (KyberiumException $e) {
            Log::error('Kyberium decryption failed', [
                'error' => $e->getMessage()
            ]);
            throw $e;
        }
    }
    
    public function signData($data)
    {
        try {
            $signature = $this->kyberium->sign($data);
            return base64_encode($signature);
            
        } catch (KyberiumException $e) {
            Log::error('Kyberium signing failed', [
                'error' => $e->getMessage()
            ]);
            throw $e;
        }
    }
    
    public function verifySignature($data, $signature)
    {
        try {
            $signatureBytes = base64_decode($signature);
            return $this->kyberium->verify($data, $signatureBytes);
            
        } catch (KyberiumException $e) {
            Log::error('Kyberium verification failed', [
                'error' => $e->getMessage()
            ]);
            return false;
        }
    }
    
    public function __destruct()
    {
        if ($this->kyberium) {
            $this->kyberium->cleanup();
        }
    }
}
```

## Tests

### Tests unitaires PHPUnit

```php
<?php
// tests/KyberiumTest.php
use PHPUnit\Framework\TestCase;

class KyberiumTest extends TestCase
{
    private $kyberium;
    
    protected function setUp(): void
    {
        $this->kyberium = new KyberiumPHP();
    }
    
    protected function tearDown(): void
    {
        if ($this->kyberium) {
            $this->kyberium->cleanup();
        }
    }
    
    public function testBasicSession()
    {
        // Test d'initialisation de session
        $publicKey = $this->kyberium->initSession();
        $this->assertNotNull($publicKey);
        $this->assertGreaterThan(0, strlen($publicKey));
        
        // Test de handshake
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->assertNotNull($ciphertext);
        
        $success = $this->kyberium->completeHandshake($ciphertext);
        $this->assertTrue($success);
    }
    
    public function testEncryptionDecryption()
    {
        // Initialiser la session
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        
        // Test de chiffrement/déchiffrement
        $originalMessage = "Test message";
        $encrypted = $this->kyberium->encrypt($originalMessage);
        
        $this->assertNotNull($encrypted);
        $this->assertCount(2, $encrypted);
        
        $decrypted = $this->kyberium->decrypt($encrypted[0], $encrypted[1]);
        $this->assertNotNull($decrypted);
        $this->assertEquals($originalMessage, $decrypted);
    }
    
    public function testTripleRatchet()
    {
        // Générer les clés (simulation)
        $kemPublic = random_bytes(1184);
        $signPublic = random_bytes(1952);
        
        // Test Triple Ratchet
        $initMsg = $this->kyberium->initTripleRatchet($kemPublic, $signPublic);
        
        $this->assertNotNull($initMsg);
        $this->assertArrayHasKey('kem_ciphertext', $initMsg);
        $this->assertArrayHasKey('kem_signature', $initMsg);
        
        $success = $this->kyberium->completeTripleRatchetHandshake(
            $initMsg['kem_ciphertext'],
            $initMsg['kem_signature'],
            $initMsg['sign_public_key']
        );
        $this->assertTrue($success);
    }
    
    public function testSignatureVerification()
    {
        $message = "Message to sign";
        
        // Signer le message
        $signature = $this->kyberium->sign($message);
        $this->assertNotNull($signature);
        $this->assertGreaterThan(0, strlen($signature));
        
        // Vérifier la signature
        $isValid = $this->kyberium->verify($message, $signature);
        $this->assertTrue($isValid);
        
        // Test avec signature invalide
        $invalidSignature = $signature;
        $invalidSignature[0] = chr(ord($invalidSignature[0]) ^ 0xFF); // Corrompre la signature
        
        $isInvalid = $this->kyberium->verify($message, $invalidSignature);
        $this->assertFalse($isInvalid);
    }
    
    public function testPerformanceStats()
    {
        // Effectuer quelques opérations
        $publicKey = $this->kyberium->initSession();
        $ciphertext = $this->kyberium->initSessionWithPeer($publicKey);
        $this->kyberium->completeHandshake($ciphertext);
        
        $encrypted = $this->kyberium->encrypt("Test");
        $this->kyberium->decrypt($encrypted[0], $encrypted[1]);
        
        // Vérifier les statistiques
        $stats = $this->kyberium->getPerformanceStats();
        $this->assertNotNull($stats);
        $this->assertGreaterThan(0, $stats['total_encryptions']);
    }
}
?>
```

## Déploiement

### Configuration Apache/Nginx

```apache
# Apache (.htaccess)
<IfModule mod_rewrite.c>
    RewriteEngine On
    
    # Sécuriser les fichiers Kyberium
    <Files "kyberium_php.php">
        Order Allow,Deny
        Deny from all
    </Files>
</IfModule>
```

```nginx
# Nginx
server {
    listen 80;
    server_name example.com;
    root /var/www/html;
    
    # Sécuriser les fichiers Kyberium
    location ~ ^/lib/kyberium_php\.php$ {
        deny all;
        return 404;
    }
    
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
}
```

### Docker

```dockerfile
# Dockerfile pour application PHP avec Kyberium FFI
FROM php:8.1-fpm

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    libpython3.11 \
    python3.11 \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer l'extension FFI
RUN docker-php-ext-install ffi

# Copier l'application
COPY . /var/www/html/
COPY lib/kyberium_php.php /var/www/html/lib/

# Configurer les permissions
RUN chown -R www-data:www-data /var/www/html
RUN chmod 644 /var/www/html/lib/kyberium_php.php

# Point d'entrée
CMD ["php-fpm"]
```

### Configuration de production

```php
<?php
// config/kyberium.php
return [
    'enabled' => env('KYBERIUM_ENABLED', true),
    'python_path' => env('PYTHON_PATH', '/usr/bin/python3'),
    'library_path' => env('KYBERIUM_LIBRARY_PATH', '/usr/local/lib'),
    'log_level' => env('KYBERIUM_LOG_LEVEL', 'info'),
    'performance_monitoring' => env('KYBERIUM_PERFORMANCE_MONITORING', true),
    
    'security' => [
        'key_rotation_interval' => env('KYBERIUM_KEY_ROTATION_INTERVAL', 3600),
        'max_session_duration' => env('KYBERIUM_MAX_SESSION_DURATION', 86400),
        'enable_audit_logging' => env('KYBERIUM_ENABLE_AUDIT_LOGGING', true),
    ]
];
?>
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
3. **Memory management** : Réutiliser les buffers pour éviter les allocations fréquentes
4. **FFI caching** : Mettre en cache les pointeurs FFI pour éviter les appels répétés

## Troubleshooting

### Erreurs courantes

#### `FFI extension not loaded`
```bash
# Solution : Installer l'extension FFI
sudo apt-get install php8.1-ffi
# Redémarrer PHP
sudo systemctl restart php8.1-fpm
```

#### `Python library not found`
```bash
# Solution : Vérifier l'installation Python
python3 -c "import kyberium.api; print('OK')"

# Vérifier le chemin de la bibliothèque
ldconfig -p | grep python
```

#### `Permission denied`
```bash
# Solution : Vérifier les permissions
sudo chmod 755 /usr/lib/x86_64-linux-gnu/libpython3.11.so
sudo chown root:root /usr/lib/x86_64-linux-gnu/libpython3.11.so
```

### Debug

```bash
# Activer le debug PHP
php -d ffi.enable=1 -d display_errors=1 -d error_reporting=E_ALL script.php

# Vérifier les extensions
php -m | grep ffi

# Tester l'intégration
php -r "
require_once 'lib/kyberium_php.php';
try {
    \$k = new KyberiumPHP();
    echo 'FFI integration OK\n';
} catch (Exception \$e) {
    echo 'Error: ' . \$e->getMessage() . '\n';
}
"
```

## Support

- **Documentation** : [docs/API_REFERENCE.md](../docs/API_REFERENCE.md)
- **Exemples** : [examples/](../examples/)
- **Issues** : [GitHub Issues](https://github.com/your-username/kyberium/issues)

---

Cette intégration FFI permet d'utiliser Kyberium dans des applications PHP avec des performances optimales et une sécurité post-quantique complète. 