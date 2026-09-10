"""DeepSeek LLM 客户端。

保密约定：
- API Key 仅从环境变量 / .env 读取，不接受参数传入。
- 本文件不打印 Key；出错时也只展示非敏感信息。
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# 加载 .env（不依赖 python-dotenv，自己简单解析）
def _load_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

_load_env()


class LLMError(RuntimeError):
    pass


class DeepSeekClient:
    """DeepSeek 客户端（OpenAI 兼容协议，支持 Function Calling）。"""

    def __init__(self) -> None:
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.enabled = bool(self.api_key) and self.api_key != "your-key-here"
        if not self.enabled:
            print("[llm] DEEPSEEK_API_KEY 未设置或为占位值，LLM 旁白降级为占位文本。")

    # ---------- 公共方法 ----------
    def game_master_call(
        self,
        system: str,
        user_message: str,
        tools: List[Dict[str, Any]],
        timeout: float = 15.0,
    ) -> Optional[Dict[str, Any]]:
        """调用 game_master 工具，返回解析后的 args dict。失败/未启用时返回 None。"""
        if not self.enabled:
            return None
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "tools": tools,
            "tool_choice": {"type": "function", "function": {"name": "game_master"}},
            "temperature": 0.7,
            "max_tokens": 400,
        }
        url = self.base_url.rstrip("/") + "/v1/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            print(f"[llm] HTTP {e.code}: {body}")
            raise LLMError(f"DeepSeek 返回 {e.code}") from e
        except urllib.error.URLError as e:
            print(f"[llm] 网络错误: {e.reason}")
            raise LLMError(f"无法连接 DeepSeek: {e.reason}") from e
        except (TimeoutError, OSError) as e:
            print(f"[llm] 超时: {e}")
            raise LLMError("DeepSeek 调用超时") from e

        try:
            msg = data["choices"][0]["message"]
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                # 没调工具但返回了内容 → 视作旁白
                return {"narration": msg.get("content") or "", "clues": [], "unlocked_objects": [], "flags": {}}
            args_raw = tool_calls[0]["function"]["arguments"]
            return json.loads(args_raw)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"[llm] 响应解析失败: {e}; 原始: {data}")
            return None


# 单例
_client: Optional[DeepSeekClient] = None


def get_client() -> DeepSeekClient:
    global _client
    if _client is None:
        _client = DeepSeekClient()
    return _client