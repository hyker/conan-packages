from conans import ConanFile, CMake, tools
from conans.tools import replace_in_file
import os

class CryptoppConan(ConanFile):
    name              = "CryptoPP"
    version           = "5.6.5"
    license           = "MIT"
    url               = "https://github.com/hykersec/conan-packages"
    settings          = "os", "compiler", "build_type", "arch"
    options           = {
        "shared": [False, True],
        "disable_asm": [False, True], # This and next options are described in https://www.cryptopp.com/wiki/CMake
        "disable_sse3": [False, True],
        "disable_sse4": [False, True],
        "disable_aesni": [False, True],
        "disable_sha": [False, True],
        "native_arch": [False, True],
    }
    default_options   = "shared=False", \
        "disable_asm=False", \
        "disable_sse3=False", \
        "disable_sse4=False", \
        "disable_aesni=False", \
        "disable_sha=False", \
        "native_arch=False"
    generators        = "cmake"
    source_git_url    = "https://github.com/weidai11/cryptopp.git"
    source_git_commit = "aaf62695fc03bf941ec51e40a139f5e0eb8652f3"

    def source(self):
        self.run("git clone %s" % self.source_git_url)
        self.run("cd cryptopp && git reset --hard %s" % self.source_git_commit)

        # Guarantee proper /MT /MD linkage in MSVC
        tools.replace_in_file("cryptopp/CMakeLists.txt", "project(cryptopp)", '''project(cryptopp)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()''')

    def build(self):
        if self.settings.os == "iOS":
            arches = ["armv7", "armv7s", "arm64"]

            replace_in_file("./cryptopp/setenv-ios.sh", " == ", " = ")
            for arch in arches:
                self.run("cd cryptopp && . ./setenv-ios.sh %s && export CXXFLAGS='-DNDEBUG -g2 -O3 -fPIC -pipe -fembed-bitcode' && make clean && make -f GNUmakefile-cross" % arch)
                self.run("cd cryptopp && cp libcryptopp.a libcryptopp-%s.a" % arch)

            self.run("cd cryptopp && lipo -create %s -output ./libcryptopp.a" % (" ".join(["./libcryptopp-%s.a" % arch for arch in arches])))
        else:
            cmake = CMake(self, parallel=True)
            
            on_off_map = {False: "OFF", True: "ON"}            
            cmake.definitions["DISABLE_ASM"] = on_off_map[bool(self.options.disable_asm)]
            cmake.definitions["DISABLE_SSSE3"] = on_off_map[bool(self.options.disable_sse3)]
            cmake.definitions["DISABLE_SSE4"] = on_off_map[bool(self.options.disable_sse4)]
            cmake.definitions["DISABLE_AESNI"] = on_off_map[bool(self.options.disable_aesni)]
            cmake.definitions["DISABLE_SHA"] = on_off_map[bool(self.options.disable_sha)]
            cmake.definitions["CRYPTOPP_NATIVE_ARCH"] = on_off_map[bool(self.options.native_arch)]
            
            cmake.definitions["BUILD_SHARED"] = on_off_map[bool(self.options.shared)]
            cmake.definitions["BUILD_STATIC"] = on_off_map[bool(not self.options.shared)]
            
            self.output.info("Confgigured with %s" % cmake.command_line)
            cmake.configure(source_dir="cryptopp")
            cmake.build()

    def package(self):
        self.copy("*.h", dst="include/cryptopp", src="cryptopp")
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.dylib", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs = ["cryptopp"] if self.options.shared else ["cryptopp-static"]
        else:
            self.cpp_info.libs = ["cryptopp"] if self.options.shared else ["libcryptopp.a"]
