#!/usr/bin/env python3
from pathlib import Path
import argparse
from comptext_phone_agent.config import load_config
from comptext_phone_agent.storage.exclusions import ExclusionEngine
from comptext_phone_agent.storage.scanner import StorageScanner
from comptext_phone_agent.storage.duplicates import DuplicateDetector
from comptext_phone_agent.reports.markdown import render_markdown
parser=argparse.ArgumentParser()
parser.add_argument('root',nargs='?',default='./mock-phone')
parser.add_argument('output',nargs='?',default='./demo-report.md')
args=parser.parse_args()
root=Path(args.root).resolve(); output=Path(args.output).resolve()
config=load_config(); result=StorageScanner(ExclusionEngine(config.exclusions)).scan(root)
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(render_markdown(result,DuplicateDetector().find(result,verify=True)),encoding='utf-8')
print(output)
