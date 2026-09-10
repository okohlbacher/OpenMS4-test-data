# OpenMS regression fixtures

Versioned TOPP fixtures and the complete original numerical regression suite. Core
class fixtures remain with the core SDK's optional `TestSupport` component. This
package uses `LANGUAGES NONE`; installing fixtures and registering tests requires
no C++ compiler and performs no OpenMS build.

Configure with `cmake -S . -B build`, then install with
`cmake --install build --prefix /sdk/test-data`. Source archives must additionally
set `OPENMS4_SOURCE_REVISION` to their exact package commit.

Consumers find `OpenMSTestData 1.0.0 EXACT CONFIG`. Its config exports the relocatable
`OpenMSTestData_TOPP_DIR` and `OpenMSTestData_REGRESSION_SOURCE_DIR`. The latter is a
complete installed CMake harness: it includes its own dependency lock and package
identity, so the original source checkout is unnecessary after installation.

To register regression tests, configure either this repository or the installed
`OpenMSTestData_REGRESSION_SOURCE_DIR` with `OPENMS4_REGRESSION_TESTS=ON`. Provide the
pinned core through `CMAKE_PREFIX_PATH` and set `OPENMS4_TOOLS_BIN` to the complete
installed suite's binary directory. Registration reads the compiler-free
`OpenMSData` metadata package, verifies its exact core revision against the lock,
and requires core `TestSupport` fixtures. It never loads native CMake dependency
packages solely to locate fixture files.

A suite staging prefix can combine separately built products. Installed product
manifests in `share/openms4/tools/*.tools.tsv` determine the tool names used for
`-write_ini` and `-write_ctd` tests. If using an older installation without
manifests, supply `OPENMS4_TOOL_NAMES` explicitly as a semicolon-separated list.
The directory is not globbed for arbitrary executables or DLLs. Windows executable
suffixes are handled separately from logical tool names.

Set `WITH_GUI=ON` for desktop numerical tests and `HAS_XSERVER=ON` for tests that
require a display. External engine discovery and its upstream version checks stay
in place. The test process environment selects the pinned core's runtime data.

Fixture files are copied into the test build directory before registration:
several external engines write caches beside their inputs. This keeps installed
fixtures immutable. Numerical outputs and temporary files likewise stay in the
test build directory. The fixture working copy needs roughly 433 MB.

Run the registered numerical tests with `ctest --test-dir <regression-build>` only
after building/installing the products. This is a full-suite acceptance harness;
individual product repositories also have separate smoke tests.

## Packaging validation

`python3 -m unittest discover -s tests -v` passes seven tests. They configure and
install this compiler-free package into temporary directories, relocate the
installation, register the full suite with mock core metadata and placeholder
binaries, and inspect CTest's test listing. They check installed-only paths,
manifest filtering, Windows `.exe` paths, copied fixtures, pinned runtime data,
and unchanged external-engine conditions. No placeholder or OpenMS executable is
run, and numerical correctness is not claimed.
