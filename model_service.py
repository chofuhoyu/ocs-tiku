import logging
import json
import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

from prompt import PROMPT
from cache import ensure_cache_db, cache_get, cache_set, cache_delete
from logger import setup_logging

logger = logging.getLogger(__name__)

# DeepSeek API配置（从环境变量读取）
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL_ID = os.getenv("DEEPSEEK_MODEL_ID", "deepseek-chat")

def answer(data, guess: bool = False, cache: bool = False) -> tuple[list[str], dict]:
    meta = {"cached": False, "guessed": False}
    options = []
    # 统一构造稳定、可复现的缓存 key：dict 用排序后的 JSON，其他类型用 str
    if isinstance(data, dict):
        options = data.get("options", []) or []
        cache_key = json.dumps(data, ensure_ascii=False, sort_keys=True)
    else:
        cache_key = str(data)

    if cache:
        ensure_cache_db()
        hit = cache_get(cache_key)
        if hit is not None:
            logger.info("Cache hit for question")
            meta["cached"] = True
            try:
                return json.loads(hit), meta
            except json.JSONDecodeError:
                return [hit], meta

    messages = PROMPT + "\n" + str(data)

    # 调用DeepSeek API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": DEEPSEEK_MODEL_ID,
        "messages": [
            {"role": "user", "content": messages}
        ],
        "max_tokens": 4096
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        result = response.json()
        ans_raw = result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Failed to call DeepSeek API: {e}")
        ans_raw = "API调用失败" if not options else options[0]

    ans_list = [a.strip() for a in ans_raw.split("#")]

    guessed = False
    if guess and isinstance(options, list) and len(options) > 0:
        if not all(a in options for a in ans_list):
            ans_list = [random.choice(options)]
            guessed = True
            logger.warning(
                "Guess enabled: model answer(s) not in options, randomly selected one.")

    if guessed:
        meta["guessed"] = True
    elif cache:
        cache_set(cache_key, json.dumps(ans_list, ensure_ascii=False))

    return ans_list, meta


if __name__ == "__main__":
    import time

    setup_logging(logging.INFO)

    test_questions = [
        {'question': '实验室事故的原因是多种多样的，必须加强全方位的安全监管。',
         'type': 'judgement',
         'options': ['对', '错']},
        {'question': '实验室安全教育应该常抓不懈，其目的在于：',
         'type': 'single',
         'options': [
             '可以据此设置专门的实验室安全教育岗位。',
             '使研究人员从思想上树立起实验室安全意识，克服存在的侥幸心理，以保证相关规范的贯彻。',
             '促使研究人员全文背诵实验室安全规范。',
             '使研究人员尽量少做实验以免发生安全问题。'
         ]},
        {'question': '以下哪些属于实验室安全防护装备？',
         'type': 'multiple',
         'options': ['安全眼镜', '防护手套', '运动鞋', '实验室外套']},
    ]

    results = []  # (label, answer_list, duration, options)

    print("=== 第一轮：API调用 ===")
    for q in test_questions:
        start_time = time.time()
        cache_key = json.dumps(q, ensure_ascii=False, sort_keys=True)
        ans_list, _meta = answer(q, guess=True, cache=True)
        duration = round((time.time() - start_time) * 1000)
        results.append(("API调用", ans_list, duration, q.get("options", [])))
        print(f"  [{q['type']}] {'#'.join(ans_list)}")
        print(f"  cost time: {duration}ms")

    print("\n=== 第二轮：缓存命中 ===")
    for q in test_questions:
        start_time = time.time()
        cache_key = json.dumps(q, ensure_ascii=False, sort_keys=True)
        ans_list, _meta = answer(q, guess=True, cache=True)
        duration = round((time.time() - start_time) * 1000)
        results.append(("缓存命中", ans_list, duration, q.get("options", [])))
        print(f"  [{q['type']}] {'#'.join(ans_list)}")
        print(f"  cost time: {duration}ms")

    print("\n=== 清理测试缓存 ===")
    for q in test_questions:
        cache_key = json.dumps(q, ensure_ascii=False, sort_keys=True)
        cache_delete(cache_key)

    # 验证缓存已清理
    cache_cleared = True
    for q in test_questions:
        cache_key = json.dumps(q, ensure_ascii=False, sort_keys=True)
        if cache_get(cache_key) is not None:
            cache_cleared = False
            break

    # ====== 测试总结 ======
    print("\n" + "=" * 50)
    print("  测试总结")
    print("=" * 50)

    checks = []

    # 1. API调用延迟应 > 100ms
    api_times = [r[2] for r in results if r[0] == "API调用"]
    api_ok = all(t > 100 for t in api_times)
    checks.append(("API调用延迟 > 100ms", api_ok, f"{api_times}"))

    # 2. 缓存命中延迟应 < 10ms
    cache_times = [r[2] for r in results if r[0] == "缓存命中"]
    cache_ok = all(t < 10 for t in cache_times)
    checks.append(("缓存命中延迟 < 10ms", cache_ok, f"{cache_times}"))

    # 3. 所有答案非空
    all_answer_lists = [r[1] for r in results]
    answer_ok = all(len(a) > 0 and all(item for item in a) for a in all_answer_lists)
    checks.append(("答案非空", answer_ok, ""))

    # 4. 答案在选项中
    in_options_ok = all(
        all(item in opts for item in ans_list)
        for ans_list, (_, _, _, opts) in zip(all_answer_lists, results)
    )
    checks.append(("答案在选项中", in_options_ok, ""))

    # 5. 缓存清理成功
    checks.append(("缓存清理成功", cache_cleared, ""))

    all_pass = True
    for label, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        line = f"  [{status}] {label}"
        if detail:
            line += f"  ({detail})"
        print(line)

    print("=" * 50)
    if all_pass:
        print("  结论：全部通过，服务运行正常")
    else:
        print("  结论：存在失败项，请检查")
    print("=" * 50)