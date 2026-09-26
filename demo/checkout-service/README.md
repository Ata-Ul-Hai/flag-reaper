# checkout-service

A small checkout service used as the live target for the Feature Flag Reaper.

It uses **real Unleash** when `UNLEASH_URL` is set (production mode), and falls
back to static flag values for offline tests (`UNLEASH_URL` unset).

```bash
pip install -r requirements.txt
pytest            # runs offline with static flags
UNLEASH_URL=http://localhost:4242 python -m app   # live mode
```
