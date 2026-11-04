"""Security tests (run with pytest)."""
import pytest

from app.ai_core.security.input_validation import InputValidator, RateLimiter
from app.ai_core.security.output_validation import OutputValidator
from app.ai_core.security.pii import PIIScanner
from app.ai_core.security.audit import SecurityAuditor


def test_input_validator_length():
    v = InputValidator()
    short = "hello world"
    assert v.validate_text(short) == short
    long_text = "x" * 5001
    with pytest.raises(Exception):
        v.validate_text(long_text)


def test_input_validator_script():
    v = InputValidator()
    with pytest.raises(Exception):
        v.validate_text("<script>alert(1)</script>")


def test_input_validator_file():
    v = InputValidator()
    meta = v.validate_file("doc.pdf", "application/pdf", 1000)
    assert meta["extension"] == ".pdf"
    with pytest.raises(Exception):
        v.validate_file("evil.exe", "application/octet-stream", 1000)
    with pytest.raises(Exception):
        v.validate_file("big.pdf", "application/pdf", 100 * 1024 * 1024)


def test_rate_limiter():
    rl = RateLimiter(max_per_minute=3)
    rl.check("user1")
    rl.check("user1")
    rl.check("user1")
    with pytest.raises(Exception):
        rl.check("user1")
    # different key unaffected
    rl.check("user2")


def test_output_validator_pii():
    ov = OutputValidator()
    res = ov.validate("Contact me at alice@example.com or call +998901234567")
    assert res["pii_found"] is True
    assert "alice@example.com" not in res["content"]
    assert "[REDACTED]" in res["content"]


def test_output_validator_internal_echo():
    ov = OutputValidator()
    res = ov.validate("Normal answer with [SYSTEM] leak")
    assert res["internal_echo"] is True
    assert "[SYSTEM]" not in res["content"]


def test_pii_scanner():
    s = PIIScanner()
    scan = s.scan("Email: bob@school.uz")
    assert scan["pii_found"] is True
    redacted = s.redact("Email: bob@school.uz")
    assert "bob@school.uz" not in redacted


def test_security_auditor():
    a = SecurityAuditor()
    ev = a.record("prompt_injection", "high", details="Bearer secret123 tried override")
    assert ev["severity"] == "high"
    assert "secret123" not in ev["details"]
    assert "[REDACTED]" in ev["details"]
    assert len(a.events) == 1
