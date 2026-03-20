import mss
import mss.tools
from PIL import Image
import threading
import time
import os
from datetime import datetime

class GIFRecorder:
    def __init__(self, save_dir):
        self.save_dir = save_dir
        self.is_recording = False
        self.frames = []
        self._thread = None
        self.region = None  # (left, top, width, height)
        self.max_duration = 15  # Max 15 seconds
        self.fps = 10
        self.saved_filepath = None
        self._start_time = 0
        self.on_auto_stop = None   # callback when 15s auto-stop fires
        self.on_tick = None        # callback(remaining_sec) each second

    @property
    def elapsed(self):
        if not self.is_recording:
            return 0
        return time.time() - self._start_time

    def start(self, region=None):
        if self.is_recording:
            return
        print("Recording started...")
        self.region = region
        self.saved_filepath = None
        self.is_recording = True
        self.frames = []
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._record, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.is_recording:
            return
        print("Recording scaling down... Handing over to save thread.")
        self.is_recording = False
        # Do not wait for _thread.join() or save here. 
        # The background _record loop will detect is_recording=False and save the GIF without freezing the UI.

    def _record(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            if self.region:
                left, top, width, height = self.region
                monitor = {"left": monitor["left"] + left, "top": monitor["top"] + top,
                           "width": width, "height": height}

            last_tick = -1
            while self.is_recording:
                elapsed = time.time() - self._start_time
                remaining = max(0, self.max_duration - elapsed)

                # Tick callback (once per second)
                sec = int(remaining)
                if sec != last_tick and self.on_tick:
                    last_tick = sec
                    try:
                        self.on_tick(sec)
                    except Exception:
                        pass

                if elapsed >= self.max_duration:
                    print("Max duration (15s) reached. Auto-stopping.")
                    break

                img = sct.grab(monitor)
                frame = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                self.frames.append(frame)
                time.sleep(1.0 / self.fps)

            self.is_recording = False

            # Auto-stop: save immediately and fire callback
            if self.frames and self.saved_filepath is None:
                print("Auto-stop: Saving GIF...")
                self.saved_filepath = self._save()
                if self.on_auto_stop:
                    try:
                        self.on_auto_stop(self.saved_filepath)
                    except Exception as e:
                        print(f"on_auto_stop error: {e}")

    def _save(self):
        import uuid, shutil, subprocess, sys
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.gif"
        filepath = os.path.join(self.save_dir, filename)

        if not self.frames:
            return None

        # Create temporary directory for fast BMP dump
        temp_dir = os.path.join(self.save_dir, f"temp_{uuid.uuid4().hex}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # 1. Dump frames to disk as BMP (very fast, <0.2s for 150 frames)
            # This is fast enough not to freeze Tkinter noticeably.
            for i, f in enumerate(self.frames):
                p = os.path.join(temp_dir, f"{i:04d}.bmp")
                f.save(p)
                self.frames[i] = None # free memory early
        
            # 2. Subprocess script to combine BMP into GIF
            # We use a subprocess so that the heavy GIF quantization (which locks Python's GIL)
            # does not freeze the main Tkinter thread. We also use optimize=False for speed.
            script = f"""
import sys, os
from PIL import Image

output_path = r"{filepath}"
temp_dir = r"{temp_dir}"
fps = {self.fps}

files = sorted([f for f in os.listdir(temp_dir) if f.endswith('.bmp')])
if not files:
    sys.exit(1)

frames = [Image.open(os.path.join(temp_dir, f)) for f in files]
frames[0].save(
    output_path, 
    save_all=True, 
    append_images=frames[1:], 
    optimize=False, 
    duration=int(1000/fps), 
    loop=0
)
"""
            script_path = os.path.join(temp_dir, "build.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)

            # CREATE_NO_WINDOW (0x08000000) prevents the command prompt window from flashing on Windows
            creationflags = 0x08000000 if os.name == 'nt' else 0
            
            print("Encoding GIF in background worker...")
            subprocess.run([sys.executable, script_path], creationflags=creationflags)
            
            if os.path.exists(filepath):
                print(f"GIF saved to: {filepath}")
                return filepath
        except Exception as e:
            print(f"Failed to save GIF via subprocess: {e}")
        finally:
            self.frames = []
            shutil.rmtree(temp_dir, ignore_errors=True)
            
