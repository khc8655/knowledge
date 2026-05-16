"""
Tender Matching Service.
Extracts structured requirements from tender text and matches them
against product evidence and report evidence.
"""

import re
import uuid
from evidence.risk import assess_report_risk, check_model_match

EVIDENCE_KEYWORDS = {
    'CMA': ['CMA', '检测报告', '第三方检测'],
    'CNAS': ['CNAS'],
    '原厂证明函': ['原厂证明', '原厂授权', '厂家证明'],
    '信创认证': ['信创', '适配认证'],
    '兼容性证明': ['兼容性', '互操作'],
}

CAPABILITY_KEYWORDS = {
    'SM2': ['SM2', '国密SM2'],
    'SM3': ['SM3', '国密SM3'],
    'SM4': ['SM4', '国密SM4'],
    'H.323': ['H.323', 'H323'],
    'SIP': ['SIP'],
    'AVC': ['AVC'],
    'SVC': ['SVC'],
    '全编全解': ['全编全解'],
}

MODEL_PATTERN = re.compile(r'[A-Z]{2,}\d{3,}(?:\s*[A-Z]+\d+)?')

REQUIREMENT_TYPE_KEYWORDS = {
    'security': ['加密', '安全', 'SM2', 'SM3', 'SM4', '国密', '认证', '审计'],
    'performance': ['性能', '并发', '延迟', '带宽', '容量', '帧率', '分辨率'],
    'compatibility': ['兼容', '互操作', '适配', '对接', '集成', 'H.323', 'SIP'],
    'price': ['价格', '报价', '预算', '万元', '单价'],
}


class TenderService:
    def __init__(self, conn):
        self.conn = conn

    def extract_requirements(self, tender_text):
        """Extract structured requirements from tender text using rule-based parsing.

        Split by numbered items (1. 2. 3. etc), then for each item:
        - Detect capability requirements from CAPABILITY_KEYWORDS
        - Detect evidence requirements from EVIDENCE_KEYWORDS
        - Detect target models via MODEL_PATTERN
        - Determine requirement_type: security/performance/compatibility/price/general

        Returns list of dicts with: id, raw_text, requirement_type, target_models,
        required_capabilities, required_evidence
        """
        items = re.split(r'(?m)^\s*\d+[.、]\s*', tender_text)
        items = [item.strip() for item in items if item.strip()]

        requirements = []
        for item in items:
            req_id = str(uuid.uuid4())[:8]

            # Detect capabilities
            required_capabilities = []
            for cap_name, keywords in CAPABILITY_KEYWORDS.items():
                for kw in keywords:
                    if kw in item:
                        required_capabilities.append(cap_name)
                        break

            # Detect evidence requirements
            required_evidence = []
            for ev_name, keywords in EVIDENCE_KEYWORDS.items():
                for kw in keywords:
                    if kw in item:
                        required_evidence.append(ev_name)
                        break

            # Detect target models
            target_models = MODEL_PATTERN.findall(item)

            # Determine requirement type
            requirement_type = 'general'
            type_scores = {}
            for rtype, keywords in REQUIREMENT_TYPE_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in item)
                if score > 0:
                    type_scores[rtype] = score
            if type_scores:
                requirement_type = max(type_scores, key=type_scores.get)

            requirements.append({
                'id': req_id,
                'raw_text': item,
                'requirement_type': requirement_type,
                'target_models': target_models,
                'required_capabilities': required_capabilities,
                'required_evidence': required_evidence,
            })

        return requirements

    def match_single(self, requirement, product_evidence, report_evidence):
        """Match a single requirement against product and report evidence.

        Uses evidence.risk.assess_report_risk() for the core logic.

        Returns dict with: requirement_id, judgement, confidence, product_evidence,
        report_evidence, risks
        """
        required_capabilities = requirement.get('required_capabilities', [])
        target_models = requirement.get('target_models', [])

        # Filter product evidence by model match if target models specified
        filtered_product = product_evidence
        if target_models:
            filtered_product = []
            for card in product_evidence:
                card_models = card.get('models', [])
                match_result = check_model_match(target_models, card_models)
                if match_result['match'] or not card_models:
                    filtered_product.append(card)

        # Run risk assessment
        result = assess_report_risk(
            required_capabilities=required_capabilities,
            product_evidence=filtered_product,
            report_evidence=report_evidence,
        )

        # Compute confidence from scores
        if required_capabilities:
            confidence = (result['capability_score'] + result['report_score']) / 2
        else:
            confidence = result['report_score']

        return {
            'requirement_id': requirement['id'],
            'judgement': result['judgement'],
            'confidence': round(confidence, 2),
            'product_evidence': filtered_product,
            'report_evidence': report_evidence,
            'risks': result['risks'],
        }

    def match_batch(self, requirements, evidence_by_capability):
        """Match multiple requirements against evidence.

        Args:
            requirements: list of requirement dicts from extract_requirements
            evidence_by_capability: dict mapping capability name to
                {'product_evidence': [...], 'report_evidence': [...]}

        Returns list of match_single results.
        """
        results = []
        for req in requirements:
            # Aggregate evidence from all required capabilities
            product_evidence = []
            report_evidence = []
            seen_ids = set()

            caps = req.get('required_capabilities', [])
            if not caps:
                # If no specific capability, try all available evidence
                for cap_evidence in evidence_by_capability.values():
                    for card in cap_evidence.get('product_evidence', []):
                        card_id = id(card)
                        if card_id not in seen_ids:
                            seen_ids.add(card_id)
                            product_evidence.append(card)
                    for card in cap_evidence.get('report_evidence', []):
                        card_id = id(card)
                        if card_id not in seen_ids:
                            seen_ids.add(card_id)
                            report_evidence.append(card)
            else:
                for cap in caps:
                    cap_data = evidence_by_capability.get(cap, {})
                    for card in cap_data.get('product_evidence', []):
                        card_id = id(card)
                        if card_id not in seen_ids:
                            seen_ids.add(card_id)
                            product_evidence.append(card)
                    for card in cap_data.get('report_evidence', []):
                        card_id = id(card)
                        if card_id not in seen_ids:
                            seen_ids.add(card_id)
                            report_evidence.append(card)

            result = self.match_single(req, product_evidence, report_evidence)
            results.append(result)

        return results
