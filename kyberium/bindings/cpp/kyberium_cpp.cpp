#include <pybind11/pybind11.h>
#include <pybind11/embed.h>
#include <pybind11/stl.h>

namespace py = pybind11;
using namespace py::literals;

class KyberiumAPI {
public:
    KyberiumAPI() {
        py::initialize_interpreter();
        kyberium = py::module_::import("kyberium.api");
    }
    ~KyberiumAPI() {
        py::finalize_interpreter();
    }

    // Session classique
    py::object init_session(py::bytes peer_public_key = py::none(), std::string kdf_type = "sha3", std::string symmetric_type = "aesgcm") {
        if (!peer_public_key.is_none())
            return kyberium.attr("init_session")(peer_public_key, kdf_type, symmetric_type);
        else
            return kyberium.attr("init_session")();
    }
    py::object complete_handshake(py::bytes ciphertext) {
        return kyberium.attr("complete_handshake")(ciphertext);
    }
    py::object encrypt(py::bytes plaintext, py::object aad = py::none()) {
        return kyberium.attr("encrypt")(plaintext, aad);
    }
    py::object decrypt(py::bytes ciphertext, py::bytes nonce, py::object aad = py::none()) {
        return kyberium.attr("decrypt")(ciphertext, nonce, aad);
    }
    py::object sign(py::bytes message) {
        return kyberium.attr("sign")(message);
    }
    py::object verify(py::bytes message, py::bytes signature, py::object public_key = py::none()) {
        return kyberium.attr("verify")(message, signature, public_key);
    }

    // Triple Ratchet
    py::object init_triple_ratchet(py::bytes peer_kem_public, py::bytes peer_sign_public, std::string kdf_type = "sha3", std::string symmetric_type = "aesgcm") {
        return kyberium.attr("init_triple_ratchet")(peer_kem_public, peer_sign_public, kdf_type, symmetric_type);
    }
    py::object complete_triple_ratchet_handshake(py::bytes kem_ciphertext, py::bytes kem_signature, py::bytes peer_sign_public, std::string kdf_type = "sha3", std::string symmetric_type = "aesgcm") {
        return kyberium.attr("complete_triple_ratchet_handshake")(kem_ciphertext, kem_signature, peer_sign_public, kdf_type, symmetric_type);
    }
    py::object triple_encrypt(py::bytes plaintext, py::object aad = py::none()) {
        return kyberium.attr("triple_encrypt")(plaintext, aad);
    }
    py::object triple_decrypt(py::bytes ciphertext, py::bytes nonce, py::bytes signature, int msg_num, py::bytes peer_sign_public, py::object aad = py::none()) {
        return kyberium.attr("triple_decrypt")(ciphertext, nonce, signature, msg_num, peer_sign_public, aad);
    }

private:
    py::object kyberium;
};

PYBIND11_MODULE(kyberium_cpp, m) {
    py::class_<KyberiumAPI>(m, "KyberiumAPI")
        .def(py::init<>())
        .def("init_session", &KyberiumAPI::init_session, "peer_public_key"_a = py::none(), "kdf_type"_a = "sha3", "symmetric_type"_a = "aesgcm")
        .def("complete_handshake", &KyberiumAPI::complete_handshake)
        .def("encrypt", &KyberiumAPI::encrypt, "plaintext"_a, "aad"_a = py::none())
        .def("decrypt", &KyberiumAPI::decrypt, "ciphertext"_a, "nonce"_a, "aad"_a = py::none())
        .def("sign", &KyberiumAPI::sign)
        .def("verify", &KyberiumAPI::verify, "message"_a, "signature"_a, "public_key"_a = py::none())
        .def("init_triple_ratchet", &KyberiumAPI::init_triple_ratchet, "peer_kem_public"_a, "peer_sign_public"_a, "kdf_type"_a = "sha3", "symmetric_type"_a = "aesgcm")
        .def("complete_triple_ratchet_handshake", &KyberiumAPI::complete_triple_ratchet_handshake, "kem_ciphertext"_a, "kem_signature"_a, "peer_sign_public"_a, "kdf_type"_a = "sha3", "symmetric_type"_a = "aesgcm")
        .def("triple_encrypt", &KyberiumAPI::triple_encrypt, "plaintext"_a, "aad"_a = py::none())
        .def("triple_decrypt", &KyberiumAPI::triple_decrypt, "ciphertext"_a, "nonce"_a, "signature"_a, "msg_num"_a, "peer_sign_public"_a, "aad"_a = py::none());
} 