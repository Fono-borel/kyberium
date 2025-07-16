import unittest
import subprocess
import base64
from kyberium.api import api

class InteropTest(unittest.TestCase):
    def setUp(self):
        # Initialisation d'une session Python
        self.session = api.SessionManager()
        self.session.init_session()

    def test_python_to_java(self):
        message = b"Interopérabilité Python-Java"
        ct, nonce = self.session.encrypt(message)
        # Encodage base64 pour passage CLI
        b64_ct = base64.b64encode(ct).decode()
        b64_nonce = base64.b64encode(nonce).decode()
        # Appel du déchiffrement Java
        result = subprocess.check_output([
            "java", "-cp", "kyberium/bindings/java:.", "InteropDecryptTest",
            b64_ct, b64_nonce
        ]).decode().strip()
        self.assertEqual(result, message.decode())

    def test_python_to_php(self):
        message = b"Interopérabilité Python-PHP"
        ct, nonce = self.session.encrypt(message)
        b64_ct = base64.b64encode(ct).decode()
        b64_nonce = base64.b64encode(nonce).decode()
        result = subprocess.check_output([
            "php", "kyberium/bindings/php/interop_decrypt.php", b64_ct, b64_nonce
        ]).decode().strip()
        self.assertEqual(result, message.decode())

    def test_python_to_cpp(self):
        message = b"Interopérabilité Python-C++"
        ct, nonce = self.session.encrypt(message)
        b64_ct = base64.b64encode(ct).decode()
        b64_nonce = base64.b64encode(nonce).decode()
        result = subprocess.check_output([
            "kyberium/bindings/cpp/interop_decrypt", b64_ct, b64_nonce
        ]).decode().strip()
        self.assertEqual(result, message.decode())

if __name__ == "__main__":
    unittest.main() 