#!/usr/bin/env python3
from pathlib import Path
import argparse
from comptext_phone_agent.mocks.filesystem import create_mock_phone
parser = argparse.ArgumentParser()
parser.add_argument("path", nargs="?", default="./mock-phone")
args = parser.parse_args()
print(create_mock_phone(Path(args.path).resolve()))
