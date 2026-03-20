import pystray
from PIL import Image, ImageDraw
import keyboard
import threading
import sys
import os
import webbrowser
import http.server
import functools
from recorder import GIFRecorder
import config
from selector import select_region
from viewer import generate_viewer
from controller import ControllerUI

# ── Local HTTP server so editor.html can fetch GIFs ──
SERVER_PORT = 0  # will be assigned after bind
httpd = None

def start_http_server():
    global httpd, SERVER_PORT
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=config.SAVE_DIR)
    httpd = http.server.HTTPServer(('127.0.0.1', 0), handler)
    SERVER_PORT = httpd.server_address[1]
    print(f"HTTP server running at http://127.0.0.1:{SERVER_PORT}/")
    httpd.serve_forever()

def create_placeholder_icon():
    # Create a simple red square icon for the system tray
    width = 64
    height = 64
    color1 = (255, 0, 0)
    color2 = (255, 255, 255)
    image = Image.new('RGB', (width, height), color2)
    draw = ImageDraw.Draw(image)
    draw.rectangle([width//4, height//4, width*3//4, height*3//4], fill=color1)
    return image

# Initialize Recorder
recorder = GIFRecorder(config.SAVE_DIR)
ui = None  # ControllerUI reference

def _open_gallery_in_browser():
    generate_viewer()
    url = f"http://127.0.0.1:{SERVER_PORT}/index.html"
    webbrowser.open(url)

def _on_auto_stop(filepath):
    """Called from recorder thread when recording finishes and GIF is saved."""
    if ui:
        ui.root.after(0, lambda: ui._set_recording(False))
    if filepath:
        _open_gallery_in_browser()

def on_quit_tray(icon, item):
    recorder.stop()
    icon.stop()
    os._exit(0)

def start_rec():
    recorder.start()

def start_selection_rec(done_callback=None):
    def on_selected(region):
        recorder.start(region)
        if done_callback:
            done_callback()
    select_region(on_selected)

def stop_rec():
    if ui:
        ui.root.after(0, lambda: ui.status_var.set("⏳ 保存中..."))
        ui.root.after(0, lambda: ui.timer_var.set(""))
        ui.root.after(0, lambda: ui.btn_stop.config(state="disabled"))
    recorder.stop()

def open_gallery():
    _open_gallery_in_browser()

def quit_app():
    recorder.stop()
    if httpd:
        httpd.shutdown()
    os._exit(0)

def setup_hotkeys():
    print(f"Hotkeys configured:")
    print(f"  Start Fullscreen: {config.START_RECORDING}")
    print(f"  Start Region:     {config.START_SELECTION}")
    print(f"  Stop:             {config.STOP_RECORDING}")

    keyboard.add_hotkey(config.START_RECORDING, start_rec)
    keyboard.add_hotkey(config.START_SELECTION, start_selection_rec)
    keyboard.add_hotkey(config.STOP_RECORDING, stop_rec)

    keyboard.wait()


def main():
    global ui

    # 1. Start local HTTP server
    ht = threading.Thread(target=start_http_server, daemon=True)
    ht.start()
    import time; time.sleep(0.3)  # wait for port to bind

    # 2. Start hotkey listener
    tm = threading.Thread(target=setup_hotkeys, daemon=True)
    tm.start()

    # 3. Wire recorder callbacks
    recorder.on_auto_stop = _on_auto_stop

    # 4. Launch the controller panel (main thread – tkinter requires it)
    print("GifShoot is running. Controller panel opened.")
    ui = ControllerUI(
        on_fullscreen=start_rec,
        on_region=start_selection_rec,
        on_stop=stop_rec,
        on_gallery=open_gallery,
        on_quit=quit_app,
        recorder=recorder,
    )
    ui.run()

if __name__ == "__main__":
    main()
