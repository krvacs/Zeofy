import customtkinter as ctk
from sidebar import Sidebar
from main import MainPanel
from bulk import BulkPanel
from review import ReviewPanel
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resource path helper (works both dev and PyInstaller)
# ---------------------------------------------------------------------------
def get_resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python execution - use current directory
        base_path = os.path.abspath(".")
    return Path(base_path) / relative_path

# ---------------------------------------------------------------------------

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ZeofyApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Zeofy")
        
        # Wrapped the icon paths with get_resource_path()
        self.app_icon = tk.PhotoImage(file=get_resource_path("icons/logo1.png"))
        self.iconphoto(False, self.app_icon)

        try:
            self.iconbitmap(get_resource_path("icons/logo1.ico"))
        except Exception:
            pass

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        start_width = int(screen_width * 0.8)
        start_height = int(screen_height * 0.8)

        x = (screen_width - start_width) // 2
        y = (screen_height - start_height) // 3

        self.geometry(f"{start_width}x{start_height}+{x}+{y}")
        self.minsize(1000, 600)

        #   Disable maximize button if you want to lock resizing
        # self.resizable(False, False)

        # -------------------------
        # Configure main window background
        # -------------------------
        self.configure(fg_color="#1b1b1b")

        # -------------------------
        # Grid layout with proper weights
        # -------------------------
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=70)
        self.grid_columnconfigure(1, weight=0) 
        self.grid_columnconfigure(2, weight=1)  

        # -------------------------
        # Sidebar
        # -------------------------
        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # -------------------------
        # Vertical separator
        # -------------------------
        self.separator = ctk.CTkFrame(self, width=1, fg_color="#1f2937")
        self.separator.grid(row=0, column=1, sticky="ns")

        # -------------------------
        # Container for panels
        # -------------------------
        self.panel_container = ctk.CTkFrame(self, fg_color="#0f0f0f")
        self.panel_container.grid(row=0, column=2, sticky="nsew")
        self.panel_container.grid_rowconfigure(0, weight=1)
        self.panel_container.grid_columnconfigure(0, weight=1)

        # PRE-LOAD GIF FRAMES - Load once during startup
        print("Pre-loading animation assets...")
        self.gif_frames = self._preload_gif_frames()
        print("Animation assets loaded!")

        # -------------------------
        # Create all panels
        # -------------------------
        print("Creating panels...")
        self.main_panel = MainPanel(self.panel_container)
        self.bulk_panel = BulkPanel(self.panel_container)
        self.review_panel = ReviewPanel(self.panel_container)
        print("Panels created!")
        
        self.current_panel = None
        self.show_panel("synthesize")

        # -------------------------
        # Connect sidebar callbacks
        # -------------------------
        self.sidebar.btn_synthesize.configure(command=lambda: self.show_panel("synthesize"))
        self.sidebar.btn_bulk.configure(command=lambda: self.show_panel("bulk"))
        self.sidebar.btn_review.configure(command=lambda: self.show_panel("review"))
        self.update_idletasks()
        self.bind("<Configure>", self._on_window_configure)
        self._resize_after_id = None

    def _preload_gif_frames(self):
        try:
            # Wrapped the GIF path with get_resource_path()
            gif_path = get_resource_path("icons/loading2.gif")
            gif_image = Image.open(gif_path)
            frames = []
            for frame in ImageSequence.Iterator(gif_image):
                frame_resized = frame.copy().convert("RGBA").resize((120, 120), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame_resized))
            return frames
        except Exception as e:
            print(f"Could not pre-load GIF: {e}")
            return None

    def show_panel(self, panel_name):
        if self.current_panel == panel_name:
            return
        
        self.main_panel.grid_remove()
        self.bulk_panel.grid_remove()
        self.review_panel.grid_remove()
        
        if panel_name == "synthesize":
            self.main_panel.grid(row=0, column=0, sticky="nsew")
            self.sidebar._set_active_button(self.sidebar.btn_synthesize)
        elif panel_name == "bulk":
            self.bulk_panel.grid(row=0, column=0, sticky="nsew")
            self.sidebar._set_active_button(self.sidebar.btn_bulk)
        elif panel_name == "review":
            self.review_panel.grid(row=0, column=0, sticky="nsew")
            self.sidebar._set_active_button(self.sidebar.btn_review)
        
        self.current_panel = panel_name
        self.update_idletasks()

    def _on_window_configure(self, event):
        if event.widget != self:
            return
        # Skip redraws when maximized/minimized
        if self.state() in ("zoomed", "iconic"):
            return
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(16, self._update_after_resize)

    def _update_after_resize(self):
        self._resize_after_id = None
        self.update_idletasks()

if __name__ == "__main__":
    app = ZeofyApp()
    app.mainloop()