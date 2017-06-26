from conans import ConanFile
from conans import tools
import platform, os, sys

class BoostConan(ConanFile):
    name                = "Boost"
    version             = "1.64.0"
    settings            = "os", "arch", "compiler", "build_type"
    source_folder_name  = "boost_%s" % version.replace(".", "_")
    source_zip_filename = "%s.zip" % source_folder_name if sys.platform == "win32" else "%s.tar.gz" % source_folder_name
    source_zip_url      = "http://sourceforge.net/projects/boost/files/boost/%s/%s/download" % (version, source_zip_filename)
    options             = {
        "shared":          [True, False],
        "header_only":     [True, False],
        "fPIC":            [True, False],
        "python":          [True, False],
        "atomic":          [True, False],
        "chrono":          [True, False],
        "container":       [True, False],
        "context":         [True, False],
        "coroutine":       [True, False],
        "coroutine2":      [True, False],
        "date_time":       [True, False],
        "exception":       [True, False],
        "filesystem":      [True, False],
        "graph":           [True, False],
        "graph_parallel":  [True, False],
        "iostreams":       [True, False],
        "locale":          [True, False],
        "log":             [True, False],
        "math":            [True, False],
        "mpi":             [True, False],
        "program_options": [True, False],
        "random":          [True, False],
        "regex":           [True, False],
        "serialization":   [True, False],
        "signals":         [True, False],
        "system":          [True, False],
        "test":            [True, False],
        "thread":          [True, False],
        "timer":           [True, False],
        "type_erasure":    [True, False],
        "wave":            [True, False]
    }
    default_options     = "=False\n".join(options.keys()) + "=False"
    url                 = "https://github.com/hykersec/conan-packages"
    exports             = ["FindBoost.cmake", "OriginalFindBoost*"]
    license             = "Boost Software License - Version 1.0. http://www.boost.org/LICENSE_1_0.txt"
    short_paths         = True

    def config_options(self):
        if self.settings.compiler == "Visual Studio":
            self.options.remove("fPIC")

    def configure(self):
        if self.settings.compiler == "Visual Studio" and self.options.shared and "MT" in str(self.settings.compiler.runtime):
            self.options.shared = False

        if self.options.header_only:
            self.options.remove("shared")
            self.options.remove("fPIC")
            self.options.remove("python")

    def conan_info(self):
        if self.options.header_only:
            self.info.requires.clear()
            self.info.settings.clear()

    def source(self):
        self.output.info("Downloading %s..." % self.source_zip_url)
        tools.download(self.source_zip_url, self.source_zip_filename)
        tools.unzip(self.source_zip_filename, ".")
        os.unlink(self.source_zip_filename)

    def build(self):
        if self.options.header_only:
            self.output.warn("Header only package, skipping build")
            return

        try:
            command = "bootstrap" if self.settings.os == "Windows" else "./bootstrap.sh --with-toolset=%s"% ("clang" if self.settings.compiler == "apple-clang" else self.settings.compiler)
            self.run("cd %s && %s" % (self.source_folder_name, command))
        except:
            self.run("cd %s && type bootstrap.log" % self.source_folder_name
                    if self.settings.os == "Windows"
                    else "cd %s && cat bootstrap.log" % self.source_folder_name)
            raise

        flags = []
        if self.settings.compiler == "Visual Studio":
            flags.append("toolset=msvc-%s" % self._msvc_version())
        elif self.settings.compiler == "gcc":
            # For GCC we only need the major version otherwhise Boost doesn't find the compiler
            flags.append("toolset=%s-%s"% (self.settings.compiler, self._gcc_short_version(self.settings.compiler.version)))
        elif str(self.settings.compiler) in ["clang"]:
            flags.append("toolset=%s-%s"% (self.settings.compiler, self.settings.compiler.version))

        flags.append("link=%s" % ("static" if not self.options.shared else "shared"))
        if self.settings.compiler == "Visual Studio" and self.settings.compiler.runtime:
            flags.append("runtime-link=%s" % ("static" if "MT" in str(self.settings.compiler.runtime) else "shared"))
        flags.append("variant=%s" % str(self.settings.build_type).lower())
        flags.append("address-model=%s" % ("32" if self.settings.arch == "x86" else "64"))

        option_names = {
            "--with-atomic":          self.options.atomic,
            "--with-chrono":          self.options.chrono,
            "--with-container":       self.options.container,
            "--with-context":         self.options.context,
            "--with-coroutine":       self.options.coroutine,
            "--with-coroutine2":      self.options.coroutine2,
            "--with-date_time":       self.options.date_time,
            "--with-exception":       self.options.exception,
            "--with-filesystem":      self.options.filesystem,
            "--with-graph":           self.options.graph,
            "--with-graph_parallel":  self.options.graph_parallel,
            "--with-iostreams":       self.options.iostreams,
            "--with-locale":          self.options.locale,
            "--with-log":             self.options.log,
            "--with-math":            self.options.math,
            "--with-mpi":             self.options.mpi,
            "--with-program_options": self.options.program_options,
            "--with-random":          self.options.random,
            "--with-regex":           self.options.regex,
            "--with-serialization":   self.options.serialization,
            "--with-signals":         self.options.signals,
            "--with-system":          self.options.system,
            "--with-test":            self.options.test,
            "--with-thread":          self.options.thread,
            "--with-timer":           self.options.timer,
            "--with-type_erasure":    self.options.type_erasure,
            "--with-wave":            self.options.wave
        }

        for option_name, activated in option_names.items():
            if activated:
                flags.append(option_name)

        cxx_flags = []
        # fPIC DEFINITION
        if self.settings.compiler != "Visual Studio":
            if self.options.fPIC:
                cxx_flags.append("-fPIC")


        # LIBCXX DEFINITION FOR BOOST B2
        try:
            if str(self.settings.compiler.libcxx) == "libstdc++":
                flags.append("define=_GLIBCXX_USE_CXX11_ABI=0")
            elif str(self.settings.compiler.libcxx) == "libstdc++11":
                flags.append("define=_GLIBCXX_USE_CXX11_ABI=1")
            if "clang" in str(self.settings.compiler):
                if str(self.settings.compiler.libcxx) == "libc++":
                    cxx_flags.append("-stdlib=libc++")
                    cxx_flags.append("-std=c++11")
                    flags.append('linkflags="-stdlib=libc++"')
                else:
                    cxx_flags.append("-stdlib=libstdc++")
                    cxx_flags.append("-std=c++11")
        except:
            pass

        if self.settings.os == "iOS":
            flags.append("architecture=arm target-os=iphone")
            for arch in ["armv7", "armv7s", "arm64"]:
                cxx_flags.append("-arch %s" % arch)
            cxx_flags.append("-isysroot %s" % "/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk")

        cxx_flags = 'cxxflags="%s"' % " ".join(cxx_flags) if cxx_flags else ""
        flags.append(cxx_flags)

        command = "b2" if self.settings.os == "Windows" else "./b2"

        b2_flags = " ".join(flags)

        python = "--with-python" if self.options.python else ""
        full_command = "cd %s && %s %s -j%s --abbreviate-paths %s" % (
            self.source_folder_name,
            command,
            b2_flags,
            tools.cpu_count(),
            python)
        self.output.warn(full_command)

        envs = self.prepare_deps_options_env()
        with tools.environment_append(envs):
            self.run(full_command)

    def prepare_deps_options_env(self):
        return {}

    def package(self):
        self.copy("FindBoost.cmake", ".", ".")
        self.copy("OriginalFindBoost*", ".", ".")

        self.copy(pattern="*",        dst="include/boost", src="%s/boost" % self.source_folder_name)
        self.copy(pattern="*.a",      dst="lib",           src="%s/stage/lib" % self.source_folder_name)
        self.copy(pattern="*.so",     dst="lib",           src="%s/stage/lib" % self.source_folder_name)
        self.copy(pattern="*.so.*",   dst="lib",           src="%s/stage/lib" % self.source_folder_name)
        self.copy(pattern="*.dylib*", dst="lib",           src="%s/stage/lib" % self.source_folder_name)
        self.copy(pattern="*.lib",    dst="lib",           src="%s/stage/lib" % self.source_folder_name)
        self.copy(pattern="*.dll",    dst="bin",           src="%s/stage/lib" % self.source_folder_name)

    def package_info(self):
        if not self.options.header_only and self.options.shared:
            self.cpp_info.defines.append("BOOST_ALL_DYN_LINK")
        else:
            self.cpp_info.defines.append("BOOST_USE_STATIC_LIBS")

        if self.options.header_only:
            return

        lib_names = {
            "atomic":          self.options.atomic,
            "chrono":          self.options.chrono,
            "container":       self.options.container,
            "context":         self.options.context,
            "coroutine":       self.options.coroutine,
            "coroutine2":      self.options.coroutine2,
            "date_time":       self.options.date_time,
            "exception":       self.options.exception,
            "filesystem":      self.options.filesystem,
            "graph":           self.options.graph,
            "graph_parallel":  self.options.graph_parallel,
            "iostreams":       self.options.iostreams,
            "locale":          self.options.locale,
            "log":             self.options.log,
            "math":            self.options.math,
            "mpi":             self.options.mpi,
            "program_options": self.options.program_options,
            "random":          self.options.random,
            "regex":           self.options.regex,
            "serialization":   self.options.serialization,
            "signals":         self.options.signals,
            "system":          self.options.system,
            "test":            self.options.test,
            "thread":          self.options.thread,
            "timer":           self.options.timer,
            "type_erasure":    self.options.type_erasure,
            "wave":            self.options.wave
        }

        libs = []
        for lib_name, activated in lib_names.items():
            if activated:
                libs.append(lib_name)

        if self.options.python:
            libs.append("python")
            if not self.options.shared:
                self.cpp_info.defines.append("BOOST_PYTHON_STATIC_LIB")

        if self.settings.compiler == "Visual Studio":
            # http://www.boost.org/doc/libs/1_55_0/more/getting_started/windows.html
            runtime = "mt" # str(self.settings.compiler.runtime).lower()

            abi_tags = []
            if self.settings.compiler.runtime in ("MTd", "MT"):
                abi_tags.append("s")

            if self.settings.build_type == "Debug":
                abi_tags.append("gd")

            abi_tags = ("-%s" % "".join(abi_tags)) if abi_tags else ""

            version = "_".join(self.version.split(".")[0:2])
            suffix = "vc%s-%s%s-%s" %  (self._msvc_version().replace(".", ""), runtime, abi_tags, version)
            prefix = "lib" if not self.options.shared else ""

            win_libs = []
            win_libs.extend(["%sboost_%s-%s" % (prefix, lib, suffix) for lib in libs if lib not in ["exception", "test_exec_monitor"]])
            win_libs.extend(["libboost_exception-%s" % suffix, "libboost_test_exec_monitor-%s" % suffix])

            self.cpp_info.libs.extend(win_libs)
            self.cpp_info.defines.extend(["BOOST_ALL_NO_LIB"])
        else:
            self.cpp_info.libs.extend(["boost_%s" % lib for lib in libs])

    def _msvc_version(self):
        if self.settings.compiler.version == "15":
            return "14.1"
        else:
            return "%s.0" % self.settings.compiler.version

    def _gcc_short_version(self, version):
        return str(version)[0]

    def boost_libraries():
        return 
