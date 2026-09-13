# OpenMS regression fixtures

Versioned TOPP fixtures and the complete original numerical regression suite. Core
class fixtures remain with the core SDK's optional `TestSupport` component. This
package uses `LANGUAGES NONE`; installing fixtures and registering tests requires
no C++ compiler and performs no OpenMS build.

Configure with `cmake -S . -B build`, then install with
`cmake --install build --prefix /sdk/test-data`. Source archives must additionally
set `OPENMS4_SOURCE_REVISION` to their exact package commit.
Archive builds must also declare `OPENMS4_SOURCE_DIRTY`; the installed harness
preserves both values. `OPENMS4_REQUIRE_CLEAN_SOURCE=ON` rejects modified sources
when producing publishable packages.

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
A flat custom binary directory such as `<prefix>/custom bin` uses the same
sibling `share/openms4/tools` discovery and is covered by registration tests.
For a nested binary directory, pass `OPENMS4_TOOL_NAMES` explicitly; this harness
still requires all selected tools together in `OPENMS4_TOOLS_BIN` and does not
resolve arbitrary per-tool paths from manifest column four.

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
The six PeakPickerHiRes invalid-parameter cases require exit code 6
(`ILLEGAL_PARAMETERS`) and case-specific diagnostics through
`cmake/ExpectToolFailure.cmake`. An unrelated ordinary failure, loader failure or
signal cannot satisfy these tests. Other preserved numerical negatives retain
their original assertions until migrated with their own known diagnostics.

## Packaging validation

`python3 -m unittest discover -s tests -v` passes 14 tests. Nine configure and
install this compiler-free package into temporary directories, relocate the
installation, register the full suite with mock core metadata and placeholder
binaries, and inspect CTest's test listing. They check installed-only paths,
manifest filtering, Windows `.exe` paths, copied fixtures, pinned runtime data,
and unchanged external-engine conditions, including custom binary directories
with spaces and the six explicit negative assertions. Five further checks run
controlled Python children through the assertion wrapper, covering expected
failure, wrong status/reason, loader errors and signal termination. No placeholder
or OpenMS executable is run, and numerical correctness is not claimed. Execute
the six native negatives again after installing the actual tool package.

<!-- package-graph:begin -->
## Where this package sits

![OpenMS 4 package architecture](docs/package-architecture.svg)

`test-data` builds against the installed **core** package at the revisions recorded in [`dependencies.lock.json`](dependencies.lock.json). **topp**, **openswath**, **flash**, **desktop**, **pyopenms**, **nuxl**, **prose**, **nase**, **comet**, **mascot**, **database-suitability**, **proteomics-lfq**, **parquet-diff** build against it.

| Repository | Relation | Contents |
| --- | --- | --- |
| [OpenMS4-core](https://github.com/okohlbacher/OpenMS4-core) | dependency | scientific library, OpenSwathAlgo, readers and writers, runtime data, optional TestSupport |
| [OpenMS4-topp](https://github.com/okohlbacher/OpenMS4-topp) | consumer | 123 console tools |
| [OpenMS4-openswath](https://github.com/okohlbacher/OpenMS4-openswath) | consumer | 19 executables and OpenSwathBase |
| [OpenMS4-flash](https://github.com/okohlbacher/OpenMS4-flash) | consumer | FLASHDeconv and the OpenMS::FLASH backend |
| [OpenMS4-desktop](https://github.com/okohlbacher/OpenMS4-desktop) | consumer | GUI SDK, TOPPView, ImageCreator, INIFileEditor, TOPPAS, ExecutePipeline |
| [OpenMS4-pyopenms](https://github.com/okohlbacher/OpenMS4-pyopenms) | consumer | nanobind bindings, installed module tree and repaired wheels |
| [OpenMS4-nuxl](https://github.com/okohlbacher/OpenMS4-nuxl) | consumer | OpenNuXL |
| [OpenMS4-prose](https://github.com/okohlbacher/OpenMS4-prose) | consumer | ProSE and the OpenMS::ProSE backend |
| [OpenMS4-nase](https://github.com/okohlbacher/OpenMS4-nase) | consumer | NucleicAcidSearchEngine |
| [OpenMS4-comet](https://github.com/okohlbacher/OpenMS4-comet) | consumer | CometAdapter |
| [OpenMS4-mascot](https://github.com/okohlbacher/OpenMS4-mascot) | consumer | MascotAdapterOnline |
| [OpenMS4-database-suitability](https://github.com/okohlbacher/OpenMS4-database-suitability) | consumer | DatabaseSuitability |
| [OpenMS4-proteomics-lfq](https://github.com/okohlbacher/OpenMS4-proteomics-lfq) | consumer | ProteomicsLFQ |
| [OpenMS4-parquet-diff](https://github.com/okohlbacher/OpenMS4-parquet-diff) | consumer | ParquetDiff |

The eighteen repositories are assembled by the parent repository
[OpenMS4-tests](https://github.com/okohlbacher/OpenMS4-tests), which holds the submodule pins (`packages.lock.json`), the
dependency-order build runner and the contract tests that keep the graph consistent.
[`docs/project-state.md`](https://github.com/okohlbacher/OpenMS4-tests/blob/codex/package-split/docs/project-state.md) is the current state
of the whole project; [`docs/build-split-packages.md`](https://github.com/okohlbacher/OpenMS4-tests/blob/codex/package-split/docs/build-split-packages.md)
reproduces the installed-SDK build.
<!-- package-graph:end -->
