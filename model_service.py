from qwen3_model import Qwen3ModelService
from prompt import PROMPT

model = Qwen3ModelService("Qwen/Qwen3-4B")


def answer(question) -> str:
    messages = PROMPT + "\n" + str(question)
    _, content = model.generate(
        messages=[{"role": "user", "content": messages}],
        max_new_tokens=256,
        enable_thinking=False,
    )
    return content


if __name__ == "__main__":
    import time

    start_time = time.time()
    question = "{'question': '实验室事故的原因是多种多样的，必须加强全方位的安全监管。', 'options': ['对', '错']}"
    print(answer(question))
    print("cost time:", time.time() - start_time)

    start_time = time.time()
    question = "{'question': '实验室安全教育应该常抓不懈，其目的在于：', 'options': ['可以据此设置专门的实验室安全教育岗位。', '使研究人员从思想上树立起实验室安全意识，克服存在的侥幸心理，以保证相关规范的贯彻落实。', '促使研究人员全文背诵实验室安全规范。', '使研究人员尽量少做实验以免发生安全问题。']}"
    print(answer(question))
    print("cost time:", time.time() - start_time)
