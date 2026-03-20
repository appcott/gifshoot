import tkinter as tk
import threading

class RegionSelector:
    def __init__(self, callback):
        self.callback = callback
        self.root = tk.Tk()
        self.root.attributes("-alpha", 0.5)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2, fill="white", stipple="gray50" # semi transparent appearance
        )

    def on_drag(self, event):
        cur_x, cur_y = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        if self.start_x is None or self.start_y is None:
            return
        
        x0, y0 = min(self.start_x, event.x), min(self.start_y, event.y)
        x1, y1 = max(self.start_x, event.x), max(self.start_y, event.y)
        width, height = x1 - x0, y1 - y0

        if width < 10 or height < 10:
            return
        
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        self.canvas.delete("all")
        self.root.attributes("-alpha", 0.7)
        self.canvas.config(bg="gray10")
        
        self.label = tk.Label(self.root, text="", font=("Helvetica", 120), fg="white", bg="gray10")
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.countdown(3, (x0, y0, width, height))

    def countdown(self, num, region):
        if num > 0:
            self.label.config(text=str(num))
            self.root.after(1000, self.countdown, num - 1, region)
        else:
            self.root.destroy()
            self.callback(region)

    def start(self):
        self.root.mainloop()

def select_region(callback):
    # This must be run in a thread
    def run():
        app = RegionSelector(callback)
        app.start()
    
    t = threading.Thread(target=run, daemon=True)
    t.start()
