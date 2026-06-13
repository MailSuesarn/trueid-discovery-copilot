from app.api.middleware import redact_pii


def test_redacts_thai_national_ids_but_not_short_numbers():
    text = "เลขบัตร 1105267819254 และ 1-2345-67890-12-3 เริ่ม 1234"
    out = redact_pii(text)
    assert "1105267819254" not in out
    assert "1-2345-67890-12-3" not in out
    assert out.count("<REDACTED>") == 2
    assert "1234" in out  # a bare short number must NOT be redacted
