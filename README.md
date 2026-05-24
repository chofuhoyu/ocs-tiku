# OCS网课助手之AI自动刷题

使用[OCS](https://docs.ocsjs.com/docs/quickly-start)刷课时有些课程题目较多且没有现成题库，本项目通过调用 DeepSeek API 实现 AI 自动答题，解放劳动力。

## 环境要求

- 安装 [OCS](https://docs.ocsjs.com/docs/quickly-start) 脚本
- Python 3.10+
- DeepSeek API Key（在 [platform.deepseek.com](https://platform.deepseek.com) 获取，余额不少于 10 元即可使用）

## 使用方法

克隆本项目并配置环境

```bash
git clone git@github.com:Guo-Chenxu/ocs-tiku.git
cd ocs-tiku

uv sync
```

配置 DeepSeek API Key，编辑 `.env` 文件，填写你的 API Key 和模型：

```bash
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_MODEL_ID=deepseek-v4-pro
```

启动后端

```bash
python app.py
```

参数：

- `--guess`：虽然有 prompt 限制，但是并不能保证大模型的输出一定是输入的 options 中的一个，开启此参数会判断输出是否合法，如果非法则随机选一个答案（此方法旨在赌正确率大于 60% 以过任务点，仍然可能会存在无法通过任务点需要手动复核的情况，只是降低了概率）
- `--cache`：开启缓存，将每道题结果缓存到本地，下次请求相同题目时直接返回缓存结果，避免重复调用 API（蒙的答案不会缓存）

```bash
# 推荐用法：同时开启 guess 和 cache
python app.py --guess --cache
```

如果一切正常，服务会启动在 9999 端口，接下来在 OCS 中进行配置。

打开 OCS 页面，"通用" -> "全局设置" -> "题库配置"

![](./assets/config.png)

在"题库配置"中添加如下格式的 JSON 配置，保存配置即可。

```json
[
    {
        "name": "TikuAdapter题库",
        "url": "http://127.0.0.1:9999/api/search",
        "homepage": "https://github.com/Guo-Chenxu/ocs-tiku",
        "method": "post",
        "type": "GM_xmlhttpRequest",
        "contentType": "json",
        "headers": {},
        "data": {
            "question": "${title}",
            "type": "${type}",
            "options": {
                "handler": "return (env)=>env.options?.split('\\n').map(s=>s.replace(/\\u00a0/g,' ').trim()).filter(s => s && !/^[A-F]\\.?$/.test(s))"
            }
        },
        "handler": "return (res)=>res.answer.allAnswer.map(i=>([res.question,i.join('#')]))"
    }
]
```

> [!NOTE]
> 如果 OCS 脚本和后端运行在同一台电脑上，直接使用 `http://127.0.0.1:9999/api/search` 即可，无需公网地址。如果 OCS 脚本运行在其他电脑上，需要将 url 改为后端所在机器的局域网 IP（如 `http://192.168.x.x:9999/api/search`）或公网地址。

> [!WARNING]
> 目前仅支持单选和判断两种题型，其他题型能否正常运行为未知状态（多半不行）。

## 模型说明

在 `.env` 文件中通过 `DEEPSEEK_MODEL_ID` 配置模型。推荐使用 `deepseek-v4-pro` 兼顾精度与速度，低延迟场景可用 `deepseek-v4-flash`，高精度场景可用 `deepseek-reasoner`。

## 致谢

- [OCS](https://docs.ocsjs.com/docs/quickly-start)
- [tikuAdapter](https://github.com/DokiDoki1103/tikuAdapter)
