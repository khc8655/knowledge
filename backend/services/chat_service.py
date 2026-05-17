"""
对话编排服务 — 意图检测 → 搜索/生成 → SSE 流式输出
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

import httpx
import requests

from db.models import get_db
from config import AppConfig


INTENT_SYSTEM_PROMPT = """你是小鱼易连产品知识库的意图分类器。根据用户消息判断意图，输出JSON。

输出格式（只输出JSON，不要其他文字）:
{"intent": "<intent>", "params": {"query": "<搜索词>"}}

intent 取值:
- search: 查询产品信息（价格、参数、型号、对比、配件、停产、功能、规格等）。这是最常见的情况。
- proposal: 用户明确要求生成方案文档
- tender: 用户明确要求分析招标文件
- bom: 用户明确要求生成BOM清单/配置报价
- reply: 用户明确要求撰写客户回复
- clarify: 用户消息太模糊，无法判断要查什么
- general: 纯闲聊、打招呼、与产品无关的问题

示例:
用户: "AE800价格是多少？" → {"intent":"search","params":{"query":"AE800 价格"}}
用户: "PE8000什么时候停产" → {"intent":"search","params":{"query":"PE8000 停产"}}
用户: "XE800和AE800对比" → {"intent":"search","params":{"query":"XE800 AE800 对比"}}
用户: "帮我做个方案" → {"intent":"proposal","params":{"query":"方案"}}
用户: "你好" → {"intent":"general","params":{"query":""}}

规则:
1. 默认归类为search，只有用户明确要求生成文档/方案时才用其他intent
2. 提取query时补全上下文（如代词指代之前的型号）
3. 只输出JSON"""


SEARCH_SYSTEM_PROMPT = """你是小鱼易连产品知识库助手。根据检索到的知识库卡片内容，回答用户的问题。

要求:
1. 基于卡片内容回答，不要编造信息
2. 如果卡片中有具体数据（价格、参数、型号），准确引用
3. 回答简洁专业，用中文
4. 如果卡片内容不足以回答，坦诚说明"""


GENERAL_SYSTEM_PROMPT = """你是小鱼易连产品知识库AI助手。你可以帮助用户:
- 查询产品信息、价格、参数
- 生成方案文档、招标应答、BOM清单、客户回复
- 回答关于小鱼易连产品的一般问题

请用中文简洁专业地回答。"""


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _llm_stream_sync(profile: dict, messages: list, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, temperature: float = 0.7, max_tokens: int = 2000):
    """同步流式调用 LLM，将 token 放入 asyncio Queue (线程安全)。"""
    try:
        resp = requests.post(
            f"{profile['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {profile['api_key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": profile["model"],
                "messages": messages,
                "stream": True,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=120,
            stream=True,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if not decoded.startswith("data: "):
                continue
            payload = decoded[6:]
            if payload.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta:
                    loop.call_soon_threadsafe(queue.put_nowait, delta)
            except (json.JSONDecodeError, IndexError, KeyError):
                continue
    except Exception as e:
        loop.call_soon_threadsafe(queue.put_nowait, f"\n\n[LLM 调用失败: {str(e)}]")
    finally:
        loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel: done


async def _llm_stream(profile: dict, messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> AsyncGenerator[str, None]:
    """调用 LLM 流式接口，逐 token 返回。"""
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _llm_stream_sync, profile, messages, queue, loop, temperature, max_tokens)
    while True:
        token = await queue.get()
        if token is None:
            break
        yield token


async def _llm_call_sync(profile: dict, messages: list, temperature: float = 0.1, max_tokens: int = 500) -> str:
    """同步调用 LLM（用于意图检测等短任务）。"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{profile['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {profile['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": profile["model"],
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return json.dumps({"intent": "general", "params": {"query": ""}})


def _detect_intent_fallback(content: str) -> dict:
    """关键词回退意图检测。"""
    c = content.lower()
    if any(kw in c for kw in ['价格', '报价', '多少钱', '费用']):
        return {"intent": "search", "params": {"query": content}}
    if any(kw in c for kw in ['方案', '可研']):
        return {"intent": "proposal", "params": {"query": content}}
    if any(kw in c for kw in ['招标', '投标']):
        return {"intent": "tender", "params": {"query": content}}
    if any(kw in c for kw in ['bom', '清单', '报价单']):
        return {"intent": "bom", "params": {"query": content}}
    if any(kw in c for kw in ['回复', '客户答复']):
        return {"intent": "reply", "params": {"query": content}}
    return {"intent": "search", "params": {"query": content}}


def _build_card_context(cards: list, max_chars: int = 4000) -> str:
    """将搜索结果构建为 LLM 上下文。"""
    parts = []
    total = 0
    for i, card in enumerate(cards):
        title = card.get("title", "")
        body = card.get("body", "")
        source = card.get("doc_file", "")
        brand = card.get("brand", "")
        hit = card.get("hit_rate", 0)
        brand_str = f" | 品牌: {brand}" if brand else ""
        text = f"[卡片{i+1}] {title}\n来源: {source} | 命中率: {hit:.0%}{brand_str}\n{body}"
        if total + len(text) > max_chars:
            break
        parts.append(text)
        total += len(text)
    return "\n\n---\n\n".join(parts)


def _build_messages(history: list, system_prompt: str, user_content: str, context: str = None, history_limit: int = 10) -> list:
    """构建发送给 LLM 的 messages 数组。"""
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-history_limit:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    if context:
        user_content = f"以下是知识库检索结果:\n\n{context}\n\n用户问题: {user_content}"
    messages.append({"role": "user", "content": user_content})
    return messages


def _save_message(session_id: str, role: str, content: str, intent: str = None, cards: list = None, thinking: str = None) -> str:
    """保存消息到数据库。"""
    msg_id = uuid.uuid4().hex[:16]
    now = datetime.utcnow().isoformat()
    cards_json = json.dumps(cards, ensure_ascii=False) if cards else None
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO chat_messages (id, session_id, role, content, intent, cards_json, thinking_text, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (msg_id, session_id, role, content, intent, cards_json, thinking, now),
        )
        conn.execute("UPDATE chat_sessions SET updated_at=? WHERE id=?", (now, session_id))
        conn.commit()
    finally:
        conn.close()
    return msg_id


def _auto_title(content: str) -> str:
    """从用户首条消息生成会话标题。"""
    title = content.strip()[:30]
    if len(content) > 30:
        title += "..."
    return title


async def stream_chat_response(
    session_id: str,
    user_content: str,
    mode_override: str = None,
) -> AsyncGenerator[str, None]:
    """核心对话编排：意图检测 → 执行 → 流式输出。"""
    config = AppConfig()
    max_cards = config.get("max_cards_per_response", 5)
    history_limit = config.get("chat_history_limit", 10)

    # 1. 保存用户消息
    _save_message(session_id, "user", user_content)

    # 2. 加载历史
    conn = get_db()
    try:
        session = dict(conn.execute("SELECT * FROM chat_sessions WHERE id=?", (session_id,)).fetchone())
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE session_id=? AND role IN ('user','assistant') ORDER BY created_at DESC LIMIT ?",
            (session_id, history_limit),
        ).fetchall()
        history = [dict(r) for r in reversed(rows)]

        # 自动标题
        if session["title"] == "新对话":
            new_title = _auto_title(user_content)
            conn.execute("UPDATE chat_sessions SET title=? WHERE id=?", (new_title, session_id))
            conn.commit()
    finally:
        conn.close()

    # 3. 意图检测
    mode = mode_override or session.get("mode", "auto")

    if mode == "auto":
        yield _sse_event("thinking", {"stage": "intent_detection", "detail": "正在分析您的问题..."})
        default_profile = config.get_llm_profile("default")
        intent_resp = await _llm_call_sync(
            default_profile,
            [{"role": "system", "content": INTENT_SYSTEM_PROMPT},
             {"role": "user", "content": user_content}],
        )
        try:
            intent_data = json.loads(intent_resp.strip())
            intent = intent_data.get("intent", "search")
            query = intent_data.get("params", {}).get("query", user_content)
        except (json.JSONDecodeError, AttributeError):
            intent_data = _detect_intent_fallback(user_content)
            intent = intent_data["intent"]
            query = intent_data["params"]["query"]
    else:
        intent = mode
        query = user_content

    # 4. 按意图分发
    if intent == "search":
        async for event in _handle_search(session_id, history, query, config, max_cards, history_limit):
            yield event
    elif intent in ("proposal", "tender", "bom", "reply"):
        async for event in _handle_generation(session_id, history, intent, query, config, history_limit):
            yield event
    elif intent == "clarify":
        async for event in _handle_clarify(session_id, history, user_content, config):
            yield event
    else:
        async for event in _handle_general(session_id, history, user_content, config):
            yield event


async def _handle_search(session_id, history, query, config, max_cards, history_limit=10) -> AsyncGenerator[str, None]:
    """搜索意图处理。"""
    yield _sse_event("thinking", {"stage": "searching", "detail": f"正在搜索: {query}"})

    from index.search import unified_search
    search_result = unified_search(query, limit=max_cards)
    cards = search_result.get("results", [])
    search_intent = search_result.get("intent", "default")

    yield _sse_event("cards", {"cards": cards, "intent": search_intent, "total": len(cards)})

    if not cards:
        yield _sse_event("text", {"delta": "抱歉，没有找到相关的知识库内容。请尝试换个关键词或描述更详细一些。"})
        _save_message(session_id, "assistant", "抱歉，没有找到相关的知识库内容。", intent="search", cards=[])
        yield _sse_event("done", {"total_cards": 0})
        return

    yield _sse_event("thinking", {"stage": "generating", "detail": "正在生成回答..."})

    context = _build_card_context(cards)
    gen_profile = config.get_llm_profile("generation")
    messages = _build_messages(history, SEARCH_SYSTEM_PROMPT, query, context, history_limit)

    full_text = ""
    async for delta in _llm_stream(gen_profile, messages):
        full_text += delta
        yield _sse_event("text", {"delta": delta})

    _save_message(session_id, "assistant", full_text, intent="search", cards=cards)
    yield _sse_event("done", {"total_cards": len(cards)})


async def _handle_generation(session_id, history, intent, query, config, history_limit=10) -> AsyncGenerator[str, None]:
    """方案/招标/BOM/回复生成意图处理。"""
    intent_labels = {"proposal": "方案", "tender": "招标", "bom": "BOM", "reply": "回复"}
    label = intent_labels.get(intent, intent)

    yield _sse_event("thinking", {"stage": "searching", "detail": f"正在检索{label}相关资料..."})

    # 先搜索相关资料
    from index.search import unified_search
    search_result = unified_search(query, limit=10)
    cards = search_result.get("results", [])

    yield _sse_event("cards", {"cards": cards, "intent": intent, "total": len(cards)})

    yield _sse_event("thinking", {"stage": "generating", "detail": f"正在生成{label}内容..."})

    context = _build_card_context(cards) if cards else ""

    gen_prompts = {
        "proposal": "你是一位资深的售前工程师。根据知识库资料，为用户生成一份方案文档大纲。包括：项目背景、需求分析、解决方案、产品选型、实施计划等章节。每个章节用知识库中的具体产品型号和参数支撑。",
        "tender": "你是一位招标应答专家。根据知识库资料，帮助用户分析招标需求并给出应答建议。逐条列出技术要求，对应产品参数和优势。",
        "bom": "你是一位BOM配置专家。根据知识库资料，为用户生成一份产品配置清单（BOM）。列出产品型号、数量、单价、小计。注意检查产品是否停产。",
        "reply": "你是一位客户沟通专家。根据知识库资料，帮助用户撰写一份专业的客户回复。回复要准确、专业、有理有据。",
    }
    system_prompt = gen_prompts.get(intent, GENERAL_SYSTEM_PROMPT)

    gen_profile = config.get_llm_profile("generation")
    messages = _build_messages(history, system_prompt, query, context, history_limit)

    full_text = ""
    async for delta in _llm_stream(gen_profile, messages, max_tokens=3000):
        full_text += delta
        yield _sse_event("text", {"delta": delta})

    _save_message(session_id, "assistant", full_text, intent=intent, cards=cards)
    yield _sse_event("done", {"total_cards": len(cards)})


async def _handle_clarify(session_id, history, user_content, config) -> AsyncGenerator[str, None]:
    """澄清意图处理。"""
    yield _sse_event("thinking", {"stage": "clarifying", "detail": "需要更多信息..."})

    gen_profile = config.get_llm_profile("generation")
    messages = _build_messages(history, GENERAL_SYSTEM_PROMPT, user_content)

    full_text = ""
    async for delta in _llm_stream(gen_profile, messages, max_tokens=500):
        full_text += delta
        yield _sse_event("text", {"delta": delta})

    _save_message(session_id, "assistant", full_text, intent="clarify")
    yield _sse_event("done", {"total_cards": 0})


async def _handle_general(session_id, history, user_content, config) -> AsyncGenerator[str, None]:
    """一般对话处理。"""
    yield _sse_event("thinking", {"stage": "thinking", "detail": "思考中..."})

    gen_profile = config.get_llm_profile("generation")
    messages = _build_messages(history, GENERAL_SYSTEM_PROMPT, user_content)

    full_text = ""
    async for delta in _llm_stream(gen_profile, messages, max_tokens=1500):
        full_text += delta
        yield _sse_event("text", {"delta": delta})

    _save_message(session_id, "assistant", full_text, intent="general")
    yield _sse_event("done", {"total_cards": 0})
