from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from typing import Iterator
from urllib import error, request


@contextmanager
def local_llama_server(
    *,
    model: str,
    ctx_size: int = 65536,
    startup_timeout_s: float = 60.0,
) -> Iterator[str]:
    model_path = Path(model).resolve()
    if not model_path.is_file():
        raise ValueError(f"local model not found: {model_path}")
    port = _free_port()
    script = Path(__file__).resolve().parents[1] / "scripts" / "start_llama_server.sh"
    env = dict(os.environ)
    env["PORT"] = str(port)
    env["CTX_SIZE"] = str(ctx_size)
    log = tempfile.TemporaryFile(mode="w+")
    process = subprocess.Popen(
        [str(script), str(model_path)],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_until_ready(process, port, startup_timeout_s, log)
        yield f"http://127.0.0.1:{port}/v1"
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        log.close()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(
    process: subprocess.Popen[str],
    port: int,
    timeout_s: float,
    log: object,
) -> None:
    deadline = time.monotonic() + timeout_s
    health_url = f"http://127.0.0.1:{port}/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        try:
            with request.urlopen(health_url, timeout=1):
                return
        except (error.URLError, TimeoutError):
            time.sleep(0.2)
    log.seek(0)
    detail = str(log.read())[-2000:]
    raise RuntimeError(f"local llama-server did not become ready: {detail}")
