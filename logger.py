import json
import logging
import sys
from datetime import datetime, timezone

_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process"
}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        for k, v in record.__dict__.items():
            if k not in _RESERVED:
                base[k] = v
        return json.dumps(base, ensure_ascii=False)


def setup_root_json_logging(level: int = logging.INFO) -> None:
    """将 JSON handler 安装到根 logger，使所有子 logger（logging.getLogger 获取）生效。"""
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    root.propagate = False  # 根 logger 不再向上级传播
    logging.captureWarnings(True)


def get_json_logger(name: str = "app", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def init_app_logger(app, level: int = logging.INFO) -> None:
    # 改为初始化根 logger，并让 app/werkzeug 走 propagate
    setup_root_json_logging(level)

    app.logger.handlers.clear()
    app.logger.setLevel(level)
    app.logger.propagate = True

    werk = logging.getLogger("werkzeug")
    werk.handlers.clear()
    werk.setLevel(level)
    werk.propagate = True
