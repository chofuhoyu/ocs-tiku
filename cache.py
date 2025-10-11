import sqlite3
import threading
import atexit
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DB = None
_DB_LOCK = threading.Lock()
_DB_PATH = Path(__file__).with_name("qa_cache.sqlite3")


def cache_db_path() -> Path:
    return _DB_PATH.resolve()


def _close_db():
    global _DB
    with _DB_LOCK:
        if _DB is not None:
            try:
                _DB.commit()
                _DB.close()
                logger.info(f"Closed SQLite cache at: {cache_db_path()}")
            except Exception as e:
                logger.warning(f"Failed to close SQLite cache: {e}")
            finally:
                _DB = None


def ensure_cache_db():
    global _DB
    with _DB_LOCK:
        if _DB is None:
            try:
                # 连接即会在本地创建 SQLite 文件
                _DB = sqlite3.connect(_DB_PATH, check_same_thread=False)
                _DB.execute("PRAGMA journal_mode=WAL;")
                _DB.execute("PRAGMA synchronous=NORMAL;")
                _DB.execute(
                    "CREATE TABLE IF NOT EXISTS qa_cache ("
                    "  k TEXT PRIMARY KEY,"
                    "  v TEXT"
                    ")"
                )
                _DB.commit()
                atexit.register(_close_db)
                logger.info(f"Initialized SQLite cache at: {cache_db_path()}")
            except Exception as e:
                logger.warning(f"Failed to init SQLite cache: {e}")


def cache_get(k: str):
    ensure_cache_db()
    with _DB_LOCK:
        try:
            cur = _DB.execute("SELECT v FROM qa_cache WHERE k = ?", (k,))
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None


def cache_set(k: str, v: str):
    ensure_cache_db()
    with _DB_LOCK:
        try:
            _DB.execute(
                "INSERT OR REPLACE INTO qa_cache(k, v) VALUES(?, ?)", (k, v))
            _DB.commit()
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
