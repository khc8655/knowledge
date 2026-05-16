from services.output_service import OutputService

DEFAULT_CHAPTERS = [
    '项目背景与需求分析',
    '系统架构设计',
    '核心功能说明',
    '安全方案',
    '部署方案',
    '售后服务',
]


class ProposalService:
    def __init__(self, conn):
        self.conn = conn

    def generate(self, project_id, title, customer_context='', industry=None,
                 deployment_type=None, outline=None, template_id=None,
                 required_models=None, forbidden_models=None,
                 output_format='markdown', evidences=None):
        required_models = required_models or []
        forbidden_models = forbidden_models or []
        evidences = evidences or []

        chapters = self._resolve_chapters(outline, template_id)
        content_json = {
            'chapters': [],
            'customer_context': customer_context,
            'industry': industry,
            'deployment_type': deployment_type,
        }

        risk_summary = []
        for ch_title in chapters:
            matched = self._match_evidence_to_chapter(ch_title, evidences, required_models, forbidden_models)
            coverage = min(1.0, len(matched) * 0.5) if matched else 0.0
            chapter = {
                'title': ch_title,
                'evidence_ids': [e.get('id') or e.get('evidence_id', '') for e in matched],
                'coverage': coverage,
            }
            if coverage < 0.6:
                chapter['status'] = '待补证据'
                risk_summary.append(f"章节「{ch_title}」证据覆盖率不足 ({coverage:.0%}) — 待确认")
            else:
                chapter['status'] = 'evidence_ok'
            content_json['chapters'].append(chapter)

        preview_md = self._generate_preview(title, content_json)

        output_svc = OutputService(self.conn)
        output = output_svc.create_output(
            project_id=project_id,
            output_type='proposal',
            title=title,
            content_md=preview_md,
            content_json=content_json,
        )

        for ch in content_json['chapters']:
            for eid in ch.get('evidence_ids', []):
                output_svc.link_evidence(project_id, output['id'], eid, ch['title'], 'primary')

        coverage_map = {ch['title']: ch['coverage'] for ch in content_json['chapters']}

        return {
            'output_id': output['id'],
            'status': 'draft',
            'evidence_coverage': coverage_map,
            'risk_summary': risk_summary,
            'preview_md': preview_md,
        }

    def regenerate_section(self, output_id, chapter_title, evidences=None):
        output_svc = OutputService(self.conn)
        output = output_svc.get_output(output_id)
        if not output:
            return None
        content = output.get('content_json', {})
        if isinstance(content, str):
            import json
            content = json.loads(content)
        for ch in content.get('chapters', []):
            if ch['title'] == chapter_title:
                matched = self._match_evidence_to_chapter(chapter_title, evidences or [], [], [])
                ch['evidence_ids'] = [e.get('id') or e.get('evidence_id', '') for e in matched]
                ch['coverage'] = min(1.0, len(matched) * 0.5) if matched else 0.0
                ch['status'] = 'evidence_ok' if ch['coverage'] >= 0.6 else '待补证据'
                break
        preview_md = self._generate_preview(output['title'], content)
        output_svc.update_output(output_id, content_md=preview_md, content_json=content)
        return output_svc.get_output(output_id)

    def _resolve_chapters(self, outline, template_id):
        if outline:
            return [line.strip() for line in outline.split('\n') if line.strip()]
        return DEFAULT_CHAPTERS

    def _match_evidence_to_chapter(self, chapter_title, evidences, required_models, forbidden_models):
        matched = []
        keywords = set()
        for kw in ['安全', '架构', '部署', '功能', '背景', '售后', '方案']:
            if kw in chapter_title:
                keywords.add(kw)
        for ev in evidences:
            ev_type = ev.get('evidence_type', '')
            claim = ev.get('claim', '')
            body = ev.get('body', '')
            score = 0
            for kw in keywords:
                if kw in claim or kw in body or kw in ev_type:
                    score += 1
            if required_models:
                for m in required_models:
                    if m in body or m in claim:
                        score += 1
            if forbidden_models:
                skip = False
                for m in forbidden_models:
                    if m in body:
                        skip = True
                        break
                if skip:
                    continue
            if score > 0:
                matched.append(ev)
        return matched[:5]

    def _generate_preview(self, title, content_json):
        lines = [f"# {title}\n"]
        for ch in content_json.get('chapters', []):
            status_marker = f" [{ch.get('status', '')}]" if ch.get('status') != 'evidence_ok' else ''
            lines.append(f"## {ch['title']}{status_marker}")
            if ch.get('evidence_ids'):
                lines.append(f"> 引用 {len(ch['evidence_ids'])} 条证据")
            lines.append('')
        return '\n'.join(lines)
