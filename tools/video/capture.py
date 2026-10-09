"""Capture real screenshots of the running Pərdə app with headless Chrome (CDP)."""
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = OUT / "_chrome_profile"

proc = subprocess.Popen([
    CHROME, "--headless=new", "--remote-debugging-port=9333", f"--user-data-dir={PROFILE}",
    "--window-size=1920,1080", "--hide-scrollbars", "--force-dark-mode", "about:blank",
])
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9333/json"))
            page = next(t for t in tabs if t["type"] == "page")
            break
        except Exception:
            time.sleep(0.2)
    ws = connect(page["webSocketDebuggerUrl"], max_size=50_000_000)
    n = 0

    def cmd(method, **params):
        global n
        n += 1
        ws.send(json.dumps({"id": n, "method": method, "params": params}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == n:
                return msg.get("result", {})

    def js(expr):
        return cmd("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)

    def shot(name):
        data = cmd("Page.captureScreenshot", format="png")["data"]
        (OUT / f"{name}.png").write_bytes(base64.b64decode(data))
        print("saved", name)

    cmd("Emulation.setDeviceMetricsOverride", width=1920, height=1080, deviceScaleFactor=1, mobile=False)
    cmd("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "dark"}])
    cmd("Page.enable")
    cmd("Page.navigate", url="http://localhost:8501/")
    time.sleep(8)
    shot("01_start")
    js("[...document.querySelectorAll('button')].find(b => b.innerText.includes('Protect and send')).click()")
    time.sleep(4)
    shot("02_after_send")
    js("window.scrollBy(0, 380)")
    js("document.querySelector('section.main, [data-testid=stMain]')?.scrollBy(0, 380)")
    time.sleep(1)
    shot("03_scrolled")
    js("[...document.querySelectorAll('button[role=tab]')].find(b => b.innerText.includes('Evidence')).click()")
    time.sleep(2)
    js("document.querySelector('[data-testid=stMain]')?.scrollTo(0, 0)")
    time.sleep(1)
    shot("04_evidence")
    ws.close()
finally:
    proc.terminate()
