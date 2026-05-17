#!/usr/bin/env python3
"""
文档召回测试 — 13 条用例
"""
import json
import requests

BASE = "http://localhost:8000/api/v1"

TEST_CASES = [
    {"id": 1, "query": "AE800的价格是多少？", "expect_keywords": ["AE800", "价格"]},
    {"id": 2, "query": "PE8000的价格是多少？", "expect_keywords": ["PE8000", "价格"]},
    {"id": 3, "query": "AI相关的报价分类有哪些？", "expect_keywords": ["AI", "语音转写", "大模型"]},
    {"id": 4, "query": "可按年购买的固定方数云会议室有哪几种？", "expect_keywords": ["会议室模式", "云会议服务"]},
    {"id": 5, "query": "AE800可以使用的配件有哪些？", "expect_keywords": ["TP10", "遥控器", "传屏器"]},
    {"id": 6, "query": "AE800包含哪些配件？", "expect_keywords": ["终端主机", "摄像机", "麦克风"]},
    {"id": 7, "query": "PE8000什么时候停产？", "expect_keywords": ["停产", "PE8800"]},
    {"id": 8, "query": "XE800与AE800的接口对比", "expect_keywords": ["XE800", "AE800"]},
    {"id": 9, "query": "GE600的招标参数", "expect_keywords": ["GE600"]},
    {"id": 10, "query": "云视频在公安行业的应用有哪些？", "expect_keywords": ["公安", "巡查督导", "会议会商"]},
    {"id": 11, "query": "软件端与硬件端的对比", "expect_keywords": ["软件", "硬件", "对比"]},
    {"id": 12, "query": "NP5000的介绍", "expect_keywords": ["NP5000"]},
    {"id": 13, "query": "互联互通的介绍页面", "expect_keywords": ["互联互通"]},
]


def run_test(tc):
    try:
        r = requests.post(f"{BASE}/query", json={"query": tc["query"]}, timeout=30)
        data = r.json()
    except Exception as e:
        return {"id": tc["id"], "query": tc["query"], "status": "ERROR", "detail": str(e)}

    results = data.get("results", [])
    total = data.get("total", 0)
    intent = data.get("intent", "unknown")

    if total == 0:
        return {"id": tc["id"], "query": tc["query"], "status": "FAIL", "detail": "no results", "intent": intent}

    # Check if any result contains expected keywords
    found_keywords = set()
    top_results = []
    for r in results[:5]:
        body = r.get("body", "") + " " + r.get("title", "")
        top_results.append({"title": r.get("title", "")[:60], "hit_rate": r.get("hit_rate", 0)})
        for kw in tc["expect_keywords"]:
            if kw.lower() in body.lower():
                found_keywords.add(kw)

    coverage = len(found_keywords) / len(tc["expect_keywords"]) if tc["expect_keywords"] else 0
    status = "PASS" if coverage >= 0.3 else "FAIL"

    return {
        "id": tc["id"],
        "query": tc["query"],
        "status": status,
        "intent": intent,
        "total_results": total,
        "keyword_coverage": f"{len(found_keywords)}/{len(tc['expect_keywords'])}",
        "found_keywords": list(found_keywords),
        "top_results": top_results[:3],
    }


def main():
    print("=" * 70)
    print("文档召回测试 — 13 条用例")
    print("=" * 70)

    passed = 0
    failed = 0
    errors = 0

    for tc in TEST_CASES:
        result = run_test(tc)
        status = result["status"]
        if status == "PASS":
            passed += 1
            icon = "✓"
        elif status == "FAIL":
            failed += 1
            icon = "✗"
        else:
            errors += 1
            icon = "!"

        print(f"\n{icon} [{result['id']:2d}] {result['query']}")
        print(f"    status={status} intent={result.get('intent','')} results={result.get('total_results',0)} coverage={result.get('keyword_coverage','')}")
        if result.get("found_keywords"):
            print(f"    found: {result['found_keywords']}")
        if status == "FAIL":
            print(f"    detail: {result.get('detail', '')}")
            if result.get("top_results"):
                print(f"    top hits: {result['top_results']}")

    print("\n" + "=" * 70)
    print(f"结果: {passed} PASS / {failed} FAIL / {errors} ERROR (共 {len(TEST_CASES)} 条)")
    print("=" * 70)

    return failed + errors


if __name__ == "__main__":
    exit(main())
