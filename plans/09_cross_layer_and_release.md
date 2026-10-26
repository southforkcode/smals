# Cross-Layer Completion and Release Gates

Close remaining cross-layer behaviors explicitly, then assemble evidence rather than using a broad final test run as an unbounded task. Delivery infrastructure is necessary work but earns no specification credit by itself.

Source: [specification index](../specs/README.md). Delivery and evidence rules: [00](00_delivery_and_evidence.md). All checkboxes are initially open. Commands and implementation paths below are planned interfaces, not existing tools. Each listed row is one increment with a 15-minute active-work ceiling.

## Cross-layer behavior

Paths: src/cli/, test/integration/, test/foreign/. These are concrete behaviors not captured by merely implementing a class/interface.

| Increment / estimate | Prerequisites | Bounded deliverable | Demonstration and pass condition | Requirements advanced |
| --- | --- | --- | --- | --- |
| <a id="j001"></a>- [ ] **J001** / 10 min | T006, I009, E010 | Add explicit foreign-layout adapter descriptor admission, retaining module layout and rejecting uncontracted native containers/transfers. | A fixture requiring foreign record repacking rejects without an adapter; one explicitly declared copy adapter preserves logical value/ABI, while unexpected foreign transfer terminates at boundary. | ABI-007, CMP-003, EXC-009 |
| <a id="j002"></a>- [ ] **J002** / 10 min | E007, M016, Y009 | Add end-to-end stored/global-value persistence and scope-versus-lifetime demonstrations. | Loaded SSA retains old value after call updates mutable global; later load sees update; global visibility grants no synchronization; finalized content fault remains distinct from address lifetime. | TYP-009, TYP-018 |
| <a id="j003"></a>- [ ] **J003** / 10 min | B012, V021, L021, Y011 | Enforce CLI stage/version/capability claims and reject unsupported extension syntax/foreign/native requirements. | No source/fingerprint/host success can set a native target implemented; arrays/float/vector/generic volatile/weak atomics/dynamic module loading rejected; width-preserving logical output independent of host mode. | SMIL-003, SMIL-010, SMIL-011 |
| <a id="j004"></a>- [ ] **J004** / 10 min | R017, R020 | Add monitor transport routing and raised-return expiry checks common to profile adapters. | Reference 8008 read/write port asymmetry and trap-service register contract checked separately; raised completion invalidates local IDs before caller edge; no native unwinding assumption. | MON-003, MON-004, RFN-004 |

## Digest prerequisite split

Paths: thirdparty/, src/serialization/. These two rows precede canonical serializer I006 even though listed here to preserve stable IDs.

| Increment / estimate | Prerequisites | Bounded deliverable | Demonstration and pass condition | Requirements advanced |
| --- | --- | --- | --- | --- |
| <a id="i011"></a>- [ ] **I011** / 10 min | C011 | Resolve/pin one reputable SHA-256 dependency under repository third-party policy, or document a separate bounded implementation decision before coding. | Record primary authority, version/license/source pin and API/error behavior; unavailable dependency blocks digest consumer instead of substituting an unverified hash. | REF-003, IFC-002 |
| <a id="i012"></a>- [ ] **I012** / 10 min | I011, B006 | Wrap only SHA-256 bytes-to-digest with error-as-value behavior and known-answer tests. | Empty, abc, multi-block and Unicode UTF-8 byte cases match independent Python hashlib and published vectors; changed byte changes expected fixture digest. | REF-003, IFC-002 |

## Release gates

All 435 requirement audit rows and all 38 exact-profile gates are prerequisites of the final claim. No release gate fills missing implementation or performs an unbounded all-target suite.

| Increment / estimate | Prerequisites | Bounded deliverable | Demonstration and pass condition | Requirements advanced |
| --- | --- | --- | --- | --- |
| <a id="fin001"></a>- [ ] **FIN001** / 10 min | ALL-REQUIREMENT-AUDITS | Produce the final 435-key conformance manifest by validating existing scope receipts and all exact-profile availability gates; no full-suite rerun hidden here. | Report exactly 435 verified keys,38 qualified profiles,zero unresolved contracts/clauses/stale receipts; otherwise explicit incomplete/blocked report without advertising completion. | SMIL-010 |
| <a id="fin002"></a>- [ ] **FIN002** / 10 min | FIN001 | Reproduce one representative little-endian and one big-endian two-module example from a clean documented checkout using separate bounded build/run shards. | Recorded commands regenerate pinned contracts/objects/images and exact output/fault/status traces on independent engines; installed tools have no dependence on preexisting build cache. | SMIL-004, SMIL-010 |
| <a id="fin003"></a>- [ ] **FIN003** / 10 min | FIN002 | Publish completion report with evidence index, measured timings, remaining environment limitations and exact implemented target list. | Every checkbox links to a valid receipt; limitations do not contradict conformance claims; plan remains an implementation record rather than modifying specification requirements. | Delivery infrastructure; no spec closure |

