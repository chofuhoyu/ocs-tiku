from flask import Flask, json, request, jsonify
import logging
import time
from flask import g
from logger import init_app_logger

from model_service import answer

app = Flask(__name__)
init_app_logger(app)

try:
    app.json.ensure_ascii = False
except Exception:
    app.config['JSON_AS_ASCII'] = False


@app.before_request
def _start_timer_and_capture_input():
    g._start_time = time.perf_counter()
    # 缓存请求体，避免后续视图函数读取受影响
    g._request_body = request.get_data(cache=True, as_text=True)
    g._request_json = request.get_json(silent=True)


@app.after_request
def _log_request_and_response(response):
    duration_ms = None
    if hasattr(g, "_start_time"):
        duration_ms = round((time.perf_counter() - g._start_time) * 1000, 2)

    req_args = request.args.to_dict(flat=True)
    req_json = getattr(g, "_request_json", None)
    req_body = getattr(g, "_request_body", None)

    try:
        resp_json = response.get_json(silent=True)
    except Exception:
        resp_json = None
    resp_text = None if resp_json is not None else response.get_data(
        as_text=True)

    app.logger.info(
        "request handled",
        extra={
            "event": "http_request",
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "remote_addr": request.remote_addr,
            "query": req_args,
            "request_json": req_json if req_json is not None else None,
            "request_body": None if req_json is not None else req_body,
            "response_json": resp_json if resp_json is not None else None,
            "response_body": None if resp_json is not None else resp_text,
        },
    )
    return response


@app.route("/api/config", methods=["GET"])
def api_config():
    config = json.load(open("config.json", "r", encoding="utf-8"))
    return jsonify(config), 200


@app.route("/api/search", methods=["POST"])
def api_search():
    data = json.loads(request.get_data(as_text=True))
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
    return jsonify(resp), 200


@app.route("/", methods=["GET", "HEAD"])
def root_ok():
    return "ok", 200


if __name__ == "__main__":
    # 开发模式运行
    import argparse

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
