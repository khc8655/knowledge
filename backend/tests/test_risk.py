import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone, timedelta
from evidence.risk import detect_risk_flags, check_model_match, assess_report_risk


def test_expired_certificate_detected():
    """Test that expired certificates are detected."""
    past_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    card = {
        "report_meta": {
            "valid_to": past_date,
            "scan_available": True,
        },
        "semantic": {"quality_tier": "high"},
    }
    flags = detect_risk_flags(card)
    assert "expired_certificate" in flags
    assert "scan_unavailable" not in flags


def test_scan_unavailable_detected():
    """Test that scan unavailable flag is detected."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    card = {
        "report_meta": {
            "valid_to": future_date,
            "scan_available": False,
        },
        "semantic": {"quality_tier": "high"},
    }
    flags = detect_risk_flags(card)
    assert "scan_unavailable" in flags
    assert "expired_certificate" not in flags


def test_model_mismatch_detected():
    """Test model mismatch detection."""
    result = check_model_match(
        required_models=["Model-A", "Model-B"],
        card_models=["Model-C", "Model-D"],
    )
    assert result["match"] is False
    assert "Model-A" in result["flags"]
    assert "Model-B" in result["flags"]

    # Test match case
    result2 = check_model_match(
        required_models=["Model-A", "Model-B"],
        card_models=["Model-A", "Model-C"],
    )
    assert result2["match"] is True
    assert result2["flags"] == []


def test_missing_report_detected():
    """Test that missing reports are detected in risk assessment."""
    result = assess_report_risk(
        required_capabilities=["cap1"],
        product_evidence=[
            {"tags": ["cap1"], "keywords": [], "related_topics": [], "title": "", "body": ""}
        ],
        report_evidence=[],
    )
    assert "检测报告未确认" in result["risks"]
    assert result["report_score"] == 0.0
    assert result["judgement"] == "partial"


def test_report_expired_risk():
    """Test that expired reports generate risk flags."""
    past_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    result = assess_report_risk(
        required_capabilities=["cap1"],
        product_evidence=[
            {"tags": ["cap1"], "keywords": [], "related_topics": [], "title": "", "body": ""}
        ],
        report_evidence=[
            {"report_meta": {"valid_to": past_date, "scan_available": True}}
        ],
    )
    assert "报告已过期" in result["risks"]
    assert result["report_score"] == 0.0


def test_satisfied_with_valid_report():
    """Test satisfied judgement with valid report and full capability coverage."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    result = assess_report_risk(
        required_capabilities=["cap1", "cap2"],
        product_evidence=[
            {"tags": ["cap1", "cap2"], "keywords": [], "related_topics": [], "title": "", "body": ""}
        ],
        report_evidence=[
            {"report_meta": {"valid_to": future_date, "scan_available": True}}
        ],
    )
    assert result["capability_score"] >= 0.75
    assert result["report_score"] >= 0.75
    assert result["risks"] == []
    assert result["judgement"] == "satisfied"


if __name__ == "__main__":
    test_expired_certificate_detected()
    test_scan_unavailable_detected()
    test_model_mismatch_detected()
    test_missing_report_detected()
    test_report_expired_risk()
    test_satisfied_with_valid_report()
    print("ALL 6 TESTS PASSED")
