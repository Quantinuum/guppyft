# Changelog

## 0.0.1 (2026-07-09)


### ⚠ BREAKING CHANGES

* Rename angle parameter to phase ([#125](https://github.com/quantinuum-dev/guppyft/issues/125))
* Custom op checker and compiler for `with` and `map` global ops ([#60](https://github.com/quantinuum-dev/guppyft/issues/60))
* Rework encoder pass ([#29](https://github.com/quantinuum-dev/guppyft/issues/29))
* Add support for linear input arguments, use `concrete` function to derive inputs for HUGR op ([#25](https://github.com/quantinuum-dev/guppyft/issues/25))
* Remove global swap, add global `with` and `map` ([#11](https://github.com/quantinuum-dev/guppyft/issues/11))
* Auto generate declarations for operations ([#8](https://github.com/quantinuum-dev/guppyft/issues/8))
* Encoder specs provide wrapper functions instead of setup and teardown ([#6](https://github.com/quantinuum-dev/guppyft/issues/6))
* Introduce existing encoder pass from Rust and Python ([#1](https://github.com/quantinuum-dev/guppyft/issues/1))

### Features

* Add dynamic logical qubits, borrowed blocks and associated operations to the Iceberg extension ([#70](https://github.com/quantinuum-dev/guppyft/issues/70)) ([426c170](https://github.com/quantinuum-dev/guppyft/commit/426c170baf167f3fc9c28759bfea8b86c40490ab))
* Add Guppy bindings for Iceberg extension ([#61](https://github.com/quantinuum-dev/guppyft/issues/61)) ([8d47352](https://github.com/quantinuum-dev/guppyft/commit/8d473525921b3c75560e4ce409a4622bb0bef41a))
* Add Iceberg extension ([#42](https://github.com/quantinuum-dev/guppyft/issues/42)) ([0438129](https://github.com/quantinuum-dev/guppyft/commit/0438129c783b309405e0028690c033f08dda9fcf))
* Add more ops to Iceberg extension ([#120](https://github.com/quantinuum-dev/guppyft/issues/120)) ([2ff7f3c](https://github.com/quantinuum-dev/guppyft/commit/2ff7f3cfe48c053966e280037d9deb1939540c70))
* Add support for linear input arguments, use `concrete` function to derive inputs for HUGR op ([#25](https://github.com/quantinuum-dev/guppyft/issues/25)) ([3095687](https://github.com/quantinuum-dev/guppyft/commit/3095687ee7132529a2a38e9536b9c693eb66cc13))
* Add support for tuple type as the global variable. ([#107](https://github.com/quantinuum-dev/guppyft/issues/107)) ([3fb71ab](https://github.com/quantinuum-dev/guppyft/commit/3fb71ab03c3c874629b7f18a272264c3df12e87a))
* Allow configuring all tket passes that are run during encoding ([#7](https://github.com/quantinuum-dev/guppyft/issues/7)) ([9148c2c](https://github.com/quantinuum-dev/guppyft/commit/9148c2ccf0778510d0589e28b37b7c93a53fe5a6))
* Auto generate declarations for operations ([#8](https://github.com/quantinuum-dev/guppyft/issues/8)) ([2536840](https://github.com/quantinuum-dev/guppyft/commit/25368408a63a00b80d655462f20c8daaa6d59343))
* Custom op checker and compiler for `with` and `map` global ops ([#60](https://github.com/quantinuum-dev/guppyft/issues/60)) ([7b333b0](https://github.com/quantinuum-dev/guppyft/commit/7b333b073b2dd8ef8557d5eec0140ad1e66db9ec))
* Derive type replacements from implementation signatures and allow ops with custom instantiations ([#122](https://github.com/quantinuum-dev/guppyft/issues/122)) ([bc95f3a](https://github.com/quantinuum-dev/guppyft/commit/bc95f3adb4728d969367d198a7026e75f90ff009))
* Make `measure_all` return a future array of bool ([#51](https://github.com/quantinuum-dev/guppyft/issues/51)) ([39ac934](https://github.com/quantinuum-dev/guppyft/commit/39ac934c05fc2e7ae215923364975530d3d77427))
* Remove global swap, add global `with` and `map` ([#11](https://github.com/quantinuum-dev/guppyft/issues/11)) ([c34cbb7](https://github.com/quantinuum-dev/guppyft/commit/c34cbb7433e1746caa90b2fbf005055685322fc7))
* Rename angle parameter to phase ([#125](https://github.com/quantinuum-dev/guppyft/issues/125)) ([e9da53c](https://github.com/quantinuum-dev/guppyft/commit/e9da53cb8e88495081287a8ad57aba365c0ed37d))
* Replace `Measurement` type with `bool` during `implement_ops` pass and force early read ([#92](https://github.com/quantinuum-dev/guppyft/issues/92)) ([3ebe29c](https://github.com/quantinuum-dev/guppyft/commit/3ebe29ce8bcaab798fe8d649c7c674790691da87))
* Restore `CustomValidator` for Iceberg ops ([#103](https://github.com/quantinuum-dev/guppyft/issues/103)) ([de33300](https://github.com/quantinuum-dev/guppyft/commit/de333006bebe25eb0d5d46be2da4bb0358d9bb66))
* Use `BorrowArray` instead of `Array` for result of `measure_all()`. ([#59](https://github.com/quantinuum-dev/guppyft/issues/59)) ([556341d](https://github.com/quantinuum-dev/guppyft/commit/556341d1d284e86df27fdebfdf455e5c4621d283))
* Use future-bool types throughout ([#57](https://github.com/quantinuum-dev/guppyft/issues/57)) ([a90a404](https://github.com/quantinuum-dev/guppyft/commit/a90a404915d858bc4630a59740effa88ce280aa5))


### Bug Fixes

* Remove `CustomValidator` for Iceberg ops ([#83](https://github.com/quantinuum-dev/guppyft/issues/83)) ([3e25a1b](https://github.com/quantinuum-dev/guppyft/commit/3e25a1ba3d8a99355fb45754605a9ff74bcc906f))
* Silence failure for missing HUGR extensions when preparing ops for encoding ([#22](https://github.com/quantinuum-dev/guppyft/issues/22)) ([59e87fe](https://github.com/quantinuum-dev/guppyft/commit/59e87fe859fd1187ad228d0883777199126afa20))
* Upgrade to latest dependencies and remove git repository references ([#87](https://github.com/quantinuum-dev/guppyft/issues/87)) ([7485d79](https://github.com/quantinuum-dev/guppyft/commit/7485d79f4019c6fa71efd6b254aa4ee4ec94a2a6))


### Documentation

* Add README ([#18](https://github.com/quantinuum-dev/guppyft/issues/18)) ([bb76707](https://github.com/quantinuum-dev/guppyft/commit/bb767073310a215b1dee0c902d1ab71c26cc6adb))
* Improve docstrings for non-destructive measurement ops. ([#50](https://github.com/quantinuum-dev/guppyft/issues/50)) ([7c03f9d](https://github.com/quantinuum-dev/guppyft/commit/7c03f9d94f89834bf33127bcd7d226f29594f319))


### Code Refactoring

* Encoder specs provide wrapper functions instead of setup and teardown ([#6](https://github.com/quantinuum-dev/guppyft/issues/6)) ([847b4e4](https://github.com/quantinuum-dev/guppyft/commit/847b4e437dd75afa4a41754b3be18dfb957e168d))
* Introduce existing encoder pass from Rust and Python ([#1](https://github.com/quantinuum-dev/guppyft/issues/1)) ([3b996c0](https://github.com/quantinuum-dev/guppyft/commit/3b996c05d759beb92d9c4f2b9755eba1538d753a))
* Rework encoder pass ([#29](https://github.com/quantinuum-dev/guppyft/issues/29)) ([af9836d](https://github.com/quantinuum-dev/guppyft/commit/af9836d495e2b71ac8228a84584973de02438665))
