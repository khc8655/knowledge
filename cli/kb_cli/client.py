"""HTTP client for kb-platform API."""
import json
import sys
import time
from typing import Any, Generator

import httpx

from kb_cli.config import load_config


class KbClient:
    """HTTP client wrapping kb-platform REST API."""

    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        config = load_config()
        self.base_url = (base_url or config["api_base_url"]).rstrip("/")
        self.timeout = timeout or config["timeout"]
        self._client = httpx.Client(
            base_url=f"{self.base_url}/api/v1",
            timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )

    def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        """GET request, return parsed JSON."""
        start = time.monotonic()
        try:
            resp = self._client.get(path, params=params)
            elapsed = int((time.monotonic() - start) * 1000)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json(), "meta": {"elapsed_ms": elapsed}}
        except httpx.ConnectError:
            return self._error("CONNECTION_REFUSED",
                               f"Cannot connect to kb-platform at {self.base_url}",
                               "Is the backend running? Start with: cd /home/jjb/kb-platform/backend && python main.py")
        except httpx.TimeoutException:
            return self._error("TIMEOUT", f"Request timed out after {self.timeout}s",
                               "Try increasing --timeout")
        except httpx.HTTPStatusError as e:
            return self._error(self._status_code(e.response.status_code),
                               self._extract_detail(e.response),
                               f"HTTP {e.response.status_code}")
        except Exception as e:
            return self._error("UNKNOWN", str(e))

    def post(self, path: str, json_data: dict | None = None, timeout: int | None = None) -> dict[str, Any]:
        """POST request, return parsed JSON."""
        start = time.monotonic()
        try:
            resp = self._client.post(path, json=json_data, timeout=timeout or self.timeout)
            elapsed = int((time.monotonic() - start) * 1000)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json(), "meta": {"elapsed_ms": elapsed}}
        except httpx.ConnectError:
            return self._error("CONNECTION_REFUSED",
                               f"Cannot connect to kb-platform at {self.base_url}",
                               "Is the backend running? Start with: cd /home/jjb/kb-platform/backend && python main.py")
        except httpx.TimeoutException:
            return self._error("TIMEOUT", f"Request timed out after {timeout or self.timeout}s",
                               "Try increasing --timeout")
        except httpx.HTTPStatusError as e:
            return self._error(self._status_code(e.response.status_code),
                               self._extract_detail(e.response),
                               f"HTTP {e.response.status_code}")
        except Exception as e:
            return self._error("UNKNOWN", str(e))

    def put(self, path: str, json_data: dict | None = None) -> dict[str, Any]:
        """PUT request, return parsed JSON."""
        start = time.monotonic()
        try:
            resp = self._client.put(path, json=json_data)
            elapsed = int((time.monotonic() - start) * 1000)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json(), "meta": {"elapsed_ms": elapsed}}
        except httpx.ConnectError:
            return self._error("CONNECTION_REFUSED",
                               f"Cannot connect to kb-platform at {self.base_url}",
                               "Is the backend running?")
        except httpx.TimeoutException:
            return self._error("TIMEOUT", f"Request timed out after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            return self._error(self._status_code(e.response.status_code),
                               self._extract_detail(e.response))
        except Exception as e:
            return self._error("UNKNOWN", str(e))

    def delete(self, path: str) -> dict[str, Any]:
        """DELETE request, return parsed JSON."""
        start = time.monotonic()
        try:
            resp = self._client.delete(path)
            elapsed = int((time.monotonic() - start) * 1000)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json(), "meta": {"elapsed_ms": elapsed}}
        except httpx.ConnectError:
            return self._error("CONNECTION_REFUSED",
                               f"Cannot connect to kb-platform at {self.base_url}")
        except httpx.HTTPStatusError as e:
            return self._error(self._status_code(e.response.status_code),
                               self._extract_detail(e.response))
        except Exception as e:
            return self._error("UNKNOWN", str(e))

    def post_stream(self, path: str, json_data: dict | None = None,
                    timeout: int | None = None) -> Generator[tuple[str, Any], None, None]:
        """POST request with SSE streaming. Yields (event_type, data) tuples."""
        try:
            with self._client.stream("POST", path, json=json_data,
                                     timeout=timeout or 120,
                                     headers={"Accept": "text/event-stream"}) as resp:
                resp.raise_for_status()
                event_type = None
                for line in resp.iter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            data = data_str
                        yield event_type or "message", data
                        event_type = None
        except httpx.ConnectError:
            yield "error", {"code": "CONNECTION_REFUSED",
                            "message": f"Cannot connect to kb-platform at {self.base_url}"}
        except httpx.TimeoutException:
            yield "error", {"code": "TIMEOUT",
                            "message": f"Request timed out after {timeout or 120}s"}
        except httpx.HTTPStatusError as e:
            yield "error", {"code": self._status_code(e.response.status_code),
                            "message": self._extract_detail(e.response)}
        except Exception as e:
            yield "error", {"code": "UNKNOWN", "message": str(e)}

    def upload(self, path: str, file_path: str, **kwargs) -> dict[str, Any]:
        """Upload a file via multipart/form-data."""
        start = time.monotonic()
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path, f)}
                data = {k: v for k, v in kwargs.items() if v is not None}
                # Use a separate client without Content-Type header for multipart
                resp = httpx.Client(base_url=f"{self.base_url}/api/v1", timeout=60).post(
                    path, files=files, data=data
                )
            elapsed = int((time.monotonic() - start) * 1000)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json(), "meta": {"elapsed_ms": elapsed}}
        except httpx.ConnectError:
            return self._error("CONNECTION_REFUSED",
                               f"Cannot connect to kb-platform at {self.base_url}")
        except httpx.HTTPStatusError as e:
            return self._error(self._status_code(e.response.status_code),
                               self._extract_detail(e.response))
        except Exception as e:
            return self._error("UNKNOWN", str(e))

    @staticmethod
    def _error(code: str, message: str, hint: str | None = None) -> dict[str, Any]:
        err = {"code": code, "message": message}
        if hint:
            err["hint"] = hint
        return {"ok": False, "error": err}

    @staticmethod
    def _status_code(status: int) -> str:
        mapping = {400: "BAD_REQUEST", 404: "NOT_FOUND", 500: "SERVER_ERROR"}
        return mapping.get(status, f"HTTP_{status}")

    @staticmethod
    def _extract_detail(resp: httpx.Response) -> str:
        try:
            data = resp.json()
            return data.get("detail", resp.text)
        except Exception:
            return resp.text or f"HTTP {resp.status_code}"
