import os
from pathlib import Path

# Hotkeys (compatible with the 'keyboard' library)
START_RECORDING = "ctrl+shift+r"
STOP_RECORDING = "ctrl+shift+s"
START_SELECTION = "ctrl+alt+g"

# Save directory: gifshoot/shots/
SAVE_DIR = Path(__file__).parent / "shots"

# Ensure the save directory exists
try:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Error creating save directory: {e}")
    SAVE_DIR = Path.cwd()  # Fallback to current directory

SAVE_DIR = str(SAVE_DIR)  # Keep as str for compatibility with os.path usage elsewhere
