# ThermoSeal

ThermoSeal is a standalone GenLayer Intelligent Contract primitive for cold-chain shipment escrow. A sponsor commits the shipment manifest, carrier, logger and delivery evidence hosts, temperature band, excursion allowance, and delivery deadline before funding. The carrier accepts the shipment and later commits a machine-readable temperature log, a delivery record, and optionally one image from the sponsor-committed delivery host. Validators independently fetch and hash-check the exact artifacts; deterministic code evaluates the complete temperature log, while GenLayer consensus judges whether the committed records and optional image support the same shipment and delivery. The carrier summary is retained for audit display and excluded from the semantic review.

ThermoSeal is a contract primitive, not a logistics frontend, sensor network, identity system, or guarantee that an uploaded record is true.

## Why GenLayer?

A conventional contract can compare hashes and perform exact temperature arithmetic, but it cannot reliably decide whether a carrier's manifest, logger export, delivery record, and photograph describe the same shipment or contain a material contradiction. A single off-chain verifier could selectively accept or reject evidence. ThermoSeal has each assigned validator independently retrieve the committed bytes and make the bounded semantic judgement under the contract's equivalence rule. The exact temperature calculations, authorization conditions, time windows, state transitions, and escrow accounting remain deterministic.

GenLayer consensus is not a promise that every review finalizes. Validators or providers can disagree, an external host can fail, and a transaction can remain undetermined. Such cases never authorize payout; the shipment remains reviewable or reaches its public timeout-refund path.

## Lifecycle

```text
Sponsor funds and commits terms
        |
        v
 awaiting_carrier -- carrier accepts --> in_transit
        |                                  |
        | cancel / acceptance timeout      | carrier submits hash-bound evidence
        v                                  v
 refund_dispatched                evidence_submitted
                                          |
                            +-------------+-------------+
                            |                           |
                       safe review                negative review
                            |                           |
                            v                           v
                        approved                    blocked
                            |                           |
                     permissionless settle     permissionless settle
                            |                           |
                            v                           v
                 payout_dispatched           refund_dispatched

 evidence_submitted <--> retryable -- public deadline refund --> refund_dispatched
 in_transit -- delivery deadline refund -----------------------> refund_dispatched
```

The carrier cannot alter terms after funding. Once evidence is submitted, the review deadline is fixed. A retryable provider/output failure can be retried after a five-minute cooldown; anyone can trigger a sponsor refund after the review deadline. A valid but negative or uncertain semantic decision is `blocked`, which permits only the sponsor-refund settlement. An approved result permits only the carrier payout. Settlement is permissionless, but the recipient is fixed by the state transition.

## Evidence and review

- Manifest, temperature log, delivery record, and optional image are HTTPS references committed with lowercase-normalized `0x` SHA-256 digests.
- The contract hashes raw response bytes before decoding text. It rejects empty, oversized, mismatched, malformed, or invalidly encoded evidence from approval.
- The temperature log is strict UTF-8 JSON with `shipment_id`, `sensor_id`, and ordered `{timestamp, temp_milli_c}` samples. The contract checks identity, bounds, sample count, transit timestamps, coverage gaps, and excursion allowance deterministically.
- The semantic model receives the hash-verified manifest and delivery text, deterministic telemetry findings, and—if supplied—the hash-verified image bytes. Artifact text and visible image text are explicitly untrusted data, never reviewer instructions.
- Optional image URLs must use the sponsor-committed `delivery_host`, just like the delivery record. The carrier summary remains available in shipment state but is not submitted as decision evidence.
- Approval requires `shipment_match=yes`, `delivery_supported=yes`, `risk=no`, confidence at least 80, and deterministic telemetry compliance. Rationale is optional, bounded, and non-authoritative.
- Each validator independently fetches and evaluates the evidence. Approval requires both independent analyses to derive the complete safe authorization tuple. Rationale is not consensus-critical. Differently reasoned rejections may agree because neither can authorize a carrier payout.

## Escrow accounting

`open_shipment` is payable and treats only `gl.message.value` as the deposited amount. The contract stores a separate `deposited` ledger. `settle` and each refund path set that ledger to zero and record the dispatch before the single `_send_gen` transfer helper is called. This prevents a second contract-level payout from reusing the same deposit.

The recorded status is `payout_dispatched` or `refund_dispatched`. It does **not** prove that the downstream transfer message credited the recipient. Integrators must inspect the finalized child-transfer receipt and credited value when the network exposes them. A failed child transfer may not be recoverable by this contract.

## Build and release checks

Use Python 3.12, the pinned Direct Mode/linter dependencies, and the stable GenVM validation bundle `v0.2.16`:

```bash
python -m pip install -r requirements.txt
python -m pytest tests/direct -q
python scripts/preflight.py
genvm-lint check contracts/thermoseal.py --json
genvm-lint schema contracts/thermoseal.py --output artifacts/thermoseal.abi.json
```

The release gate explicitly lints the single source under `contracts/`; tests are not treated as deployable sources. It checks the runtime-required version marker followed by the pinned `py-genlayer` dependency marker, runs the genuine `genlayer-test` Direct Mode fixtures, static and SDK validation, and compares generated ABI/schema output with the tracked artifact. The small Windows pytest plugin only defers the pinned test runner's temporary-file cleanup; it does not mock contract execution or GenLayer imports. Linux CI runs the official Direct Mode loader without that workaround.

## Deployment status

ThermoSeal **v0.2.0 is deployed and verified** on stable GenLayer Studionet (chain ID 61999) at [0xdc10379Ec4508b43A04eb6BFB6AeE479E99Bb10A](https://explorer-studio.genlayer.com/address/0xdc10379Ec4508b43A04eb6BFB6AeE479E99Bb10A). The deployment transaction [0x21a6d5d60d06f2823c09ef30266a85a167be1818ff2eb435499350e6227df61f](https://explorer-studio.genlayer.com/tx/0x21a6d5d60d06f2823c09ef30266a85a167be1818ff2eb435499350e6227df61f) finalized successfully with `MAJORITY_AGREE` and GenVM `SUCCESS`. `get_info()` returned `name=ThermoSeal`, `version=0.2.0`, and the expected v0.2.0 configuration.

Deployed source was retrieved through `gen_getContractCode`, decoded, and compared byte-for-byte with `contracts/thermoseal.py`: both are 39,330 bytes with SHA-256 `3d48fbdf74919a8a979558d066d29e1cc1cdc3774d39b7d0ea9cde0cf5558c39`; parity is **YES**. Local verification on 2026-10-07: 88 Direct Mode tests passed, zero skipped/failed; preflight, GenVM lint, and ABI/schema parity passed. Hosted GitHub Actions passed on source commit `dbbe65f47c0476d96fca127eb76cdee3dd19a8d3` in [run 37581980116](https://github.com/Bibidee/thermoseal/actions/runs/37581980116) and on follow-up commit `7171c750e28d8ba1f04e06a069a752b91aa0247c` in [run 37582287013](https://github.com/Bibidee/thermoseal/actions/runs/37582287013). The v0.1.0 deployment and live transactions below are preserved as historical evidence only; they do not include image-host binding or the summary-prompt change.

## v0.2.0 live Studionet lifecycle

Shipment `THERMO-V020-LIVE-20261007-01` used sponsor `0x794678ad7e8b6c87dab33303a3a512c821e6de9a`, designated carrier `0x2cd419603eba593074653930ddc4073d4fd8fc60`, and a `0.001 GEN` deposit (`1000000000000000` wei). Every transaction below is `FINALIZED`; the corresponding JSON-RPC transaction receipt has status `0x1`.

| Stage | Transaction | Verified result |
|---|---|---|
| Open | [0x3501a2…944d99cb](https://explorer-studio.genlayer.com/tx/0x3501a2f7e63def7a87b277e92171c547586bbe561d160091218b5206944d99cb) | `awaiting_carrier`; committed manifest, host constraints, and deposit read back correctly. |
| Carrier acceptance | [0xc8659a…7391eba](https://explorer-studio.genlayer.com/tx/0xc8659aba4b73560567e46ec70cca4fb1d34c3b25376ecfa163cb060b57391eba) | `in_transit`; designated carrier accepted. |
| Evidence submission | [0x622040…321cf20](https://explorer-studio.genlayer.com/tx/0x622040e5fc8e6f81630e3f7285355a22cb9f1860f41d88de3d3d86be3321cf20) | `evidence_submitted`; committed URLs and hashes read back exactly. |
| Semantic review | [0x70c4c9…2b9f82](https://explorer-studio.genlayer.com/tx/0x70c4e9433745b8d4d91824b8d8ef6fd4327d1a3d801ff20ea6cf074b4a2b9f82) | `approved`, confidence 85. Rationale: “All records share identical shipment ID; delivery timestamp precedes deadline; telemetry compliant with zero excursions.” |
| Settlement | [0x699266…e7cb40](https://explorer-studio.genlayer.com/tx/0x69926606b0e16672a9ceaa43a6fef62cf7e79c81c18c0a936b1e00cfdde7cb40) | `payout_dispatched`; `deposited=0`, `dispatched_amount=1000000000000000`, and fixed carrier recipient. Carrier balance increased by 0.001 GEN. |

The immutable live artifacts were fetched independently and their exact raw-byte hashes checked before submission:

- Manifest: [raw artifact](https://raw.githubusercontent.com/Bibidee/thermoseal/a9358d53dda2b5809ca42bc6cd7c03fd2ce74bbd/evidence/live-v0.2.0/manifest.txt) — `0x4cf689232fdd52980017b128651fa2f4114b338216f86c7c3348bef511d7c37d`.
- Temperature log: [raw artifact](https://raw.githubusercontent.com/Bibidee/thermoseal/7e2332828efa64c70fdea75d51b64c2856708e31/evidence/live-v0.2.0/temperature-log.json) — `0xfae2d2b1c46e472b04ae67d5075ab9dda62ed4f7fd1a3b8860592cf42106032e`.
- Delivery record: [raw artifact](https://cdn.jsdelivr.net/gh/Bibidee/thermoseal@7e2332828efa64c70fdea75d51b64c2856708e31/evidence/live-v0.2.0/delivery-record.txt) — `0xee0db5b01bc13659ec538615399f130982e40e91b2b3856ef36fbcc65feaf9c9`.

The canonical post-settlement read confirmed `payout_dispatched`, zero remaining deposit, the recorded dispatch amount, and the designated carrier. The recipient balance observation corroborates credit; the contract’s dispatch state alone is not treated as proof of transfer credit.

## Historical Studionet deployment: v0.1.0

ThermoSeal v0.1.0 is deployed on stable GenLayer Studionet (chain ID 61999) at [0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2](https://explorer-studio.genlayer.com/address/0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2). The deployment transaction [0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb](https://explorer-studio.genlayer.com/tx/0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb) finalized with `MAJORITY_AGREE` and GenVM `SUCCESS`.

At the time of the v0.1.0 release, deployed source was retrieved with `gen_getContractCode` through GenLayerJS and matched byte-for-byte: 38,999 bytes, SHA-256 `52ad40cf50d77eaf840a1f3db4df2ad8c96ca82cec67d3da8ab070a79704ea88`. The historical `get_info()` read reported `name=ThermoSeal`, `version=0.1.0`, and `min_escrow_wei=1000000000000000` (0.001 GEN). That parity applies only to the old v0.1.0 source.

## Historical v0.1.0 live lifecycle evidence

Two finalized live cases now supplement the deployment evidence. Both used `thermo-sponsor` as the sponsor and `fresh-bob` as the assigned carrier; all writes finalized on Studionet with `MAJORITY_AGREE` and GenVM `SUCCESS`.

- **Fail-closed identity contradiction:** shipment `THERMO-LIVE-20261007061805` opened in [0x287928…e20b6](https://explorer-studio.genlayer.com/tx/0x287928b9a5a92e344742107f13a94ac93094bedf6e0b47abcd6883cd988e20b6), was accepted in [0x914768…67797](https://explorer-studio.genlayer.com/tx/0x914768b0ee3d06f77d52b3707264693bd6548c6fb0912191cde06ca048a67797), and supplied evidence in [0x8348bb…e9daf](https://explorer-studio.genlayer.com/tx/0x8348bb4eed6e1a5991c7bfa9120ab790c5b76cd94636534fa14867fcc35e9daf). Review [0xfb3ce0…fb67e](https://explorer-studio.genlayer.com/tx/0xfb3ce06be3db0f90c2da8f5cc1aa8f914b6013cf2f5544cc5a92f328659fb67e) detected the manifest/evidence shipment-ID contradiction and finalized `blocked`; settlement [0x4b8461…a5629](https://explorer-studio.genlayer.com/tx/0x4b8461ac302ce21ae379a1c81cf16053a095d500e9f7c0c972c6808afeda5629) dispatched the 0.001 GEN refund to the sponsor.
- **Approved carrier payout:** matching shipment `THERMO-LIVE-20261007-02` opened in [0x23f863…3372d](https://explorer-studio.genlayer.com/tx/0x23f863da3820c6b3b2251e7c74e44777859e7d9386d9b0041595bcd9a1a3372d), was accepted in [0xc8ae07…7605f](https://explorer-studio.genlayer.com/tx/0xc8ae07dc7637bc5158556136b2532e43a8d365f6b9fac15c3a2f90f4bfb7605f), and received independently fetched, hash-verified telemetry and delivery evidence in [0x1428f3…8ee5c](https://explorer-studio.genlayer.com/tx/0x1428f3d7da97188772841950d53d1799239e38206c6734a2a43c7d5542c8ee5c). Review [0xa3b8df…5e8f0](https://explorer-studio.genlayer.com/tx/0xa3b8df68d726ad1198b1d078a20ea7f097ae56f9dcab3136d251cb00d4b5e8f0) finalized `approved` at confidence 100. Settlement [0xe476e7…f4abc](https://explorer-studio.genlayer.com/tx/0xe476e722138b70801ff006a1f959cdb5eb3dc569c1d8ae87a611c84664ff4abc) finalized `payout_dispatched`, cleared `deposited` to zero, recorded `dispatched_amount=1000000000000000`, and emitted the fixed 0.001 GEN carrier transfer. The carrier balance observation moved from 449.0189 to 449.0199 GEN.

The committed live artifacts are [manifest](evidence/live/manifest-approved.txt), [temperature log](evidence/live/temperature-log-approved.json), and [delivery record](evidence/live/delivery-record-approved.txt). Their committed hashes are respectively `0xcc90292a2c32e25e8d5486690ea73cce2ce3fe64e739dc896412e099ac2025bd`, `0x05cd0e83f585509a76214542b7c450ed2e4153622081262d190eea78e93c0104`, and `0xfa8451c73bd194dcf648f966d366e737dd5571da03d74ded705abc8f4fcfba22`.

## Limits and trust assumptions

- Hash commitments prove byte identity, not sensor authenticity, shipment reality, custody, authorship, or truth.
- Hostname checks reject obvious local/IP targets and require distinct logger/delivery hostnames, but cannot prove DNS resolution, redirect behavior, domain control, or organizational independence.
- Validators and fetch infrastructure depend on external HTTPS availability. Some unavailable/LLM failures are retryable; some permanent HTTP/content/format failures are blocked. The review timeout makes the sponsor refund callable, but someone still must submit that transaction.
- Temperature checks reason over submitted samples and bounded gaps; they cannot prove unsampled physical temperatures or that a sensor was calibrated or tamper-proof.
- Semantic consensus can disagree or remain undetermined. The contract fails closed; it does not promise an approved outcome or eliminate consensus uncertainty.
- Escrow refunds and payouts are external transfer messages; dispatched accounting is not proof of recipient credit.
- Historical shipment records remain in storage and carry chain costs.

Hostname checks are admission filtering: they compare the hostname in each submitted URL to the committed host and reject obvious local or malformed targets. They do not authenticate a publisher, establish domain ownership or organizational independence, prove public DNS resolution, or guarantee that redirects remain on the checked host. SHA-256 proves only that fetched bytes equal the committed bytes. DNS and redirect handling are controlled by the GenLayer fetch layer. Integrators needing stronger provenance should use signed artifacts or an authenticated publisher identity.

## Studionet helper scripts

The typed read/write helpers use the pinned `genlayer-js` package in `package.json` and import its normal package entry points. Reads require `THERMO_CONTRACT`, `THERMO_METHOD`, and JSON-array `THERMO_ARGS_JSON`. Writes additionally require `THERMO_PRIVATE_KEY`, supplied through a secure process environment by the operator. The helper never prints or writes the key. Do not place credentials in source files, `.env` files tracked by Git, shell history, or command arguments. GenLayer CLI OS-keychain account unlocking is CLI-specific; the portable SDK helper accepts an in-memory signing key supplied by the caller.

See [DESIGN.md](docs/DESIGN.md) for protocol rules and [DEPLOYMENT.md](docs/DEPLOYMENT.md) for the release/deployment checklist.
