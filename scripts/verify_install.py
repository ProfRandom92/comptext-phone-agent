#!/usr/bin/env python3
from comptext_phone_agent.config import load_config
from comptext_phone_agent.doctor import run_doctor
config = load_config()
checks = run_doctor()
if not checks["python"]["ok"]:
    raise SystemExit("installation verification failed: unsupported Python")
if config.dashboard.host not in {"127.0.0.1", "localhost", "::1"}:
    raise SystemExit("installation verification failed: dashboard is not loopback")
print("installation verification passed")
