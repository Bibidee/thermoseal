# ThermoSeal release and deployment record

## Current release: v0.2.0

ThermoSeal **v0.2.0 is deployed and verified** on stable **GenLayer Studionet, chain ID 61999**.

- Contract: [`0xdc10379Ec4508b43A04eb6BFB6AeE479E99Bb10A`](https://explorer-studio.genlayer.com/address/0xdc10379Ec4508b43A04eb6BFB6AeE479E99Bb10A)
- Deployment transaction: [`0x21a6d5d60d06f2823c09ef30266a85a167be1818ff2eb435499350e6227df61f`](https://explorer-studio.genlayer.com/tx/0x21a6d5d60d06f2823c09ef30266a85a167be1818ff2eb435499350e6227df61f)
- Finalization: `FINALIZED`; transaction receipt status `0x1`; deployment CLI result `MAJORITY_AGREE` / GenVM `SUCCESS`.
- `get_info()`: `name=ThermoSeal`, `version=0.2.0`, image evidence `optional_hash_bound_png_jpeg_webp_from_committed_delivery_host`, with the expected v0.2.0 limits and policy fields.
- Local source: 39,330 bytes; SHA-256 `3d48fbdf74919a8a979558d066d29e1cc1cdc3774d39b7d0ea9cde0cf5558c39`.
- Deployed source: retrieved with `gen_getContractCode`, decoded, and compared byte-for-byte; 39,330 bytes; same SHA-256; parity `YES`.
- Local release verification on 2026-10-07: 88 Direct Mode tests passed, zero skipped/failed; preflight, GenVM lint, and ABI/schema parity passed.
- Hosted CI passed on source commit `dbbe65f47c0476d96fca127eb76cdee3dd19a8d3` ([run 37581980116](https://github.com/Bibidee/thermoseal/actions/runs/37581980116)) and follow-up `7171c750e28d8ba1f04e06a069a752b91aa0247c` ([run 37582287013](https://github.com/Bibidee/thermoseal/actions/runs/37582287013)).

### v0.2.0 live shipment lifecycle

Shipment `THERMO-V020-LIVE-20261007-01` used sponsor `0x794678ad7e8b6c87dab33303a3a512c821e6de9a`, designated carrier `0x2cd419603eba593074653930ddc4073d4fd8fc60`, and a deposit of `1000000000000000` wei (0.001 GEN). Each transaction is `FINALIZED` with JSON-RPC receipt status `0x1`.

| Stage | Transaction | Result |
|---|---|---|
| Open | [`0x3501a2f7e63def7a87b277e92171c547586bbe561d160091218b5206944d99cb`](https://explorer-studio.genlayer.com/tx/0x3501a2f7e63def7a87b277e92171c547586bbe561d160091218b5206944d99cb) | Canonical read: `awaiting_carrier`; terms, manifest commitment, hosts and deposit match. |
| Carrier acceptance | [`0xc8659aba4b73560567e46ec70cca4fb1d34c3b25376ecfa163cb060b57391eba`](https://explorer-studio.genlayer.com/tx/0xc8659aba4b73560567e46ec70cca4fb1d34c3b25376ecfa163cb060b57391eba) | Canonical read: `in_transit`; assigned carrier accepted. |
| Evidence submission | [`0x622040e5fc8e6f81630e3f7285355a22cb9f1860f41d88de3d3d86be3321cf20`](https://explorer-studio.genlayer.com/tx/0x622040e5fc8e6f81630e3f7285355a22cb9f1860f41d88de3d3d86be3321cf20) | Canonical read: `evidence_submitted`; URLs/hashes match submitted values. |
| Review | [`0x70c4e9433745b8d4d91824b8d8ef6fd4327d1a3d801ff20ea6cf074b4a2b9f82`](https://explorer-studio.genlayer.com/tx/0x70c4e9433745b8d4d91824b8d8ef6fd4327d1a3d801ff20ea6cf074b4a2b9f82) | Canonical read: `approved`, confidence 85; rationale: “All records share identical shipment ID; delivery timestamp precedes deadline; telemetry compliant with zero excursions.” |
| Settlement | [`0x69926606b0e16672a9ceaa43a6fef62cf7e79c81c18c0a936b1e00cfdde7cb40`](https://explorer-studio.genlayer.com/tx/0x69926606b0e16672a9ceaa43a6fef62cf7e79c81c18c0a936b1e00cfdde7cb40) | Canonical read: `payout_dispatched`; deposited ledger zeroed; dispatched amount `1000000000000000` wei to the fixed carrier. Carrier balance increased by 0.001 GEN. |

The immutable artifacts were fetched independently and raw-byte SHA-256 values matched before proposing:

- Manifest: [`https://raw.githubusercontent.com/Bibidee/thermoseal/a9358d53dda2b5809ca42bc6cd7c03fd2ce74bbd/evidence/live-v0.2.0/manifest.txt`](https://raw.githubusercontent.com/Bibidee/thermoseal/a9358d53dda2b5809ca42bc6cd7c03fd2ce74bbd/evidence/live-v0.2.0/manifest.txt) — `0x4cf689232fdd52980017b128651fa2f4114b338216f86c7c3348bef511d7c37d`.
- Temperature log: [`https://raw.githubusercontent.com/Bibidee/thermoseal/7e2332828efa64c70fdea75d51b64c2856708e31/evidence/live-v0.2.0/temperature-log.json`](https://raw.githubusercontent.com/Bibidee/thermoseal/7e2332828efa64c70fdea75d51b64c2856708e31/evidence/live-v0.2.0/temperature-log.json) — `0xfae2d2b1c46e472b04ae67d5075ab9dda62ed4f7fd1a3b8860592cf42106032e`.
- Delivery record: [`https://cdn.jsdelivr.net/gh/Bibidee/thermoseal@7e2332828efa64c70fdea75d51b64c2856708e31/evidence/live-v0.2.0/delivery-record.txt`](https://cdn.jsdelivr.net/gh/Bibidee/thermoseal@7e2332828efa64c70fdea75d51b64c2856708e31/evidence/live-v0.2.0/delivery-record.txt) — `0xee0db5b01bc13659ec538615399f130982e40e91b2b3856ef36fbcc65feaf9c9`.

The final canonical state was `payout_dispatched`, `deposited=0`, `dispatched_amount=1000000000000000`, and the designated carrier recipient. The carrier's observed balance rose from 449.0199 to 449.0209 GEN. This balance observation corroborates credit; dispatch status alone is not considered proof of transfer credit.

## Historical release: v0.1.0

The v0.1.0 address and transactions below are historical evidence only; their parity and lifecycle evidence do not apply to the current v0.2.0 deployment.

## Historical deployment: v0.1.0

ThermoSeal **v0.1.0 was deployed** on stable **GenLayer Studionet, chain ID 61999**.

- Contract: [`0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2`](https://explorer-studio.genlayer.com/address/0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2)
- Deployment transaction: [`0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb`](https://explorer-studio.genlayer.com/tx/0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb)
- Transaction status: `FINALIZED`
- Consensus: `MAJORITY_AGREE`
- GenVM execution: `SUCCESS`
- `get_info()`: `name=ThermoSeal`, `version=0.1.0`, `min_escrow_wei=1000000000000000`, `min_confidence=80`, `max_text_bytes=24000`, `max_log_bytes=128000`, `max_image_bytes=2000000`, `max_samples=2000`, `max_sample_gap_seconds=900`, `max_excursion_seconds=7200`, `review_window_seconds=604800`, `retry_cooldown_seconds=300`, image evidence `optional_hash_bound_png_jpeg_webp`, timeout refund `permissionless`, sensor identity `not_proven_by_contract`.
- Historical source retrieval/parity: retrieved using `gen_getContractCode` through GenLayerJS; deployed and then-current local bytes both 38,999; SHA-256 `52ad40cf50d77eaf840a1f3db4df2ad8c96ca82cec67d3da8ab070a79704ea88`; byte-for-byte parity `YES` for v0.1.0 only.

The first deployment attempt used an invalid contract header ordering and did not create a usable contract. It is superseded by the successful deployment above; the failed attempt was `0xc0b564e2ee13af5933bcf8e69aeaac85f1dd366ff390a5d060ad399a82db3365` and is not the current address.

## v0.1.0 live lifecycle verification

Live operations used the deployed source above without any contract modification or redeployment. The sponsor was `0x794678AD7e8B6c87dAb33303a3A512c821e6De9A`; the independent assigned carrier was `0x2cd419603eBa593074653930Ddc4073d4FD8fc60`.

### Fail-closed path: identity contradiction and sponsor refund

- Shipment ID: `THERMO-LIVE-20261007061805`
- Open: [`0x287928b9a5a92e344742107f13a94ac93094bedf6e0b47abcd6883cd988e20b6`](https://explorer-studio.genlayer.com/tx/0x287928b9a5a92e344742107f13a94ac93094bedf6e0b47abcd6883cd988e20b6)
- Carrier accept: [`0x914768b0ee3d06f77d52b3707264693bd6548c6fb0912191cde06ca048a67797`](https://explorer-studio.genlayer.com/tx/0x914768b0ee3d06f77d52b3707264693bd6548c6fb0912191cde06ca048a67797)
- Evidence submit: [`0x8348bb4eed6e1a5991c7bfa9120ab790c5b76cd94636534fa14867fcc35e9daf`](https://explorer-studio.genlayer.com/tx/0x8348bb4eed6e1a5991c7bfa9120ab790c5b76cd94636534fa14867fcc35e9daf)
- Review: [`0xfb3ce06be3db0f90c2da8f5cc1aa8f914b6013cf2f5544cc5a92f328659fb67e`](https://explorer-studio.genlayer.com/tx/0xfb3ce06be3db0f90c2da8f5cc1aa8f914b6013cf2f5544cc5a92f328659fb67e) finalized `MAJORITY_AGREE` / GenVM `SUCCESS` with canonical state `blocked`. The stored rationale identified the mismatched manifest shipment ID.
- Settle: [`0x4b8461ac302ce21ae379a1c81cf16053a095d500e9f7c0c972c6808afeda5629`](https://explorer-studio.genlayer.com/tx/0x4b8461ac302ce21ae379a1c81cf16053a095d500e9f7c0c972c6808afeda5629) finalized `MAJORITY_AGREE` / GenVM `SUCCESS`, cleared the held ledger, and dispatched the 0.001 GEN sponsor refund.

### Approved path: matching evidence and carrier payout

- Shipment ID: `THERMO-LIVE-20261007-02`
- Open: [`0x23f863da3820c6b3b2251e7c74e44777859e7d9386d9b0041595bcd9a1a3372d`](https://explorer-studio.genlayer.com/tx/0x23f863da3820c6b3b2251e7c74e44777859e7d9386d9b0041595bcd9a1a3372d)
- Carrier accept: [`0xc8ae07dc7637bc5158556136b2532e43a8d365f6b9fac15c3a2f90f4bfb7605f`](https://explorer-studio.genlayer.com/tx/0xc8ae07dc7637bc5158556136b2532e43a8d365f6b9fac15c3a2f90f4bfb7605f)
- Evidence submit: [`0x1428f3d7da97188772841950d53d1799239e38206c6734a2a43c7d5542c8ee5c`](https://explorer-studio.genlayer.com/tx/0x1428f3d7da97188772841950d53d1799239e38206c6734a2a43c7d5542c8ee5c)
- Review: [`0xa3b8df68d726ad1198b1d078a20ea7f097ae56f9dcab3136d251cb00d4b5e8f0`](https://explorer-studio.genlayer.com/tx/0xa3b8df68d726ad1198b1d078a20ea7f097ae56f9dcab3136d251cb00d4b5e8f0) finalized `MAJORITY_AGREE` / GenVM `SUCCESS`. Canonical state became `approved` with confidence `100`; the stored rationale confirms matching shipment identity, a pre-deadline delivery timestamp, and 5.000 C telemetry inside the 2.000–8.000 C band.
- Settle: [`0xe476e722138b70801ff006a1f959cdb5eb3dc569c1d8ae87a611c84664ff4abc`](https://explorer-studio.genlayer.com/tx/0xe476e722138b70801ff006a1f959cdb5eb3dc569c1d8ae87a611c84664ff4abc) finalized `MAJORITY_AGREE` / GenVM `SUCCESS`, transitioned state to `payout_dispatched`, set `deposited=0`, recorded `dispatched_amount=1000000000000000`, and emitted a 0.001 GEN message to the fixed carrier address. A post-settlement `account show` observed the carrier balance at 449.0199 GEN, up from the pre-lifecycle 449.0189 GEN.

The immutable approved-path artifact hashes are:

- Manifest: `0xcc90292a2c32e25e8d5486690ea73cce2ce3fe64e739dc896412e099ac2025bd`
- Temperature log: `0x05cd0e83f585509a76214542b7c450ed2e4153622081262d190eea78e93c0104`
- Delivery record: `0xfa8451c73bd194dcf648f966d366e737dd5571da03d74ded705abc8f4fcfba22`

## Stable toolchain

The contract begins with the runtime-required `# v0.2.0` marker followed by its stable `py-genlayer` dependency hash. The repository pins `genlayer-test==0.29.2`, `genvm-linter==0.11.0`, `pytest==9.1.1`, and GenVM validation bundle `v0.2.16`; it does not pin the Consensus v0.6 release-candidate SDK family. The default Direct Mode/network configuration is Studionet.

## Local release gate

Run from the ThermoSeal repository root with Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m pytest tests/direct -q
python scripts/preflight.py
genvm-lint check contracts/thermoseal.py --json
genvm-lint schema contracts/thermoseal.py --output artifacts/thermoseal.abi.json
```

Preflight requires exactly one `contracts/*.py` source, parses/compiles the package, runs the complete Direct Mode suite, runs GenVM lint plus SDK validation, and compares generated schema output against the tracked ABI artifact. GitHub Actions runs this preflight on Python 3.12. `tests/conftest.py` is intentionally absent; the linter is invoked on the single deployable contract source, never on tests.

The v0.1.0 deployment, its parity proof, fail-closed refund path, approved payout path, and post-settlement carrier balance observation are preserved above as historical evidence. The v0.2.0 source changes the image provenance rule and removes carrier summary from semantic review, so none of the older deployment or lifecycle evidence is evidence for the new source.
