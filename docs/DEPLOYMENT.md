# ThermoSeal release and deployment record

## Current state

ThermoSeal **v0.1.0 is deployed** on stable **GenLayer Studionet, chain ID 61999**.

- Contract: [`0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2`](https://explorer-studio.genlayer.com/address/0x4a9B92e516Dc7795F00e8eD5996287B9332Dc5b2)
- Deployment transaction: [`0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb`](https://explorer-studio.genlayer.com/tx/0x57adc59b168839b0aaaacc4b332d28640d2f991e38dca34123a181e6198f2adb)
- Transaction status: `FINALIZED`
- Consensus: `MAJORITY_AGREE`
- GenVM execution: `SUCCESS`
- `get_info()`: `name=ThermoSeal`, `version=0.1.0`, `min_escrow_wei=1000000000000000`, `min_confidence=80`, `max_text_bytes=24000`, `max_log_bytes=128000`, `max_image_bytes=2000000`, `max_samples=2000`, `max_sample_gap_seconds=900`, `max_excursion_seconds=7200`, `review_window_seconds=604800`, `retry_cooldown_seconds=300`, image evidence `optional_hash_bound_png_jpeg_webp`, timeout refund `permissionless`, sensor identity `not_proven_by_contract`.
- Source retrieval/parity: retrieved using `gen_getContractCode` through GenLayerJS; deployed and local bytes both 38,999; SHA-256 `52ad40cf50d77eaf840a1f3db4df2ad8c96ca82cec67d3da8ab070a79704ea88`; byte-for-byte parity `YES`.

The first deployment attempt used an invalid contract header ordering and did not create a usable contract. It is superseded by the successful deployment above; the failed attempt was `0xc0b564e2ee13af5933bcf8e69aeaac85f1dd366ff390a5d060ad399a82db3365` and is not the current address.

**Live shipment lifecycle: not yet run.** No proposal/open-shipment, carrier acceptance, evidence submission, semantic review, or settlement transaction is claimed. The local CLI account list currently shows no `(unlocked)` signer. Do not send a payable shipment transaction until a signer is available and the parties/evidence are verified.

## Stable toolchain

The contract begins with the runtime-required `# v0.1.0` marker followed by its stable `py-genlayer` dependency hash. The repository pins `genlayer-test==0.29.2`, `genvm-linter==0.11.0`, `pytest==9.1.1`, and GenVM validation bundle `v0.2.16`; it does not pin the Consensus v0.6 release-candidate SDK family. The default Direct Mode/network configuration is Studionet.

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

## Remaining live lifecycle checklist

1. Make an authorized sponsor and distinct carrier signer available on Studionet 61999; do not request or disclose private keys.
2. Prepare immutable, independently retrievable manifest, temperature-log, and delivery-record artifacts. Verify exact raw-byte SHA-256 values before proposing.
3. Open the shipment with the minimum supported escrow (0.001 GEN) only after verifying the sponsor, carrier, committed hostnames, temperature terms, and delivery deadline.
4. Have the designated carrier accept, then submit hash-bound telemetry and delivery evidence.
5. Run review and record its actual finalized consensus and canonical state. Do not force an approval; blocked/retryable results must follow the documented refund/retry paths.
6. If approved or blocked, settle and inspect the transfer child receipt/credited value; `*_dispatched` alone is not proof of recipient credit. If retryable, record the timeout-refund path only after its deadline.
7. Update this file and README only with observed finalized lifecycle evidence. Keep the successful deployment above as current unless a new source is deliberately deployed.

No deployment or live evidence is claimed until those steps are completed.
