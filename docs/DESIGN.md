# ThermoSeal design

## Purpose

ThermoSeal is a reusable cold-chain evidence adjudication and escrow primitive. It combines deterministic temperature-log evaluation with validator consensus over the meaning and consistency of a committed manifest, delivery record, and optional image. The carrier summary is stored for audit display but is not authoritative evidence and is not included in the model prompt. ThermoSeal does not certify physical truth or sensor identity.

## Roles and commitments

- **Sponsor:** opens a sponsor-scoped shipment record, deposits GEN, fixes the carrier, manifest hash, logger and delivery hostnames, temperature terms, deadline, and brief.
- **Carrier:** accepts before `accept_by`, then submits a delivery timestamp, hash-bound telemetry and delivery record, optional hash-bound image from the sponsor-committed delivery host, and a bounded informational summary.
- **Any caller:** may trigger review, settle a finalized approved/blocked state, or trigger a matured timeout refund. The recipient is not caller-selected.

Shipment IDs are scoped by sponsor address, so one sponsor cannot squat another sponsor's ID. Logger and delivery hostnames must be distinct; telemetry must match the committed logger host, and delivery record and optional image must match the committed delivery host. These hostname checks are admission filtering, not cryptographic publisher authentication, proof of DNS resolution, proof that redirects remain on-host, proof of domain ownership, or proof of organizational independence. SHA-256 proves exact byte identity only. DNS and redirects are handled by the GenLayer fetch layer. Integrators requiring strong provenance should use signed evidence or authenticated publisher identity.

## Deterministic temperature rule

The committed logger artifact must be UTF-8 JSON with exactly:

```json
{
  "shipment_id": "TS-001",
  "sensor_id": "device-label",
  "samples": [
    {"timestamp": 1790856060, "temp_milli_c": 4000},
    {"timestamp": 1790856660, "temp_milli_c": 4100}
  ]
}
```

Each sample object has exactly the two displayed fields; duplicate JSON keys anywhere in the log are rejected instead of being silently resolved by parser-specific last-key-wins behavior. The contract requires 2–2,000 strictly time-ordered samples, supported temperatures between -100 and +100 °C (stored as signed milli-°C), timestamps between carrier acceptance and the submitted delivery time, no adjacent gap above 15 minutes, and first/last coverage gaps no greater than five minutes. For each adjacent pair, the full interval is conservatively counted as excursion time if either endpoint is outside the sponsor's inclusive temperature band. Initial/final boundary time is also counted when the nearest sample is outside the band. Coverage must be complete and counted excursion must not exceed the sponsor's bounded allowance (0–2 hours). This deliberately conservative sampling rule may reject otherwise acceptable shipments.

Temperature records are caller-provided bytes. Their hash and parsed consistency are verifiable; their physical authenticity, calibration, and completeness between samples are not.

## Exact-byte artifact pipeline

For every review, both leader and validator:

1. Fetch manifest, telemetry, delivery record, and optional image independently over HTTPS. Optional image admission requires its URL hostname to equal the sponsor-committed delivery hostname.
2. Require a successful response, bounded non-empty raw bytes, and exact SHA-256 match before decoding or semantic use.
3. Decode manifest/delivery as UTF-8; parse and deterministically evaluate the full telemetry JSON; validate the optional image as PNG, JPEG, or WebP.
4. Only after integrity checks, call the LLM with the textual artifacts, deterministic telemetry result, and optional image bytes.

The manifest, delivery text, URLs, telemetry metadata, and visible image text are framed as untrusted data. Instructions inside them must not be followed. Carrier summary is excluded from the prompt, so it cannot act as semantic evidence. Hostname admission blocks obvious local names, IP literals, credentials, non-HTTPS schemes, non-default ports, fragments, and malformed authorities. This is not DNS/redirect protection: the GenLayer fetch layer controls actual resolution and redirects, and the contract cannot prove that a hostname resolves publicly or stays on the same host after redirect. Prompt framing reduces instruction confusion but cannot guarantee that a model is immune to prompt injection; malformed or uncertain outputs fail closed.

## Semantic schema and equivalence

Required decision fields:

- `shipment_match`: `yes`, `no`, or `unclear`;
- `delivery_supported`: `yes`, `no`, or `unclear`;
- `risk`: `yes`, `no`, or `unclear`;
- `confidence`: integer 0–100 (canonical decimal string is normalized deterministically);
- `rationale`: optional explanatory text, capped at 400 characters.

Approval is derived deterministically and only when the complete semantic tuple is `yes / yes / no`, confidence is at least 80, and deterministic temperature checks pass. Missing or malformed decision fields never approve. Rationale cannot change authorization and is sanitized rather than made consensus-critical.

Validators agree on whether the result authorizes payment, not exact prose. Every approval observation independently must satisfy the approval tuple. If one derives approval and another derives rejection/retryable, equivalence fails. Different valid rejection reasons may be equivalent because both only permit sponsor refund. Retryable infrastructure/model failures may agree with one another, but cannot authorize payout. A consensus disagreement leaves the prior canonical contract state unchanged; after the fixed review deadline, anyone can trigger the timeout refund.

## Lifecycle and transitions

| Current state | Trigger | Next state | Escrow effect |
|---|---|---|---|
| `awaiting_carrier` | Assigned carrier accepts while `now < accept_by` | `in_transit` | Held |
| `awaiting_carrier` | Sponsor cancels before acceptance deadline | `refund_dispatched` | Sponsor refund dispatched |
| `awaiting_carrier` | Public acceptance timeout at `now >= accept_by` | `refund_dispatched` | Sponsor refund dispatched |
| `in_transit` | Assigned carrier submits evidence while `now < delivery_by` and delivery time is valid | `evidence_submitted` | Held |
| `in_transit` | Public delivery timeout at `now >= delivery_by` | `refund_dispatched` | Sponsor refund dispatched |
| `evidence_submitted` / `retryable` | Valid safe review while `now < review_deadline` | `approved` | Held until settle |
| `evidence_submitted` / `retryable` | Valid negative/uncertain result or permanent artifact/content defect before deadline | `blocked` | Held until settle |
| `evidence_submitted` / `retryable` | Transient fetch/LLM failure or malformed model result before deadline | `retryable` | Held; retry cooldown and fixed review deadline |
| `approved` | Permissionless settle | `payout_dispatched` | Carrier transfer dispatched |
| `blocked` | Permissionless settle | `refund_dispatched` | Sponsor transfer dispatched |
| `evidence_submitted` / `retryable` | Public review timeout at `now >= review_deadline` | `refund_dispatched` | Sponsor refund dispatched |

No cancellation is allowed after carrier acceptance. There is no owner or emergency role. State writes and ledger debits occur outside nondeterministic callbacks. At each deadline, the corresponding action is closed and its timeout refund is open at the same `now >= deadline` boundary, so review/acceptance/evidence submission and timeout paths do not overlap.

## Accounting and transfers

`deposited` records the amount currently held. Settlement reads only that field, rejects zero, sets it to zero, records `dispatched_amount`, terminal status, and recipient route, then calls the sole `_send_gen` helper. A second settlement cannot spend the same ledger amount. GEN transfers are external messages; a terminal `*_dispatched` state records dispatch only, not a credited balance. Integrators should inspect the finalized child message/receipt and credited value where available.

## Known limitations

- No on-chain attestation that a sensor is genuine or that evidence represents a real shipment.
- HTTPS/hostname checks are admission filters; they do not prove DNS safety, redirect targets, publisher identity, domain ownership, organizational independence, or physical truth.
- Optional visual interpretation depends on the network's configured vision-capable models; provider/model failures are retryable and never approve.
- Consensus may be undetermined; retries and timeout refund provide a safe state path but do not guarantee finalization.
- External transfer dispatch can fail independently after contract state commits; no authenticated in-contract reconciliation mechanism is assumed.
