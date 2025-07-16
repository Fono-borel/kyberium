cmake_minimum_required(VERSION 3.16)
project(KyberiumCPP VERSION 1.0.0 LANGUAGES CXX)

# Configuration pour production
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release)

# Optimisations pour production
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native -mtune=native")
set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -Wall -Wextra -fsanitize=address,undefined")

# Trouver Python et pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# Configuration du module pybind11
pybind11_add_module(kyberium_cpp kyberium_cpp.cpp)

# Optimisations spécifiques pour la cryptographie
target_compile_definitions(kyberium_cpp PRIVATE
    PYTHON_VERSION=${Python3_VERSION}
    KYBERIUM_VERSION=${PROJECT_VERSION}
    _GNU_SOURCE
)

# Flags de sécurité pour production
target_compile_options(kyberium_cpp PRIVATE
    -fstack-protector-strong
    -fPIC
    -fvisibility=hidden
)

# Liaison avec les bibliothèques système
target_link_libraries(kyberium_cpp PRIVATE
    ${Python3_LIBRARIES}
    pthread
    dl
)

# Installation
install(TARGETS kyberium_cpp
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

# Configuration pour packaging
set(CPACK_PACKAGE_NAME "kyberium-cpp")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Kyberium Post-Quantum Cryptography C++ Bindings")
set(CPACK_PACKAGE_VENDOR "Kyberium Team")
set(CPACK_PACKAGE_CONTACT "security@kyberium.org")

# Tests de compilation
enable_testing()
add_test(NAME CompilationTest COMMAND ${CMAKE_COMMAND} --build . --config Release)

# Configuration pour CI/CD
if(DEFINED ENV{CI})
    set(CMAKE_BUILD_TYPE Debug)
    add_compile_options(-Werror)
endif() 