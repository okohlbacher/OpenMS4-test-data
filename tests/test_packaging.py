"""Fixture packaging and CTest registration checks; no OpenMS binaries are executed."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CMAKE = shutil.which("cmake")
CTEST = shutil.which("ctest")
REVISION = "a" * 40


@unittest.skipUnless(CMAKE and CTEST, "CMake and CTest are required")
class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="openms-testdata-package-")
        cls.directory = Path(cls.temporary.name)
        cls.build = cls.directory / "package-build"
        cls.installed = cls.directory / "installed"
        cls.moved = cls.directory / "relocated"
        cls._command([CMAKE, "-S", ROOT, "-B", cls.build,
                      "-DOPENMS4_SOURCE_REVISION=" + REVISION])
        cls._command([CMAKE, "--install", cls.build, "--prefix", cls.installed])
        cls.installed.rename(cls.moved)
        cls.harness = cls.moved / "share/openms4-test-data/1.0.0"
        cls.mock = cls.directory / "mock-sdk"
        cls.mock.mkdir()
        cls.data = cls.mock / "share/OpenMS/4.0.0"
        cls.data.mkdir(parents=True)
        cls.core_data = cls.data / "test-data/core"
        cls.core_data.mkdir(parents=True)
        core_pin = json.loads((ROOT / "dependencies.lock.json").read_text())["dependencies"]["OpenMS"]["source_revision"]
        (cls.mock / "OpenMSDataConfig.cmake").write_text(f'''
set(OpenMSData_FOUND TRUE)
set(OpenMSData_TestSupport_FOUND TRUE)
set(OpenMSData_SOURCE_REVISION "{core_pin}")
set(OpenMS_SOURCE_REVISION "{core_pin}")
set(OpenMS_DATA_DIR "{cls.data}")
set(OpenMS_TEST_DATA_DIR "{cls.core_data}")
set(OpenMS_WITH_WNETALIGN OFF)
set(OpenMS_WITH_OPENSWATH ON)
set(OpenMS_WITH_OPENTIMS OFF)
set(OpenMS_WITH_THERMO_RAW OFF)
''')
        cls._version_config(cls.mock / "OpenMSDataConfigVersion.cmake", "4.0.0")
        cls.suite = cls.directory / "suite"
        cls.bin = cls.suite / "bin"
        cls.bin.mkdir(parents=True)
        manifest_dir = cls.suite / "share/openms4/tools"
        manifest_dir.mkdir(parents=True)
        cls.names = set()
        for path in (ROOT / "topp/CMakeLists.txt", ROOT / "topp/THIRDPARTY/third_party_tests.cmake"):
            cls.names.update(re.findall(r'\$\{TOPP_BIN_PATH\}/([A-Za-z][A-Za-z0-9_]*)', path.read_text()))
        for name in cls.names:
            (cls.bin / name).write_text("registration-only placeholder; never execute\n")
        (cls.bin / "unrelated.dll").write_text("not a tool\n")
        (cls.bin / "unrelated-program").write_text("not a TOPP tool\n")
        manifest = "# name\tcategory\tversion\texecutable\n" + "".join(
            f"{name}\tTest\t4.0.0\tbin/{name}\n" for name in sorted(cls.names))
        (manifest_dir / "mock.tools.tsv").write_text(manifest)
        cls.registration = cls.directory / "registration"
        cls._command([CMAKE, "-S", cls.harness, "-B", cls.registration,
                      "-DOPENMS4_REGRESSION_TESTS=ON", f"-DOpenMSData_DIR={cls.mock}",
                      f"-DOPENMS4_TOOLS_BIN={cls.bin}", "-DWITH_GUI=ON", "-DHAS_XSERVER=ON",
                      "-DCMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH=FALSE",
                      "-DCMAKE_FIND_USE_CMAKE_SYSTEM_PATH=FALSE",
                      "-DCMAKE_MAKE_PROGRAM=/usr/bin/make"])
        result = cls._command([CTEST, "--test-dir", cls.registration, "--show-only=json-v1"])
        cls.tests = json.loads(result.stdout)["tests"]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @staticmethod
    def _command(command):
        result = subprocess.run(list(map(str, command)), text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        if result.returncode:
            raise AssertionError(result.stdout[-12000:])
        return result

    @classmethod
    def _version_config(cls, path, version):
        script = cls.directory / "version.cmake"
        script.write_text(f'''include(CMakePackageConfigHelpers)
write_basic_package_version_file("{path}" VERSION {version} COMPATIBILITY ExactVersion ARCH_INDEPENDENT)
''')
        cls._command([CMAKE, "-P", script])

    def test_relocated_package_is_discoverable(self):
        source = self.directory / "discovery"
        source.mkdir()
        (source / "CMakeLists.txt").write_text(f'''cmake_minimum_required(VERSION 3.24)
project(DiscoverTestData LANGUAGES NONE)
find_package(OpenMSTestData 1.0.0 EXACT REQUIRED CONFIG)
if(NOT OpenMSTestData_TOPP_DIR STREQUAL "{self.harness}/topp")
  message(FATAL_ERROR "Fixture path is not relocatable")
endif()
if(NOT OpenMSTestData_REGRESSION_SOURCE_DIR STREQUAL "{self.harness}")
  message(FATAL_ERROR "Harness source path is not relocatable")
endif()
if(NOT OpenMSTestData_SOURCE_REVISION STREQUAL "{REVISION}")
  message(FATAL_ERROR "Wrong package identity")
endif()
''')
        self._command([CMAKE, "-S", source, "-B", self.directory / "discovery-build",
                       f"-DCMAKE_PREFIX_PATH={self.moved}"])

    def test_full_suite_registers_against_installed_bins(self):
        self.assertGreater(len(self.tests), 1500)
        by_name = {test["name"]: test for test in self.tests}
        for name in ("TOPPWRITEINI_FuzzyDiff", "TOPP_FLASHDeconv_1", "TOPP_ImageCreator_1", "TOPP_INIUpdater_1"):
            self.assertIn(name, by_name)
            command = by_name[name]["command"][0]
            self.assertEqual(Path(command).parent, self.bin, command)
        self.assertFalse(any("unrelated" in test["name"] for test in self.tests))

    def test_registration_has_no_original_source_paths(self):
        serialized = json.dumps(self.tests)
        self.assertNotIn(str(ROOT), serialized)
        self.assertNotIn("../../../topp", serialized)
        self.assertNotIn("OpenMS4-tests/src", serialized)
        cache = (self.registration / "CMakeCache.txt").read_text()
        self.assertNotIn("CMAKE_CXX_COMPILER:", cache)
        self.assertNotIn("CMAKE_C_COMPILER:", cache)

    def test_fixtures_are_copied_into_writable_build_tree(self):
        fixtures = self.registration / "topp/fixtures"
        self.assertTrue((fixtures / "THIRDPARTY/spectra.mzML").is_file())
        by_name = {test["name"]: test for test in self.tests}
        command = by_name["TOPP_FileConverter_30"]["command"]
        self.assertIn(str(self.core_data / "MSPGenericFile_input.msp"), command)
        self.assertTrue(any(str(fixtures) in part for part in by_name["TOPP_FLASHDeconv_1"]["command"]))

    def test_windows_tools_keep_names_and_use_exe_paths(self):
        for name in self.names:
            (self.bin / (name + ".exe")).write_text("registration-only placeholder; never execute\n")
        build = self.directory / "registration-windows"
        self._command([CMAKE, "-S", self.harness, "-B", build,
                       "-DCMAKE_SYSTEM_NAME=Windows", "-DOPENMS4_REGRESSION_TESTS=ON",
                       f"-DOpenMSData_DIR={self.mock}", f"-DOPENMS4_TOOLS_BIN={self.bin}",
                       "-DCMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH=FALSE",
                       "-DCMAKE_FIND_USE_CMAKE_SYSTEM_PATH=FALSE",
                       "-DCMAKE_MAKE_PROGRAM=/usr/bin/make"])
        output = self._command([CTEST, "--test-dir", build, "--show-only=json-v1"])
        tests = {test["name"]: test for test in json.loads(output.stdout)["tests"]}
        self.assertIn("TOPPWRITEINI_FuzzyDiff", tests)
        self.assertNotIn("TOPPWRITEINI_FuzzyDiff.exe", tests)
        self.assertTrue(tests["TOPPWRITEINI_FuzzyDiff"]["command"][0].endswith("FuzzyDiff.exe"))
        self.assertTrue(tests["TOPP_FLASHDeconv_1"]["command"][0].endswith("FLASHDeconv.exe"))

    def test_runtime_data_is_pinned_for_all_regression_processes(self):
        for test in self.tests:
            properties = {value["name"]: value["value"] for value in test["properties"]}
            self.assertIn(f"OPENMS_DATA_PATH={self.data}", properties["ENVIRONMENT"], test["name"])

    def test_external_engine_conditions_are_preserved(self):
        names = {test["name"] for test in self.tests}
        self.assertNotIn("TOPP_CometAdapter_1", names)
        self.assertIn("TOPP_CometAdapter_missing", names)
        self.assertNotIn("TOPP_XTandemAdapter_1", names)


if __name__ == "__main__":
    unittest.main()
