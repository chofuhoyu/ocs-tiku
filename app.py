from flask import Flask, json, request, jsonify
import logging

from model_service import answer

app = Flask(__name__)

try:
    app.json.ensure_ascii = False
except Exception:
    app.config['JSON_AS_ASCII'] = False


@app.route("/api/config", methods=["GET"])
def api_config():
    config = json.load(open("config.json", "r", encoding="utf-8"))
    return jsonify(config), 200


@app.route("/api/search", methods=["POST"])
def api_search():
    data = json.loads(request.get_data(as_text=True))
    app.logger.info(f"Received data: {data}")
    ans = answer(
        data,
        guess=app.config.get("GUESS", False),
        cache=app.config.get("CACHE", False),
    )
    resp = {
        "code": 0,
        "question": data.get("question", ""),
        "options": data.get("options", []),
        "answer": {
            "allAnswer": [
                [ans],
            ]
        }
    }
    app.logger.info(f"Response data: {resp}")
    return jsonify(resp), 200


@app.route("/", methods=["GET", "HEAD"])
def root_ok():
    return "ok", 200


if __name__ == "__main__":
    # 开发模式运行
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--guess", action="store_true",
                        help="若模型答案不在选项中，则随机从选项中选择答案返回")
    parser.add_argument("--cache", action="store_true", help="启用本地缓存（题目->答案）")
    args = parser.parse_args()

    app.config["GUESS"] = args.guess
    app.config["CACHE"] = args.cache
    app.logger.info(
        f"Server starting with guess={args.guess}, cache={args.cache}")

    app.run(host="0.0.0.0", port=9999, debug=True)
