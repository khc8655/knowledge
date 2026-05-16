"""
BOM (Bill of Materials) Generation Service.
Extracts pricing and model info from evidence cards, detects risks
(discontinued items, missing models, budget overruns), and persists
a structured BOM output.
"""

import re
import uuid
from datetime import datetime, timezone

from services.output_service import OutputService

PRICE_RE = re.compile(r'价格[：:]\s*(\d+(?:\.\d+)?)')
MODEL_RE = re.compile(r'[A-Z]{2,}\d{3,}')

DISCONTINUED_KEYWORDS = ['停', '停产', '停售', '替代', 'EOL']


class BomService:
    def __init__(self, conn):
        self.conn = conn

    def generate(self, project_id, scenario, room_count, deployment_type,
                 required_models, budget_limit, evidences):
        """Generate a BOM from evidence cards.

        Args:
            project_id: presales project id
            scenario: text describing the use-case scenario
            room_count: number of rooms / endpoints
            deployment_type: e.g. 'cloud' | 'on-prem'
            required_models: list of model strings the BOM must include
            budget_limit: maximum total price (float); 0 or None = no limit
            evidences: list of evidence card dicts (from CardStore)

        Returns:
            dict with output_id, lines, total_price, risk_summary
        """
        lines = []
        risk_summary = []
        found_models = set()

        for ev in evidences:
            body = ev.get('body', '') or ''
            title = ev.get('title', '') or ''
            combined = body + ' ' + title

            # Extract price
            price_match = PRICE_RE.search(combined)
            unit_price = float(price_match.group(1)) if price_match else 0.0

            # Extract model
            model_match = MODEL_RE.search(combined)
            model = model_match.group(0) if model_match else ''

            if model:
                found_models.add(model)

            # Detect discontinued
            risk_flags = []
            for kw in DISCONTINUED_KEYWORDS:
                if kw in combined:
                    risk_flags.append('discontinued')
                    risk_summary.append(f'{model or title} 已停售/停产')
                    break

            # Quantity defaults to room_count when applicable
            quantity = room_count if room_count and room_count > 0 else 1
            total_price = unit_price * quantity

            lines.append({
                'name': title,
                'model': model,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'source': ev.get('id', ''),
                'risk_flags': risk_flags,
            })

        # Check required_models not found
        missing = [m for m in (required_models or []) if m not in found_models]
        for m in missing:
            risk_summary.append(f'必需型号 {m} 未在证据中找到')

        # Check budget
        grand_total = sum(ln['total_price'] for ln in lines)
        if budget_limit and budget_limit > 0 and grand_total > budget_limit:
            risk_summary.append(
                f'预算超限：合计 {grand_total} 超出预算 {budget_limit}'
            )

        # Persist via OutputService
        output_svc = OutputService(self.conn)
        content_json = {
            'scenario': scenario,
            'room_count': room_count,
            'deployment_type': deployment_type,
            'lines': lines,
            'total_price': grand_total,
            'risk_summary': risk_summary,
        }
        output = output_svc.create_output(
            project_id=project_id,
            output_type='bom',
            title=f'BOM - {scenario}',
            content_json=content_json,
        )

        return {
            'output_id': output['id'],
            'lines': lines,
            'total_price': grand_total,
            'risk_summary': risk_summary,
        }
