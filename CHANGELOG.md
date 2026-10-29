# Changelog

Human-readable release history for Sally, reconstructed from the full repository
history, merged pull requests, GitHub releases, and published package/image
versions. Entries describe changes when they landed; a historical release is not
a claim about the current supported configuration.

Dates use the release/merge date in America/Denver where available. Docker-only
and untagged package versions are identified explicitly. The current GLEIF-IT
remote is authoritative for release tags: its `0.6.0` points to the March 2024
IPEX release, while some older clones retain a different local tag of that name.

## [1.0.9] — 2026-10-29

### Added

- Prometheus `/metrics` endpoint with credential counts and verification/status
  breakdowns, registry counts, ACDC/TEL escrow depths, webhook pipeline depths,
  presentation and revocation throughput, and labelled exception counters.
  Credential classification is cached for 30 seconds, with snapshot age and
  duration exposed for monitoring. ([#61])
- Importable Grafana dashboard and Prometheus scrape/configuration examples.
  The dashboard covers credential state, processing backlogs, webhook outcomes,
  and exceptional conditions. ([#61])
- Credential inspection summaries for stored ACDCs, chain dependencies,
  registries, TEL-only credentials, and escrows, plus CESR export helpers for
  verified credentials and their supporting state. ([#61])
- Root changelog covering the release history and links to the changes that
  introduced major features.

### Fixed

- Keep the revocation cue processor running when a credential's ACDC body is
  absent locally, rather than dereferencing a missing credential. Such a cue
  cannot produce a credential webhook payload. ([#60])
- Increment `sally_exceptions_total{kind="revocation_unknown_credential"}` when
  consuming that cue and yield before continuing, preserving cooperative
  scheduling through a backlog of unknown-credential revocations. ([#63])

Dependencies remain `gleif_keri==1.2.17` and `gleif_hio==0.6.21`; the Docker base
remains pinned to the corresponding KERI 1.2.17 image digest.

## [1.0.8] — 2026-10-15

- Upgrade to `gleif_keri==1.2.17`, retaining `gleif_hio==0.6.21`, and pin the
  corresponding immutable Docker base. This dependency release carries the
  introduction-receipt lookup correction and the LMDB 1.x compatibility bound.
  Align package, module, and Makefile versions. ([#59])

## [1.0.7] — 2026-10-14

- Upgrade to `gleif_keri==1.2.16` and `gleif_hio==0.6.21`, carrying the terminal
  TLS-disconnect cleanup fix into Sally. Pin the matching Docker base. ([#58])

## [1.0.6] — 2026-10-14

- Adopt the GLEIF dependency chain: `gleif_keri==1.2.15` and
  `gleif_hio==0.6.20`. Pin the matching multi-platform Docker base. ([#57])
- Simplify the runtime image to install Sally over the prepared KERI image and
  check dependency consistency. Make Docker publication wait for the matching
  PyPI release, build Linux AMD64/ARM64 images, and keep CI from installing the
  upstream HIO package alongside its GLEIF replacement. ([#57])

## [1.0.5] — 2026-07-26

- Simplify IPEX presentation handling around the grant's embedded anchoring,
  issuance, and ACDC material, shared with the direct and mailbox paths. ([#54])
- Support KERIpy 1.2.13 and HIO 0.6.19 compatibility, including scheduler cleanup
  arguments and byte-safe truncated logging. Update tests and the macOS CI
  toolchain, runner, and libsodium discovery. ([#54])

## [1.0.4] — 2026-03-18

- Upgrade the KERI dependency to `keri>=1.2.12,<1.3.0`, retain the HIO 0.6 line,
  remove obsolete test/setup dependency declarations, and align release
  metadata and CLI compatibility. ([#51])

## 1.0.3 — 2025-09-18 (untagged version commit)

- Align the Python package/module version with the `sally-verifier` 1.0.3
  publication. The repository has no `1.0.3` tag; the version change is
  [commit `697e3d5`](https://github.com/GLEIF-IT/sally/commit/697e3d5fec5f1e97d555088505e6a9e96fd00208).
- PyPI records `sally-verifier==1.0.3` on September 17 and `sally==1.0.3` on
  November 24, 2025. These publication dates differ from the version commit;
  they do not establish separate source changes.

## [1.0.2] — 2025-09-10

Changes merged since the preceding repository tag, `1.0.0-rc1`:

- Log validation success, presentation timeout, and removal from the
  presentation escrow. ([#47])
- Fix the first-presentation/grant startup path, including an undefined
  exchange-message variable, and resolve configured OOBIs before starting the
  verifier. Separate identifier inception and bootstrap scheduling from server
  setup so a new instance can start with its configuration ready. ([#48])
- Add a shared truncated logging formatter and update startup, logging, and
  configuration examples. ([#48])
- Align the Docker Makefile version with the package release. ([#49])

## 1.0.0 and 1.0.1 — 2025-08-19 (package-only history)

- PyPI lists these versions under the historical distribution name
  [`sally-verifier`](https://pypi.org/project/sally-verifier/#history), alongside
  `1.0.0rc1` and a later `1.0.2` upload that day.
- The repository has no matching stable `1.0.0` or `1.0.1` tags or version
  commits defining their boundaries. Their exact source deltas cannot be
  attributed from Git alone. Merged source changes are recorded under the
  surrounding repository releases rather than assigned speculative dates.

## [1.0.0-rc1] — 2025-05-06

- Add an optional direct-mode verification agent accepting CESR streams through
  HTTP `PUT /`, alongside witness-mailbox delivery. Add direct-mode identifier
  configuration and update the server/bootstrap examples. ([#40])
- Correct the HTTP port argument type and keep direct mode disabled by default
  unless `--direct` is supplied. ([#40], [#42])

## 0.10.2 — 2025-04-24 (Docker/version-commit history)

- Temporarily use `cit-keri==1.2.7-rc1` to pick up the required logging fix, then
  align the supporting dependencies with that release. ([#38], [#39])
- Publish the `gleif/sally:0.10.2` image. There is no matching repository tag;
  [commit `a419f58`](https://github.com/GLEIF-IT/sally/commit/a419f580ba8a408b23fa1de612f60a6a442db45c)
  introduced the version/dependency change.

## [0.10.1] — 2025-04-15

- Upgrade to KERIpy 1.2.6 to address the reply-message processing bug and align
  the package and image versions. ([#36])

## 0.10.0 — 2025-03-25 (untagged version commit)

- Allow `sally server start` to create its identifier from inception
  configuration and a supplied salt. Consolidate startup/configuration examples
  and remove the separate initialization scripts. ([#35])
- Add `/health` with version and webhook-pipeline counts, including a demo-hook
  health endpoint, and expose pipeline counts through `CueBaser.getCounts()`.
  Update CLI logging and CI. ([#35])

## [0.9.4] — 2025-02-03

- Upgrade to KERIpy 1.2.4, HIO 0.6.14, and Python 3.12.2 compatibility. Adapt
  credential revocation cue handling and registry-state access to the updated
  libraries. ([#31])
- Improve webhook payloads and documentation, including readable credential
  types, credential SAIDs in payloads, OOR authorization details, and demo-hook
  response examples. ([#30])
- Align the Docker Makefile with version 0.9.4. ([#32])

## [0.9.3] — 2024-11-25

- Interpret `CLEAR_ESCROWS` as a Boolean rather than treating every nonempty
  environment-variable string as true. ([#28])

## [0.9.2] — 2024-11-20

- Upgrade to KERIpy 1.1.22 and add `sally version`. ([#27])
- Add explicit webhook-pipeline escrow clearing, enabled by default in this
  historical release, and document/configure it through `CLEAR_ESCROWS`.
  ([#27])
- Consolidate container builds around the multi-platform Dockerfile and align
  package, module, and image versions.

## [0.9.1] — 2024-09-11

- Improve log messages and formatting, make server/demo logging configurable,
  and update the CLI and macOS setup. ([#25])
- Build AMD64 and ARM64 images through the shared multi-platform Makefile.
  ([#25])

## 0.9.0 — 2024-04-02 (Docker-only labels)

- Docker Hub retains `0.9.0` and `0.9.0-arm64` image labels. There is no matching
  Git tag or explicit version commit, so this history does not claim a distinct
  source delta between those images and the surrounding 0.8/0.9.1 revisions.

## 0.8.0 — 2024-03-26 (Docker/version-commit history)

- Fix application startup to schedule the presentation handler rather than
  treating `Exchanger` as a Doer. Update the IPEX grant example.
  ([commit `ce65ad5`](https://github.com/GLEIF-IT/sally/commit/ce65ad5))
- Add separate AMD64 and ARM64 Docker build recipes and bump their image labels
  to 0.8.0. ([commit `1d5676d`](https://github.com/GLEIF-IT/sally/commit/1d5676d))

## 0.7.0 — 2024-03-26 (Docker/version-commit history)

- Correct the post-IPEX integration reference and bump the Docker build target
  to 0.7.0. ([commit `50c72d4`](https://github.com/GLEIF-IT/sally/commit/50c72d4),
  [commit `394ff08`](https://github.com/GLEIF-IT/sally/commit/394ff08))

## [0.6.0] — 2024-03-21 (current GLEIF release tag)

- Accept IPEX `/ipex/grant` presentations and update presentation storage,
  notification processing, tests, and examples for the IPEX workflow. ([#23])
- Update KERIpy 1.1.8 compatibility and the Python CI/runtime requirements.
  ([#23])

## [0.5.2] — 2022-12-12

- Restore `legalEntityCredential` and `qviCredential` fields in OOR issuance
  webhook payloads for compatibility with existing receiving applications.
  ([#20])

## [0.5.1] — 2022-11-23

- Run the Docker process with unbuffered Python output so logs appear promptly.
  ([#19])

## [0.5.0] — 2022-11-22

- Align schema SAIDs in validation code, OOBI configuration, fixtures, and tests
  with the production vLEI credential schemas. ([#18])

## [0.4.0] — 2022-11-21

- Upgrade the `gleif/keri` container base used by Sally. ([#17])

## [0.3.0] — 2022-11-14

- Add the omitted ViRA schema OOBI to the local bootstrap configuration.
  ([#16])

## [0.2.0] — 2022-11-10

- Update credential-schema SAIDs and schema-resolution OOBIs. ([#15])

## [0.1.0] — 2022-11-05

Initial Docker release, incorporating the implementation developed since
August 2022:

- Receive credential presentations, validate the vLEI credential chain, and
  notify an external webhook of accepted presentations and revocations.
  Rename the initial KARA implementation to Sally and specialize it for vLEI.
  ([initial implementation](https://github.com/GLEIF-IT/sally/commit/ea540b4), [#9])
- Include LE and OOR chain information in webhook payloads. ([#11])
- Add the presentation/revocation/webhook test coverage and generated credential
  fixtures. ([#10])
- Configure webhook retry delays and escrow expiry, use signed HTTP headers,
  and support the OOR Auth credential chain. ([#12],
  [follow-up `3d56be7`](https://github.com/GLEIF-IT/sally/commit/3d56be7))
- Update operator documentation and KERIpy OOBI integration. ([#13], [#14])
- Add local and production-schema/staging-witness configurations, GitHub CI,
  and release-triggered Docker publication. Align the image with the appropriate
  KERIpy architecture.

## Historical side branch: 0.6.1 — 2023-03-29

The retained [`0.6.1` tag](https://github.com/GLEIF-IT/sally/tree/0.6.1) belongs
to the older agent/gatekeeper branch, not the ancestry of the current vLEI
verifier release line. That branch added authorization checks and gatekeeper
configuration, removed GLEIF-specific vLEI handlers, and clarified revocation
processing. Those removals were not incorporated into current main.

Its predecessor was locally tagged `0.6.0` in some clones in March 2023. This
is different from the current GLEIF-IT `0.6.0` tag and March 2024 GitHub release.
No existing tag is rewritten by this changelog.

## Release references

- [GitHub releases](https://github.com/GLEIF-IT/sally/releases)
- [Current PyPI distribution: sally](https://pypi.org/project/sally/#history)
- [Historical PyPI distribution: sally-verifier](https://pypi.org/project/sally-verifier/#history)
- [Docker Hub image history](https://hub.docker.com/r/gleif/sally/tags)

[1.0.9]: https://github.com/GLEIF-IT/sally/compare/1.0.8...1.0.9
[1.0.8]: https://github.com/GLEIF-IT/sally/compare/1.0.7...1.0.8
[1.0.7]: https://github.com/GLEIF-IT/sally/compare/1.0.6...1.0.7
[1.0.6]: https://github.com/GLEIF-IT/sally/compare/1.0.5...1.0.6
[1.0.5]: https://github.com/GLEIF-IT/sally/compare/1.0.4...1.0.5
[1.0.4]: https://github.com/GLEIF-IT/sally/tree/1.0.4
[1.0.2]: https://github.com/GLEIF-IT/sally/compare/1.0.0-rc1...1.0.2
[1.0.0-rc1]: https://github.com/GLEIF-IT/sally/tree/1.0.0-rc1
[0.10.1]: https://github.com/GLEIF-IT/sally/tree/0.10.1
[0.9.4]: https://github.com/GLEIF-IT/sally/compare/0.9.3...0.9.4
[0.9.3]: https://github.com/GLEIF-IT/sally/compare/0.9.2...0.9.3
[0.9.2]: https://github.com/GLEIF-IT/sally/compare/0.9.1...0.9.2
[0.9.1]: https://github.com/GLEIF-IT/sally/compare/0.6.0...0.9.1
[0.6.0]: https://github.com/GLEIF-IT/sally/compare/0.5.2...0.6.0
[0.5.2]: https://github.com/GLEIF-IT/sally/compare/0.5.1...0.5.2
[0.5.1]: https://github.com/GLEIF-IT/sally/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/GLEIF-IT/sally/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/GLEIF-IT/sally/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/GLEIF-IT/sally/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/GLEIF-IT/sally/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/GLEIF-IT/sally/tree/0.1.0

[#9]: https://github.com/GLEIF-IT/sally/pull/9
[#10]: https://github.com/GLEIF-IT/sally/pull/10
[#11]: https://github.com/GLEIF-IT/sally/pull/11
[#12]: https://github.com/GLEIF-IT/sally/pull/12
[#13]: https://github.com/GLEIF-IT/sally/pull/13
[#14]: https://github.com/GLEIF-IT/sally/pull/14
[#15]: https://github.com/GLEIF-IT/sally/pull/15
[#16]: https://github.com/GLEIF-IT/sally/pull/16
[#17]: https://github.com/GLEIF-IT/sally/pull/17
[#18]: https://github.com/GLEIF-IT/sally/pull/18
[#19]: https://github.com/GLEIF-IT/sally/pull/19
[#20]: https://github.com/GLEIF-IT/sally/pull/20
[#23]: https://github.com/GLEIF-IT/sally/pull/23
[#25]: https://github.com/GLEIF-IT/sally/pull/25
[#27]: https://github.com/GLEIF-IT/sally/pull/27
[#28]: https://github.com/GLEIF-IT/sally/pull/28
[#30]: https://github.com/GLEIF-IT/sally/pull/30
[#31]: https://github.com/GLEIF-IT/sally/pull/31
[#32]: https://github.com/GLEIF-IT/sally/pull/32
[#35]: https://github.com/GLEIF-IT/sally/pull/35
[#36]: https://github.com/GLEIF-IT/sally/pull/36
[#38]: https://github.com/GLEIF-IT/sally/pull/38
[#39]: https://github.com/GLEIF-IT/sally/pull/39
[#40]: https://github.com/GLEIF-IT/sally/pull/40
[#42]: https://github.com/GLEIF-IT/sally/pull/42
[#47]: https://github.com/GLEIF-IT/sally/pull/47
[#48]: https://github.com/GLEIF-IT/sally/pull/48
[#49]: https://github.com/GLEIF-IT/sally/pull/49
[#51]: https://github.com/GLEIF-IT/sally/pull/51
[#54]: https://github.com/GLEIF-IT/sally/pull/54
[#57]: https://github.com/GLEIF-IT/sally/pull/57
[#58]: https://github.com/GLEIF-IT/sally/pull/58
[#59]: https://github.com/GLEIF-IT/sally/pull/59
[#60]: https://github.com/GLEIF-IT/sally/pull/60
[#61]: https://github.com/GLEIF-IT/sally/pull/61
[#63]: https://github.com/GLEIF-IT/sally/pull/63
