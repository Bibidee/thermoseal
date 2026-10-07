import hashlib
import json
from datetime import datetime, timezone

import pytest


CONTRACT = "contracts/thermoseal.py"
DIRECT_RUNNER_VERSION = "v0.2.16"
NOW = "2026-10-01T12:00:00Z"
NOW_TS = int(datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc).timestamp())
ACCEPTED_AT = NOW_TS + 60
DELIVERED_AT = ACCEPTED_AT + 3600
DEPOSIT = 10**16
MANIFEST_URL = "https://manifest.example.com/TS-001.txt"
LOG_URL = "https://logger.example.net/TS-001.json"
DELIVERY_URL = "https://delivery.example.org/TS-001.txt"
IMAGE_URL = "https://photos.example.co/TS-001.png"
MANIFEST = b"ThermoSeal shipment TS-001: refrigerated medicine, destination Clinic-7."
DELIVERY = b"Shipment TS-001 was delivered to Clinic-7 at the committed destination."
IMAGE = b"\x89PNG\r\n\x1a\n" + b"test-image-bytes"
APPROVED = {
    "shipment_match": "yes",
    "delivery_supported": "yes",
    "risk": "no",
    "confidence": 92,
    "rationale": "The manifest and delivery record identify the same shipment and destination.",
}


def digest(raw):
    return "0x" + hashlib.sha256(raw).hexdigest()


def address_text(address):
    return "0x" + address.hex().lower().removeprefix("0x")


def deploy(direct_vm, direct_deploy):
    direct_vm.warp(NOW)
    # Pin the official runner used by this release.  This keeps Direct Mode
    # independent of the test package's obsolete prerelease fallback.
    return direct_deploy(CONTRACT, sdk_version=DIRECT_RUNNER_VERSION)


def open_shipment(contract, direct_vm, sponsor, carrier, shipment_id="TS-001", amount=DEPOSIT,
                  min_temp=2000, max_temp=8000, max_excursion=600,
                  manifest_url=MANIFEST_URL, manifest_hash=None,
                  logger_host="logger.example.net", delivery_host="delivery.example.org",
                  deadline=None, brief="Deliver refrigerated medicine to Clinic-7."):
    direct_vm.sender = sponsor
    direct_vm.value = amount
    key = contract.open_shipment(
        shipment_id,
        address_text(carrier),
        brief,
        manifest_url,
        manifest_hash or digest(MANIFEST),
        logger_host,
        delivery_host,
        min_temp,
        max_temp,
        max_excursion,
        deadline if deadline is not None else NOW_TS + 3 * 24 * 60 * 60,
    )
    direct_vm.value = 0
    return key


def sponsor_arg(sponsor):
    return address_text(sponsor)


def telemetry(shipment_id="TS-001", temperatures=None, times=None):
    temperatures = temperatures or [4000] * 7
    times = times or [ACCEPTED_AT + 600 * index for index in range(7)]
    return json.dumps({
        "shipment_id": shipment_id,
        "sensor_id": "LOGGER-DECLARED-17",
        "samples": [
            {"timestamp": timestamp, "temp_milli_c": temperature}
            for timestamp, temperature in zip(times, temperatures)
        ],
    }, separators=(",", ":")).encode("utf-8")


def accept_and_submit(contract, direct_vm, sponsor, carrier, shipment_id="TS-001",
                       log_raw=None, delivery_raw=DELIVERY, image_raw=None,
                       delivered_at=DELIVERED_AT, summary="Shipment delivered to Clinic-7."):
    direct_vm.warp("2026-10-01T12:01:00Z")
    direct_vm.sender = carrier
    contract.accept_shipment(sponsor_arg(sponsor), shipment_id)
    direct_vm.warp("2026-10-01T13:01:00Z")
    log_raw = log_raw or telemetry(shipment_id)
    contract.submit_evidence(
        sponsor_arg(sponsor), shipment_id, delivered_at,
        LOG_URL, digest(log_raw), DELIVERY_URL, digest(delivery_raw),
        IMAGE_URL if image_raw is not None else "",
        digest(image_raw) if image_raw is not None else "",
        summary,
    )
    return log_raw, delivery_raw


def configure_review(direct_vm, log_raw=None, delivery_raw=DELIVERY, image_raw=None,
                     analysis=None, manifest=MANIFEST):
    direct_vm.mock_web(MANIFEST_URL, {"status": 200, "body": manifest})
    direct_vm.mock_web(LOG_URL, {"status": 200, "body": log_raw or telemetry()})
    direct_vm.mock_web(DELIVERY_URL, {"status": 200, "body": delivery_raw})
    if image_raw is not None:
        direct_vm.mock_web(IMAGE_URL, {"status": 200, "body": image_raw})
    direct_vm.mock_llm(
        r"You are reviewing hash-verified cold-chain shipment evidence",
        json.dumps(analysis or APPROVED),
    )


def review(contract, direct_vm, sponsor, shipment_id="TS-001"):
    direct_vm.sender = sponsor
    contract.review(sponsor_arg(sponsor), shipment_id)


def test_stable_schema_info_and_funded_open(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    key = open_shipment(contract, direct_vm, direct_alice, direct_bob)
    saved = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert key.endswith(":TS-001")
    assert saved["status"] == "awaiting_carrier"
    assert saved["sponsor"].lower() == address_text(direct_alice)
    assert saved["carrier"].lower() == address_text(direct_bob)
    assert int(saved["deposited"]) == DEPOSIT
    info = contract.get_info()
    assert info["name"] == "ThermoSeal"
    assert info["version"] == "0.1.0"
    assert info["image_evidence"] == "optional_hash_bound_png_jpeg_webp"


def test_open_rejects_invalid_value_parties_hash_hosts_and_temperature(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    direct_vm.sender = direct_alice
    direct_vm.value = DEPOSIT
    args = ["BAD-1", address_text(direct_bob), "Deliver medicine", MANIFEST_URL,
            digest(MANIFEST), "logger.example.net", "delivery.example.org",
            2000, 8000, 600, NOW_TS + 3 * 86400]
    with direct_vm.expect_revert():
        contract.open_shipment(*args[:4], "not-a-hash", *args[5:])
    with direct_vm.expect_revert():
        contract.open_shipment("BAD-2", address_text(direct_alice), *args[2:])
    with direct_vm.expect_revert():
        contract.open_shipment("BAD-3", address_text(direct_bob), " ", *args[3:])
    with direct_vm.expect_revert():
        contract.open_shipment("BAD-4", address_text(direct_bob), "Brief", "http://manifest.example.com/a",
                               *args[4:])
    with direct_vm.expect_revert():
        contract.open_shipment("BAD-5", address_text(direct_bob), "Brief", MANIFEST_URL,
                               digest(MANIFEST), "logger.example.net", "logger.example.net",
                               2000, 8000, 600, NOW_TS + 3 * 86400)
    with direct_vm.expect_revert():
        contract.open_shipment("BAD-6", address_text(direct_bob), "Brief", MANIFEST_URL,
                               digest(MANIFEST), "logger.example.net", "delivery.example.org",
                               8000, 2000, 600, NOW_TS + 3 * 86400)
    direct_vm.value = 0
    direct_vm.value = 10**15 - 1
    with direct_vm.expect_revert():
        contract.open_shipment(*args)
    direct_vm.value = 0


@pytest.mark.parametrize("url", [
    "http://logger.example.net/a",
    "https://localhost/a",
    "https://127.0.0.1/a",
    "https://10.0.0.1/a",
    "https://172.16.0.1/a",
    "https://192.168.1.1/a",
    "https://169.254.1.1/a",
    "https://[::1]/a",
    "https://[fc00::1]/a",
    "https://user:pass@logger.example.net/a",
    "https://logger.example.net:8443/a",
])
def test_open_rejects_unsafe_manifest_urls(direct_vm, direct_deploy, direct_alice, direct_bob, url):
    contract = deploy(direct_vm, direct_deploy)
    direct_vm.sender = direct_alice
    direct_vm.value = DEPOSIT
    with direct_vm.expect_revert():
        contract.open_shipment("TS-URL", address_text(direct_bob), "Brief", url,
                               digest(MANIFEST), "logger.example.net", "delivery.example.org",
                               2000, 8000, 600, NOW_TS + 3 * 86400)
    direct_vm.value = 0


def test_duplicate_shipment_id_is_sponsor_scoped(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    direct_vm.value = DEPOSIT
    with direct_vm.expect_revert():
        contract.open_shipment("TS-001", address_text(direct_charlie), "Other shipment", MANIFEST_URL,
                               digest(MANIFEST), "logger.example.net", "delivery.example.org",
                               2000, 8000, 600, NOW_TS + 3 * 86400)
    direct_vm.value = 0
    direct_vm.sender = direct_charlie
    direct_vm.value = DEPOSIT
    contract.open_shipment("TS-001", address_text(direct_bob), "Other payer shipment", MANIFEST_URL,
                           digest(MANIFEST), "logger.example.net", "delivery.example.org",
                           2000, 8000, 600, NOW_TS + 3 * 86400)
    direct_vm.value = 0


def test_only_assigned_carrier_accepts_and_submits(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert():
        contract.accept_shipment(sponsor_arg(direct_alice), "TS-001")
    direct_vm.sender = direct_bob
    contract.accept_shipment(sponsor_arg(direct_alice), "TS-001")
    direct_vm.warp("2026-10-01T13:01:00Z")
    direct_vm.sender = direct_charlie
    raw_log = telemetry()
    with direct_vm.expect_revert():
        contract.submit_evidence(sponsor_arg(direct_alice), "TS-001", DELIVERED_AT,
                                 LOG_URL, digest(raw_log), DELIVERY_URL, digest(DELIVERY), "", "", "Delivery")


def test_approved_review_and_single_payout_settlement(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    configure_review(direct_vm, raw_log, delivery)
    review(contract, direct_vm, direct_alice)
    reviewed = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert reviewed["status"] == "approved"
    assert int(reviewed["confidence"]) == 92
    assert "same shipment" in reviewed["rationale"]
    contract.settle(sponsor_arg(direct_alice), "TS-001")
    settled = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert settled["status"] == "payout_dispatched"
    assert settled["settlement"] == "carrier_payout_dispatched"
    assert int(settled["deposited"]) == 0
    assert int(settled["dispatched_amount"]) == DEPOSIT
    with direct_vm.expect_revert():
        contract.settle(sponsor_arg(direct_alice), "TS-001")


@pytest.mark.parametrize("analysis", [
    {**APPROVED, "confidence": 79},
    {**APPROVED, "shipment_match": "unclear"},
    {**APPROVED, "shipment_match": "no"},
    {**APPROVED, "delivery_supported": "unclear"},
    {**APPROVED, "delivery_supported": "no"},
    {**APPROVED, "risk": "unclear"},
    {**APPROVED, "risk": "yes"},
])
def test_semantic_uncertainty_or_rejection_never_approves(direct_vm, direct_deploy, direct_alice, direct_bob, analysis):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    configure_review(direct_vm, raw_log, delivery, analysis=analysis)
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "blocked"
    assert int(state["deposited"]) == DEPOSIT
    contract.settle(sponsor_arg(direct_alice), "TS-001")
    refunded = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert refunded["status"] == "refund_dispatched"
    assert refunded["settlement"] == "sponsor_refund_dispatched"
    assert int(refunded["deposited"]) == 0


def test_exact_confidence_threshold_is_eligible_for_approval(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    configure_review(direct_vm, raw_log, delivery, analysis={**APPROVED, "confidence": 80})
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "approved"
    assert int(state["confidence"]) == 80


def test_malformed_model_output_is_retryable_and_timeout_refunds(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    configure_review(direct_vm, raw_log, delivery, analysis={"shipment_match": "yes"})
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "retryable"
    assert state["last_reason"] == "malformed_model_output"
    assert int(state["deposited"]) == DEPOSIT
    with direct_vm.expect_revert():
        contract.settle(sponsor_arg(direct_alice), "TS-001")
    direct_vm.warp("2026-10-09T14:00:00Z")
    contract.timeout_refund(sponsor_arg(direct_alice), "TS-001")
    final = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert final["status"] == "refund_dispatched"
    assert final["settlement"] == "timeout_refund_dispatched"
    assert int(final["deposited"]) == 0
    assert int(final["dispatched_amount"]) == DEPOSIT


def test_fetch_unavailable_remains_retryable_then_refundable(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.mock_web(MANIFEST_URL, {"status": 503, "body": b"unavailable"})
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "retryable"
    assert int(state["deposited"]) == DEPOSIT
    direct_vm.warp("2026-10-09T14:00:00Z")
    contract.timeout_refund(sponsor_arg(direct_alice), "TS-001")
    assert contract.get_shipment(sponsor_arg(direct_alice), "TS-001")["status"] == "refund_dispatched"


def test_payload_hash_mismatch_blocks_and_sponsor_can_refund(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.mock_web(MANIFEST_URL, {"status": 200, "body": MANIFEST + b" changed"})
    direct_vm.mock_web(LOG_URL, {"status": 200, "body": raw_log})
    direct_vm.mock_web(DELIVERY_URL, {"status": 200, "body": delivery})
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "blocked"
    assert state["last_reason"] == "hash_mismatch"
    contract.settle(sponsor_arg(direct_alice), "TS-001")
    assert contract.get_shipment(sponsor_arg(direct_alice), "TS-001")["status"] == "refund_dispatched"


def test_temperature_excursion_is_deterministic_block(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob, max_excursion=0)
    bad_log = telemetry(temperatures=[4000, 4000, 9000, 9000, 4000, 4000, 4000])
    accept_and_submit(contract, direct_vm, direct_alice, direct_bob, log_raw=bad_log)
    direct_vm.mock_web(MANIFEST_URL, {"status": 200, "body": MANIFEST})
    direct_vm.mock_web(LOG_URL, {"status": 200, "body": bad_log})
    direct_vm.mock_web(DELIVERY_URL, {"status": 200, "body": DELIVERY})
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "blocked"
    assert state["last_reason"] == "temperature_limit_exceeded"
    assert int(state["deposited"]) == DEPOSIT


def test_invalid_temperature_log_cannot_approve(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    malformed = b"{not json"
    accept_and_submit(contract, direct_vm, direct_alice, direct_bob, log_raw=malformed)
    direct_vm.mock_web(MANIFEST_URL, {"status": 200, "body": MANIFEST})
    direct_vm.mock_web(LOG_URL, {"status": 200, "body": malformed})
    direct_vm.mock_web(DELIVERY_URL, {"status": 200, "body": DELIVERY})
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "blocked"
    assert state["last_reason"] == "invalid_temperature_log"


@pytest.mark.parametrize("analysis", [
    {key: value for key, value in APPROVED.items() if key != "risk"},
    {**APPROVED, "extra": "not allowed"},
    {**APPROVED, "risk": "maybe"},
    {**APPROVED, "confidence": True},
    {**APPROVED, "confidence": -1},
    {**APPROVED, "confidence": 101},
])
def test_malformed_semantic_output_is_retryable_never_authorizing(
    direct_vm, direct_deploy, direct_alice, direct_bob, analysis
):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    configure_review(direct_vm, raw_log, delivery, analysis=analysis)
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "retryable"
    assert state["last_reason"] == "malformed_model_output"
    assert int(state["deposited"]) == DEPOSIT


@pytest.mark.parametrize("analysis, expected_rationale", [
    ({key: value for key, value in APPROVED.items() if key != "rationale"}, ""),
    ({**APPROVED, "rationale": "x" * 401}, "x" * 400),
])
def test_non_authoritative_rationale_is_optional_and_bounded(
    direct_vm, direct_deploy, direct_alice, direct_bob, analysis, expected_rationale
):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    configure_review(direct_vm, raw_log, delivery, analysis=analysis)
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "approved"
    assert state["rationale"] == expected_rationale


@pytest.mark.parametrize("artifact, failure, expected_status", [
    ("manifest", "http", "retryable"),
    ("log", "http", "retryable"),
    ("delivery", "http", "retryable"),
    ("image", "http", "retryable"),
    ("manifest", "empty", "blocked"),
    ("log", "empty", "blocked"),
    ("delivery", "empty", "blocked"),
    ("image", "empty", "blocked"),
    ("manifest", "mismatch", "blocked"),
    ("log", "mismatch", "blocked"),
    ("delivery", "mismatch", "blocked"),
    ("image", "mismatch", "blocked"),
    ("manifest", "oversize", "blocked"),
    ("log", "oversize", "blocked"),
    ("delivery", "oversize", "blocked"),
    ("image", "oversize", "blocked"),
    ("manifest", "invalid_utf8", "blocked"),
    ("log", "invalid_utf8", "blocked"),
    ("delivery", "invalid_utf8", "blocked"),
    ("image", "bad_format", "blocked"),
])
def test_artifact_failure_matrix_never_approves(
    direct_vm, direct_deploy, direct_alice, direct_bob, artifact, failure, expected_status
):
    contract = deploy(direct_vm, direct_deploy)
    committed = {
        "manifest": MANIFEST,
        "log": telemetry(),
        "delivery": DELIVERY,
        "image": IMAGE if artifact == "image" else None,
    }
    limits = {"manifest": 24_000, "log": 128_000, "delivery": 24_000, "image": 2_000_000}
    if failure in ("empty", "oversize", "invalid_utf8", "bad_format"):
        if failure == "empty":
            committed[artifact] = b""
        elif failure == "oversize":
            committed[artifact] = b"x" * (limits[artifact] + 1)
        elif failure == "invalid_utf8":
            committed[artifact] = b"\xff\xfe"
        elif failure == "bad_format":
            committed[artifact] = b"not-an-image"
    manifest_raw = committed["manifest"]
    log_raw = committed["log"]
    delivery_raw = committed["delivery"]
    image_raw = committed["image"]
    direct_vm.sender = direct_alice
    direct_vm.value = DEPOSIT
    contract.open_shipment(
        "TS-001", address_text(direct_bob), "Deliver refrigerated medicine to Clinic-7.",
        MANIFEST_URL, digest(manifest_raw), "logger.example.net", "delivery.example.org",
        2000, 8000, 600, NOW_TS + 3 * 86400,
    )
    direct_vm.value = 0
    direct_vm.warp("2026-10-01T12:01:00Z")
    direct_vm.sender = direct_bob
    contract.accept_shipment(sponsor_arg(direct_alice), "TS-001")
    direct_vm.warp("2026-10-01T13:01:00Z")
    contract.submit_evidence(
        sponsor_arg(direct_alice), "TS-001", DELIVERED_AT,
        LOG_URL, digest(log_raw), DELIVERY_URL, digest(delivery_raw),
        IMAGE_URL if image_raw is not None else "",
        digest(image_raw) if image_raw is not None else "", "Delivery recorded.",
    )

    bodies = committed
    if failure == "http":
        response = {"status": 503, "body": b"temporarily unavailable"}
    else:
        raw = bodies[artifact]
        if failure == "mismatch":
            raw = raw + b" changed"
        response = {"status": 200, "body": raw}
    url_by_artifact = {
        "manifest": MANIFEST_URL,
        "log": LOG_URL,
        "delivery": DELIVERY_URL,
        "image": IMAGE_URL,
    }
    for name, url in url_by_artifact.items():
        direct_vm.mock_web(url, response if name == artifact else {"status": 200, "body": bodies[name]})
    direct_vm.mock_llm(
        r"You are reviewing hash-verified cold-chain shipment evidence",
        json.dumps(APPROVED),
    )
    direct_vm.sender = direct_alice
    contract.review(sponsor_arg(direct_alice), "TS-001")
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == expected_status
    assert state["status"] != "approved"
    assert int(state["deposited"]) == DEPOSIT


def test_duplicate_json_keys_in_telemetry_fail_closed(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    duplicate_key_log = (
        b'{"shipment_id":"TS-001","shipment_id":"TS-OTHER",'
        b'"sensor_id":"LOGGER-DECLARED-17","samples":'
        b'[{"timestamp":1790856060,"temp_milli_c":4000},'
        b'{"timestamp":1790856660,"temp_milli_c":4000}]}'
    )
    raw_log, delivery = accept_and_submit(
        contract, direct_vm, direct_alice, direct_bob, log_raw=duplicate_key_log
    )
    configure_review(direct_vm, raw_log, delivery, analysis=APPROVED)

    review(contract, direct_vm, direct_alice)

    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "blocked"
    assert state["last_reason"] == "invalid_temperature_log"
    assert int(state["deposited"]) == DEPOSIT


def _prepare_for_validator_check(direct_vm, direct_deploy, direct_alice, direct_bob, leader_analysis):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob)
    configure_review(direct_vm, raw_log, delivery, analysis=leader_analysis)
    review(contract, direct_vm, direct_alice)
    return contract, raw_log, delivery


def _install_validator_analysis(direct_vm, raw_log, delivery, analysis):
    direct_vm.clear_mocks()
    direct_vm.mock_web(MANIFEST_URL, {"status": 200, "body": MANIFEST})
    direct_vm.mock_web(LOG_URL, {"status": 200, "body": raw_log})
    direct_vm.mock_web(DELIVERY_URL, {"status": 200, "body": delivery})
    direct_vm.mock_llm(
        r"You are reviewing hash-verified cold-chain shipment evidence",
        json.dumps(analysis),
    )


def test_genuine_direct_validator_rejects_approval_vs_block(direct_vm, direct_deploy, direct_alice, direct_bob):
    _contract, raw_log, delivery = _prepare_for_validator_check(
        direct_vm, direct_deploy, direct_alice, direct_bob, APPROVED
    )
    _install_validator_analysis(direct_vm, raw_log, delivery, {**APPROVED, "risk": "yes"})
    assert direct_vm.run_validator() is False


def test_genuine_direct_validator_rejects_block_vs_approval(direct_vm, direct_deploy, direct_alice, direct_bob):
    blocked = {**APPROVED, "delivery_supported": "no"}
    _contract, raw_log, delivery = _prepare_for_validator_check(
        direct_vm, direct_deploy, direct_alice, direct_bob, blocked
    )
    _install_validator_analysis(direct_vm, raw_log, delivery, APPROVED)
    assert direct_vm.run_validator() is False


def test_genuine_direct_validator_ignores_rationale_for_same_approval(direct_vm, direct_deploy, direct_alice, direct_bob):
    _contract, raw_log, delivery = _prepare_for_validator_check(
        direct_vm, direct_deploy, direct_alice, direct_bob, APPROVED
    )
    _install_validator_analysis(
        direct_vm, raw_log, delivery,
        {**APPROVED, "confidence": 87, "rationale": "Independent concise explanation, same safe result."},
    )
    assert direct_vm.run_validator() is True


def test_genuine_direct_validator_accepts_distinct_safe_denials(direct_vm, direct_deploy, direct_alice, direct_bob):
    blocked_a = {**APPROVED, "shipment_match": "no"}
    blocked_b = {**APPROVED, "delivery_supported": "no", "rationale": "Delivery evidence does not support the claim."}
    _contract, raw_log, delivery = _prepare_for_validator_check(
        direct_vm, direct_deploy, direct_alice, direct_bob, blocked_a
    )
    _install_validator_analysis(direct_vm, raw_log, delivery, blocked_b)
    assert direct_vm.run_validator() is True


def test_optional_image_is_hash_verified_and_reviewed(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    raw_log, delivery = accept_and_submit(contract, direct_vm, direct_alice, direct_bob, image_raw=IMAGE)
    configure_review(direct_vm, raw_log, delivery, image_raw=IMAGE)
    review(contract, direct_vm, direct_alice)
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "approved"
    assert state["image_hash"] == digest(IMAGE)


def test_only_sponsor_can_cancel_before_acceptance(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert():
        contract.cancel_unaccepted("TS-001")
    direct_vm.sender = direct_alice
    contract.cancel_unaccepted("TS-001")
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "refund_dispatched"
    assert state["settlement"] == "sponsor_cancelled_before_acceptance"
    assert int(state["deposited"]) == 0
    with direct_vm.expect_revert():
        contract.cancel_unaccepted("TS-001")


def test_public_timeout_refund_after_carrier_abandons_acceptance(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    with direct_vm.expect_revert():
        contract.timeout_refund(sponsor_arg(direct_alice), "TS-001")
    direct_vm.warp("2026-10-03T12:00:00Z")
    direct_vm.sender = direct_charlie
    contract.timeout_refund(sponsor_arg(direct_alice), "TS-001")
    state = contract.get_shipment(sponsor_arg(direct_alice), "TS-001")
    assert state["status"] == "refund_dispatched"
    assert state["settlement"] == "timeout_refund_dispatched"
    assert int(state["deposited"]) == 0


def test_carrier_must_submit_before_deadline_and_review_is_permissionless(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert():
        contract.submit_evidence(sponsor_arg(direct_alice), "TS-001", DELIVERED_AT,
                                 LOG_URL, digest(telemetry()), DELIVERY_URL, digest(DELIVERY), "", "", "Summary")
    direct_vm.warp("2026-10-01T12:01:00Z")
    contract.accept_shipment(sponsor_arg(direct_alice), "TS-001")
    direct_vm.warp("2026-10-01T13:01:00Z")
    raw_log = telemetry()
    contract.submit_evidence(sponsor_arg(direct_alice), "TS-001", DELIVERED_AT,
                             LOG_URL, digest(raw_log), DELIVERY_URL, digest(DELIVERY), "", "", "Summary")
    configure_review(direct_vm, raw_log)
    direct_vm.sender = direct_bob
    contract.review(sponsor_arg(direct_alice), "TS-001")
    assert contract.get_shipment(sponsor_arg(direct_alice), "TS-001")["status"] == "approved"


def test_unapproved_status_cannot_settle_and_pending_cannot_be_reviewed(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy)
    open_shipment(contract, direct_vm, direct_alice, direct_bob)
    with direct_vm.expect_revert():
        contract.review(sponsor_arg(direct_alice), "TS-001")
    with direct_vm.expect_revert():
        contract.settle(sponsor_arg(direct_alice), "TS-001")
    assert int(contract.get_shipment(sponsor_arg(direct_alice), "TS-001")["deposited"]) == DEPOSIT
