#!/usr/bin/env python3
"""Block until the local Unleash Admin API answers (used by make unleash)."""
import sys
import time

import requests

URL = "http://localhost:4242/api/admin/projects"
TOKEN = "*:*.b8f8c6a1d2e34f5a9c7b0d8e1f2a3b4c5d6e7f8a9b0c1d2e"

deadline = time.time() + 120
while time.time() < deadline:
    try:
        if requests.get(URL, headers={"Authorization": TOKEN}, timeout=4).status_code == 200:
            print("Unleash is ready at http://localhost:4242")
            sys.exit(0)
    except requests.RequestException:
        pass
    time.sleep(2)
sys.exit("Unleash did not become ready in time")
