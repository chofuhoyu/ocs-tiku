import json
import logging
import re

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class _StripAnsiFilter(logging.Filter):
    def filter(self, record):
        record.msg = _ANSI_RE.sub("", str(record.msg))
        return True


def setup_logging(level: int = logging.INFO) -> None:
    """配置根 logger，使用 RichHandler 输出彩色日志。"""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )


def init_app_logger(app, level: int = logging.INFO) -> None:
    setup_logging(level)

    app.logger.handlers.clear()
    app.logger.setLevel(level)
    app.logger.propagate = True

    werk = logging.getLogger("werkzeug")
    werk.handlers.clear()
    werk.setLevel(level)
    werk.propagate = True
    werk.addFilter(_StripAnsiFilter())


def log_http(method: str, path: str, status: int, duration_ms: float,
             req_body: str | None = None, resp_body: str | None = None,
             cached: bool = False, guessed: bool = False) -> None:
    """渲染 HTTP 请求/响应日志。"""

    if status < 300:
        status_color = "green"
    elif status < 400:
        status_color = "yellow"
    else:
        status_color = "red"

    if duration_ms < 500:
        time_color = "green"
    elif duration_ms < 2000:
        time_color = "yellow"
    else:
        time_color = "red"

    tags = []
    if cached:
        tags.append((" CACHE ", "bold white on green"))
    if guessed:
        tags.append((" GUESS ", "bold white on red"))

    title = Text.assemble(
        (method, "bold"),
        " ",
        (path, "cyan"),
        " ",
        (str(status), f"bold {status_color}"),
        " ",
        (f"{duration_ms}ms", time_color),
        *[(text, style) for text, style in tags],
    )

    # 解析请求体和响应体
    req_data = None
    if req_body:
        try:
            req_data = json.loads(req_body)
        except (json.JSONDecodeError, TypeError):
            pass

    resp_data = None
    if resp_body:
        try:
            resp_data = json.loads(resp_body) if isinstance(resp_body, str) else resp_body
        except (json.JSONDecodeError, TypeError):
            pass

    table = Table(show_header=False, box=None, padding=(0, 1), expand=False)
    table.add_column("key", style="bold cyan", width=10)
    table.add_column("value", max_width=100)

    question = (req_data or {}).get("question") or (resp_data or {}).get("question", "")
    qtype = (req_data or {}).get("type", "")
    raw_options = (req_data or {}).get("options") or []
    resp_options = (resp_data or {}).get("options") or []
    # 用响应中的 options 显示（已归一化），与请求的 raw 对比
    options = resp_options or raw_options
    answers = []
    if resp_data:
        answers = (resp_data.get("answer") or {}).get("allAnswer", [[]])[0]

    if question:
        table.add_row("question", question)
    if qtype:
        table.add_row("type", qtype)
    if options:
        lines = []
        for i, o in enumerate(options):
            marker = "✓" if answers and o in answers else " "
            note = ""
            if raw_options and i < len(raw_options) and raw_options[i] != o:
                note = " [dim](normalized)[/dim]"
            lines.append(f"[{marker}] {i + 1}. {o}{note}")
        table.add_row("options", "\n".join(lines))
    if answers:
        table.add_row("answer", Text(" # ".join(answers), style="bold green"))

    if table.rows:
        console.print(Panel(table, title=title, title_align="left", border_style="grey50"))
    else:
        console.print(f"  {title}")
