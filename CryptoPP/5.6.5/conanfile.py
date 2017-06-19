from conans import ConanFile, CMake, tools
import os

class CryptoppConan(ConanFile):
    name            = "cryptopp"
    version         = "5.6.5"
    license         = "MIT"
    url             = "https://github.com/hykersec/conan-packages"
    settings        = "os", "compiler", "build_type", "arch"
    options         = {"shared": [True, False]}
    default_options = "shared=False"
    generators      = "cmake"

    def source(self):
        self.run("git clone https://github.com/weidai11/cryptopp.git")
        self.run("cd cryptopp && git reset --hard 429047a8e9765896178d2254c5469b4a5f036d67")

        # Guarantee proper /MT /MD linkage in MSVC
        tools.replace_in_file("cryptopp/CMakeLists.txt", "project(cryptopp)", '''project(cryptopp)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()''')

    def build(self):
        if self.settings.os == "iOS":
            self.run("cd cryptopp && ./setenv-ios.sh %s" % self.settings.arch)

        cmake = CMake(self)
        shared = "-DBUILD_SHARED_LIBS=ON" if self.options.shared else ""
        self.run('cmake cryptopp %s %s' % (cmake.command_line, shared))
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
