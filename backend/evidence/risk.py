"""
Risk flag detection and report assessment service.
Detects issues with product evidence cards and assesses report risk for tender matching.
"""

from datetime import datetime, timezone


def detect_risk_flags(card):
    """
    Detect risk flags in a product evidence card.

    Flags detected:
    - expired_certificate: report_meta.valid_to is in the past
    - scan_unavailable: report_meta.scan_available is False
    - unannotated: quality_tier is 'placeholder'

    Returns:
        list of flag strings
    """
    flags = []

    report_meta = card.get("report_meta")
    if report_meta:
        # Check for expired certificate
        valid_to = report_meta.get("valid_to")
        if valid_to:
            try:
                if isinstance(valid_to, str):
                    expiry = datetime.fromisoformat(valid_to.replace("Z", "+00:00"))
                else:
                    expiry = valid_to
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry < datetime.now(timezone.utc):
                    flags.append("expired_certificate")
            except (ValueError, TypeError):
                pass

        # Check for scan unavailable
        scan_available = report_meta.get("scan_available")
        if scan_available is False:
            flags.append("scan_unavailable")

    # Check for unannotated (placeholder quality tier)
    semantic = card.get("semantic")
    if semantic and semantic.get("quality_tier") == "placeholder":
        flags.append("unannotated")

    return flags


def check_model_match(required_models, card_models):
    """
    Check if any required model matches card models.

    Args:
        required_models: list of model strings required
        card_models: list of model strings in the card

    Returns:
        dict with 'match' (bool) and 'flags' (list of mismatched models)
    """
    if not required_models:
        return {"match": True, "flags": []}

    if not card_models:
        return {"match": False, "flags": required_models[:]}

    # Normalize for comparison
    card_set = {m.lower().strip() for m in card_models}
    matched = any(m.lower().strip() in card_set for m in required_models)

    if matched:
        return {"match": True, "flags": []}
    else:
        return {"match": False, "flags": required_models[:]}


def assess_report_risk(required_capabilities, product_evidence, report_evidence):
    """
    Main risk assessment for tender matching.

    Args:
        required_capabilities: list of capability strings needed
        product_evidence: list of product evidence cards
        report_evidence: list of report evidence cards

    Returns:
        dict with:
        - capability_score: float 0-1
        - report_score: float 0-1
        - risks: list of risk strings
        - judgement: 'satisfied' | 'partial' | 'unknown' | 'not_satisfied'
        - message: summary message
    """
    risks = []

    # Score capability evidence (0-1)
    capability_score = _score_capabilities(required_capabilities, product_evidence)

    # Score report evidence (0-1)
    report_score = _score_reports(report_evidence, risks)

    # Determine judgement
    judgement = _determine_judgement(capability_score, report_score, risks)

    # Generate message
    message = _generate_message(judgement, capability_score, report_score, risks)

    return {
        "capability_score": capability_score,
        "report_score": report_score,
        "risks": risks,
        "judgement": judgement,
        "message": message,
    }


def _score_capabilities(required_capabilities, product_evidence):
    """Score how well product evidence covers required capabilities."""
    if not required_capabilities:
        return 1.0

    if not product_evidence:
        return 0.0

    # Build set of covered capabilities from evidence
    covered = set()
    for card in product_evidence:
        # Check tags, keywords, and related_topics
        for field in ["tags", "keywords", "related_topics"]:
            items = card.get(field, [])
            if items:
                covered.update(item.lower().strip() for item in items)

        # Also check title and body for capability mentions
        title = (card.get("title") or "").lower()
        body = (card.get("body") or "").lower()
        for cap in required_capabilities:
            cap_lower = cap.lower()
            if cap_lower in title or cap_lower in body:
                covered.add(cap_lower)

    matched = sum(1 for cap in required_capabilities if cap.lower() in covered)
    return matched / len(required_capabilities)


def _score_reports(report_evidence, risks):
    """Score report evidence quality, appending risks as side effect."""
    if not report_evidence:
        risks.append("检测报告未确认")
        return 0.0

    scores = []
    for report in report_evidence:
        report_meta = report.get("report_meta", {})

        if not report_meta:
            scores.append(0.0)
            continue

        # Check for expired report
        valid_to = report_meta.get("valid_to")
        if valid_to:
            try:
                if isinstance(valid_to, str):
                    expiry = datetime.fromisoformat(valid_to.replace("Z", "+00:00"))
                else:
                    expiry = valid_to
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry < datetime.now(timezone.utc):
                    risks.append("报告已过期")
                    scores.append(0.0)
                    continue
            except (ValueError, TypeError):
                pass

        # Check scan availability
        scan_available = report_meta.get("scan_available", True)
        if not scan_available:
            scores.append(0.3)
            continue

        # Full score for valid, available report
        scores.append(1.0)

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def _determine_judgement(capability_score, report_score, risks):
    """Determine overall judgement based on scores and risks."""
    has_risk = len(risks) > 0

    if capability_score >= 0.75 and report_score >= 0.75 and not has_risk:
        return "satisfied"
    elif capability_score >= 0.75 and report_score < 0.75:
        return "partial"
    elif 0.4 <= capability_score < 0.75:
        return "unknown"
    else:
        return "not_satisfied"


def _generate_message(judgement, capability_score, report_score, risks):
    """Generate a human-readable summary message."""
    messages = {
        "satisfied": "能力与报告均满足要求",
        "partial": "能力满足但报告不完整",
        "unknown": "能力覆盖不足，需进一步确认",
        "not_satisfied": "能力或报告严重不足",
    }

    base = messages.get(judgement, "未知状态")
    if risks:
        base += f"；风险项：{', '.join(risks)}"

    return base
