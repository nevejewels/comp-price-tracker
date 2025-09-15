# resume_helper.py
import os

PROGRESS_FILE = "progress.txt"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return int(f.read().strip()) + 1
        except:
            pass
    return 0

def save_progress(idx):
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(idx))
    print(f"📝 Progress saved at row {idx}")
