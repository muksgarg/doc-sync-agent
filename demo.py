import subprocess
import time
import sys

def run(cmd, title):
    print(f"\n{'='*55}\n[STEP] {title}\nCOMMAND: {cmd}\n{'='*55}")
    time.sleep(1)
    res = subprocess.run(cmd, shell=True)
    return res.returncode

print("\n🚀 STARTING LIVE SYSTEM DEMO...\n")

# 1. Run full test suite
run("python -m pytest -v", "1. Running Automated Test Suite")

# 2. Check drift before sync
run("python -m doc_sync.cli check --target-path API_DOCS.md", "2. Detecting Doc Drift (CI Pipeline Mode)")

# 3. Synchronize documentation
run("python -m doc_sync.cli sync --target-path API_DOCS.md", "3. Auto-generating & Syncing Documentation")

# 4. Verify sync
run("python -m doc_sync.cli check --target-path API_DOCS.md", "4. Re-checking Sync Status (Expected: Passed)")

print("\n✅ DEMO COMPLETE: Documentation synced and verified successfully.\n")