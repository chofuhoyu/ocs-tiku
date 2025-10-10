from flask import Flask, json, request, jsonify

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
    print(f"Received data: {data}")
    ans = answer(data)
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
    print(f"Response data: {resp}")
    return jsonify(resp), 200


@app.route("/", methods=["GET", "HEAD"])
def root_ok():
    return "ok", 200


if __name__ == "__main__":
    # 开发模式运行
    app.run(host="0.0.0.0", port=9999, debug=True)
