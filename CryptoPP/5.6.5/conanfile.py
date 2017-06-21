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
        "shared": [True, False]
    }
    default_options   =
        "shared=False"
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
            replace_in_file("./cryptopp/setenv-ios.sh", " == ", " = ")
            self.run("cd cryptopp && . ./setenv-ios.sh %s && make -f GNUmakefile-cross" % self.settings.arch)
        else:
            cmake = CMake(self)
            self.run('cmake cryptopp %s %s' % (cmake.command_line, "-DBUILD_SHARED_LIBS=ON" if self.options.shared else ""))
            self.run("cmake --build . %s" % cmake.build_config)

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
