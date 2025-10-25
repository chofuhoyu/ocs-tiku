import logging
import json
import random
import requests
from prompt import PROMPT
from cache import ensure_cache_db, cache_get, cache_set
from logger import setup_root_json_logging

logger = logging.getLogger(__name__)

# 火山方舟平台API配置
VOLCANO_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
VOLCANO_API_KEY = "028c285e-2a60-4349-8e22-ed178c751952"
VOLCANO_MODEL_ID = "doubao-seed-1-6-251015"

def answer(data, guess: bool = False, cache: bool = False) -> str:
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
            return hit

    messages = PROMPT + "\n" + str(data)
    
    # 调用火山方舟平台API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VOLCANO_API_KEY}"
    }
    
    payload = {
        "model": VOLCANO_MODEL_ID,
        "reasoning_effort": "minimal",
        "messages": [
            {"role": "user", "content": messages}
        ],
        "max_completion_tokens": 65535
    }
    
    try:
        response = requests.post(VOLCANO_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        result = response.json()
        ans = result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Failed to call Volcano API: {e}")
        # 如果API调用失败，可以选择返回一个默认答案或者抛出异常
        ans = "API调用失败" if not options else options[0]

    guessed = False
    if guess and isinstance(options, list) and len(options) > 0:
        if ans not in options:
            ans = random.choice(options)
            guessed = True
            logger.warning(
                "Guess enabled: model answer not in options, randomly selected one.")

    if not guessed and cache:
        cache_set(cache_key, ans)

    return ans


if __name__ == "__main__":
    import time

    setup_root_json_logging(logging.INFO)

    start_time = time.time()
    question = {'question': '实验室事故的原因是多种多样的，必须加强全方位的安全监管。',
                'options': ['对', '错']}
    print(answer(question, guess=True, cache=True))
    print("cost time:", time.time() - start_time)

    start_time = time.time()
    question = {'question': '实验室事故的原因是多种多样的，必须加强全方位的安全监管。',
                'options': ['对', '错']}
    print(answer(question, guess=True, cache=True))
    print("cost time:", time.time() - start_time)

    start_time = time.time()
    question = {'question': '实验室安全教育应该常抓不懈，其目的在于：', 'options': [
        '可以据此设置专门的实验室安全教育岗位。', '使研究人员从思想上树立起实验室安全意识，克服存在的侥幸心理，以保证相关规范的贯彻。', '促使研究人员全文背诵实验室安全规范。', '使研究人员尽量少做实验以免发生安全问题。']}
    print(answer(question, guess=False, cache=True))
    print("cost time:", time.time() - start_time)