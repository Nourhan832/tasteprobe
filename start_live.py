"""Prompt privately for the existing event key and start a local live server.

No key files, command-line secrets, shell history entries, or credential logging.
"""
import getpass
import os
from pathlib import Path
import shutil
import warnings
import importlib
import threading
import sys
from qloo import Qloo
from server import Server


def watch_and_serve(server):
    """Reload local backend edits without asking the user to re-enter the key.

    Dev-only and bound to loopback. In-flight sessions reset after backend edits.
    """
    root = Path(__file__).resolve().parent
    modules = ("engine", "fixtures", "qloo", "service", "server")
    def versions():
        return tuple((root / (name+".py")).stat().st_mtime_ns for name in modules)
    current = versions()
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        while True:
            threading.Event().wait(1)
            latest = versions()
            if latest == current:
                continue
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
            for name in modules:
                if name in sys.modules:
                    importlib.reload(sys.modules[name])
            server = sys.modules["server"].Server(("127.0.0.1", 8767))
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            current = latest
            print("Backend updated; discovery sessions reset. The key remains in this process only.", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def main():
    runtime = Path(__file__).resolve().parents[2] / "work" / "qloo-runtime" / "node_modules" / "@qloo" / "qloo-harness" / "dist" / "bin.js"
    bundled_node = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node.exe"
    if not os.environ.get("QLOO_HARNESS_ENTRY") and runtime.is_file():
        os.environ["QLOO_HARNESS_ENTRY"] = str(runtime)
    if not os.environ.get("QLOO_NODE"):
        node = shutil.which("node") or (str(bundled_node) if bundled_node.is_file() else None)
        if node:
            os.environ["QLOO_NODE"] = node
    os.environ["QLOO_API_HOST"] = "https://hackathon.api.qloo.com"
    os.environ["QLOO_TRANSPORT"] = "harness"
    print("TasteProbe live setup — official Qloo hackathon server", flush=True)
    print("Enter your existing event key below. Input is hidden and is not saved to a file.", flush=True)
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            key = getpass.getpass("Qloo API key (hidden): ")
        except getpass.GetPassWarning:
            print("This terminal cannot hide input. Run this script in an interactive terminal instead.", flush=True)
            return
    if not key.strip():
        print("No key entered; nothing changed.", flush=True)
        return
    os.environ["QLOO_API_KEY"] = key.strip()
    del key
    server = None
    try:
        # A bounded credential/contract check; no raw diagnostics or credentials printed.
        print("Checking event API access with one entity search…", flush=True)
        payload = Qloo().search("The Matrix", "movie")
        count = len(payload.get("results", []))
        print(f"Live Qloo search succeeded ({count} candidates).", flush=True)
        os.environ["APP_ORIGIN"] = "http://127.0.0.1:8767"
        server = Server(("127.0.0.1", 8767))
        print("TasteProbe live server: http://127.0.0.1:8767", flush=True)
        print("Leave this terminal running. Ctrl+C stops it and discards the in-process key.", flush=True)
        print("Local backend edits reload automatically; sessions reset after an update.", flush=True)
        watch_and_serve(server)
    except KeyboardInterrupt:
        pass
    except (RuntimeError, ValueError) as exc:
        # Adapter errors are curated, fixed messages; never raw subprocess output.
        print(f"Live setup did not complete: {exc}", flush=True)
    except TimeoutError:
        print("Live setup timed out reaching Qloo. Check your network and try again.", flush=True)
    except OSError as exc:
        code = getattr(exc, "winerror", None) or getattr(exc, "errno", None)
        print(f"Local runtime or network error (OS code {code}). Check runtime availability and whether port 8767 is already in use.", flush=True)
    except Exception:
        print("Live setup encountered an unexpected response. No credential was saved or printed.", flush=True)
    finally:
        if server:
            server.server_close()
        os.environ.pop("QLOO_API_KEY", None)


if __name__ == "__main__":
    main()
