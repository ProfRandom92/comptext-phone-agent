#!/usr/bin/env python3
from comptext_phone_agent.config import load_config
from comptext_phone_agent.doctor import run_doctor
config = load_config()
checks = run_doctor()
assert checks["python"]["ok"]
assert config.dashboard.host in {"127.0.0.1", "localhost", "::1"}
print("installation verification passed")
