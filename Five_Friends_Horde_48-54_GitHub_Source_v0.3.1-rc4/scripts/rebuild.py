#!/usr/bin/env python3
"""Complete, offline and self-contained rc4 rebuild from this ZIP's sources."""
import subprocess
import argparse
import sys
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--skip-lua',action='store_true',help='Explicitly skip Lua 5.4 registration test if library missing')
args=parser.parse_args()
scripts=Path(__file__).resolve().parent
filenames=['build_navigation.py','enrich_navigation.py',
           'validate_navigation.py','validate_regressions.py']
if not args.skip_lua:filenames.append('validate_lua.py')
else:print('WARNING: Lua execution test explicitly SKIPPED; not validated for release.',flush=True)
for filename in filenames:
    print('RUN',filename,flush=True)
    subprocess.run([sys.executable,str(scripts/filename)],check=True,cwd=scripts.parent)
print('PASS source rebuild from bundled route ledger and research snapshots',flush=True)
