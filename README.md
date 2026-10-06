# ThermoSeal

ThermoSeal is a standalone GenLayer Intelligent Contract primitive for cold-chain shipment escrow. A sponsor commits the shipment manifest, carrier, logger and delivery evidence hosts, temperature band, excursion allowance, and delivery deadline before funding. The carrier accepts the shipment and later commits a machine-readable temperature log, a delivery record, and optionally one image. Validators independently fetch and hash-check the exact artifacts; deterministic code evaluates the complete temperature log, while GenLayer consensus judges whether the committed records and optional image support the same shipment and delivery.

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

## Studionet deployment

ThermoSeal v0.1.0 is deployed on stable GenLayer Studionet (chain ID 61999) at [0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2](https://explorer-studio.genlayer.com/address/0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2). The deployment transaction [0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb](https://explorer-studio.genlayer.com/tx/0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb) finalized with `MAJORITY_AGREE` and GenVM `SUCCESS`.

The deployed source was retrieved with `gen_getContractCode` through GenLayerJS and compared byte-for-byte with `contracts/thermoseal.py`: both are 38,999 bytes and SHA-256 `52ad40cf50d77eaf840a1f3db4df2ad8c96ca82cec67d3da8ab070a79704ea88`. The live `get_info()` read reports `name=ThermoSeal`, `version=0.1.0`, and `min_escrow_wei=1000000000000000` (0.001 GEN), with the configured limits shown in the contract.

**A shipment lifecycle has not yet been demonstrated on-chain.** No shipment was opened and no escrow funds were sent. At verification time, the installed CLI account list showed no account marked `(unlocked)`, so no authorized signer was available for the required sponsor/carrier writes. Do not treat deployment finality or source parity as lifecycle evidence.

## Limits and trust assumptions

- Hash commitments prove byte identity, not sensor authenticity, shipment reality, custody, authorship, or truth.
- Hostname checks reject obvious local/IP targets and require distinct logger/delivery hostnames, but cannot prove DNS resolution, redirect behavior, domain control, or organizational independence.
- Validators and fetch infrastructure depend on external HTTPS availability. Some unavailable/LLM failures are retryable; some permanent HTTP/content/format failures are blocked. The review timeout makes the sponsor refund callable, but someone still must submit that transaction.
- Temperature checks reason over submitted samples and bounded gaps; they cannot prove unsampled physical temperatures or that a sensor was calibrated or tamper-proof.
- Semantic consensus can disagree or remain undetermined. The contract fails closed; it does not promise an approved outcome or eliminate consensus uncertainty.
- Escrow refunds and payouts are external transfer messages; dispatched accounting is not proof of recipient credit.
- Historical shipment records remain in storage and carry chain costs.

See [DESIGN.md](docs/DESIGN.md) for protocol rules and [DEPLOYMENT.md](docs/DEPLOYMENT.md) for the release/deployment checklist.
