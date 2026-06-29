import customtkinter as ctk
from main_feature import create_bar_graph
from bulk_feature import (
    validate_excel_file,
    create_observation_display,
    create_info_panel,
    update_info_panel,
    create_animated_frequency_bar_graph,
    PersistentBulkBarChart,
    FIXED_FRAMEWORKS,
)
from tkinter import filedialog
import os
from datetime import datetime
import threading
from bulk_model import BulkZeoliteModel
from model_selector import get_resource_path, ModelSelector

# -------------------- GLOBAL SETTINGS ----------------
BG_MAIN = "#0f0f0f"
WHITE = "#ffffff"
GRAPH_CONTAINER = "#1B1B1B"
GOOD_COLOR = "#5087ff"   
BAD_COLOR = "#a78bfa"    
GRID_COLOR = "#4A4A4A"

# -------------------- BULK PANEL ----------------
class BulkPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color=BG_MAIN)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_content()

        # Cache: { version_key: bulk_result_dict } — populated on Generate
        self.all_model_results = None
        self._bar_overlay = None

    # ---------------- HEADER ----------------
    def _create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=BG_MAIN)
        header_frame.grid(row=0, column=0, padx=30, pady=(40, 15), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=0)
        header_frame.grid_columnconfigure(2, weight=0)
        header_frame.grid_columnconfigure(3, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="Bulk Synthesis",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, sticky="w")
        
        self.version_badge = ctk.CTkButton(
            header_frame,
            text="ZFY",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2563eb",
            hover_color="#2563eb",
            text_color="white",
            width=60,
            height=24,
            corner_radius=6,
            cursor="arrow"  
        )
        self.version_badge.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.version_badge.grid_remove()
        
        self.zlf_badge = ctk.CTkButton(
            header_frame,
            text="ZLF",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2563eb",
            hover_color="#2563eb", 
            text_color="white",
            width=140,
            height=24,
            corner_radius=6,
            cursor="arrow"  
        )
        self.zlf_badge.grid(row=0, column=2, sticky="w", padx=(5, 0))
        self.zlf_badge.grid_remove()

    # ---------------- CONTENT ----------------
    def _create_content(self):
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, padx=30, pady=(10, 30), sticky="nsew")

        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=8) 
        content_frame.grid_columnconfigure(1, weight=1)

        # ================= DATA CONTAINER (LEFT - WIDE) =================
        self.dataContainer = ctk.CTkFrame(
            content_frame,
            fg_color=BG_MAIN,
            corner_radius=10
        )
        self.dataContainer.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.dataContainer.grid_rowconfigure(0, weight=1)
        self.dataContainer.grid_rowconfigure(1, weight=1)
        self.dataContainer.grid_columnconfigure(0, weight=1)

        # ---------------- BAR CONTAINER ----------------
        self.barContainer = ctk.CTkFrame(
            self.dataContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.barContainer.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._create_bar_graph()

        # ---------------- OUTPUT CONTAINER ----------------
        self.outputContainer = ctk.CTkFrame(
            self.dataContainer,
            fg_color=BG_MAIN,
            corner_radius=10
        )
        self.outputContainer.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.outputContainer.grid_rowconfigure(0, weight=1)
        self.outputContainer.grid_columnconfigure(0, weight=4)
        self.outputContainer.grid_columnconfigure(1, weight=18) 

        # ---------------- OBSERVATION CONTAINER ----------------
        self.observationContainer = ctk.CTkFrame(
            self.outputContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.observationContainer.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        create_observation_display(self.observationContainer, 0, GOOD_COLOR, WHITE)

        # ---------------- BLANK CONTAINER ----------------
        self.blankContainer = ctk.CTkFrame(
            self.outputContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.blankContainer.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        self.info_items_frame = create_info_panel(self.blankContainer, WHITE)
        update_info_panel(self.info_items_frame, white_color=WHITE, good_color=GOOD_COLOR)

        # ================= FILE CONTAINER (RIGHT - NARROW) =================
        self.fileContainer = ctk.CTkFrame(
            content_frame,
            fg_color=BG_MAIN,
            corner_radius=10
        )
        self.fileContainer.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self.fileContainer.grid_rowconfigure(0, weight=0) 
        self.fileContainer.grid_rowconfigure(1, weight=1) 
        self.fileContainer.grid_columnconfigure(0, weight=1)

        # ---------------- BUTTON CONTAINER (TOP) ----------------
        self.buttonContainer = ctk.CTkFrame(
            self.fileContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10,
            height=190 
        )
        self.buttonContainer.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
        self.buttonContainer.grid_propagate(False) 
        self._create_action_buttons()

        # ---------------- UPLOAD CONTAINER (BOTTOM - COMPACT) ----------------
        self.uploadContainer = ctk.CTkFrame(
            self.fileContainer,
            fg_color=BG_MAIN,
            corner_radius=10,
            height=80  
        )
        self.uploadContainer.grid(row=1, column=0, sticky="ew", padx=0, pady=(8, 0))
        self.uploadContainer.grid_propagate(False)

    # ---------------- BAR GRAPH ----------------
    def _create_bar_graph(self):
        # Create the persistent chart once — lives for the panel lifetime.
        self._bar_chart = PersistentBulkBarChart(
            self.barContainer,
            good_color=GOOD_COLOR,
            bg_color=GRAPH_CONTAINER,
            grid_color=GRID_COLOR,
        )

    # ---------------- ACTION BUTTONS ----------------
    def _create_action_buttons(self):
        self.buttonContainer.grid_rowconfigure(0, weight=1)
        self.buttonContainer.grid_rowconfigure(1, weight=1)
        self.buttonContainer.grid_rowconfigure(2, weight=1)
        self.buttonContainer.grid_rowconfigure(3, weight=1)
        self.buttonContainer.grid_columnconfigure(0, weight=1)

        self.import_btn = ctk.CTkButton(
            self.buttonContainer,
            text="Import File",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=GOOD_COLOR,
            hover_color="#437cf6",
            text_color=WHITE,
            height=35,
            corner_radius=8,
            command=self._import_file
        )
        self.import_btn.grid(row=0, column=0, padx=12, pady=(8, 3), sticky="ew")

        self.generate_btn = ctk.CTkButton(
            self.buttonContainer,
            text="Generate",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3a3a3a",
            hover_color="#3a3a3a",
            text_color="#666666",
            height=35,
            corner_radius=8,
            state="disabled",
            command=self._generate
        )
        self.generate_btn.grid(row=1, column=0, padx=12, pady=3, sticky="ew")

        self.download_btn = ctk.CTkButton(
            self.buttonContainer,
            text="Download File",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3a3a3a",
            hover_color="#3a3a3a",
            text_color="#666666",
            height=35,
            corner_radius=8,
            state="disabled",
            command=self._download_file
        )
        self.download_btn.grid(row=2, column=0, padx=12, pady=3, sticky="ew")
        
        self.reset_btn = ctk.CTkButton(
            self.buttonContainer,
            text="Reset",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            text_color=WHITE,
            height=35,
            corner_radius=8,
            command=self._reset_bulk_process
        )
        self.reset_btn.grid(row=3, column=0, padx=12, pady=(3, 8), sticky="ew")

    # ---------------- BUTTON ACTIONS ----------------
    def _import_file(self):
        print("Import File clicked")
        
        files = filedialog.askopenfilenames(
            title="Select Excel Files",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if files:
            print(f"Selected files: {files}")
            file_path = files[0]
            filename = os.path.basename(file_path)
            upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validation_result = validate_excel_file(file_path)
            
            if validation_result["valid"]:
                self._show_upload_message(
                    f"File Uploaded Successfully: {validation_result['observations']} observations found",
                    success=True
                )
                
                self.uploaded_data = validation_result["data"]
                self.observation_count = validation_result["observations"]
                self.uploaded_filename = filename
                self.upload_time = upload_time
                
                for widget in self.observationContainer.winfo_children():
                    widget.destroy()
                create_observation_display(self.observationContainer, validation_result["observations"], GOOD_COLOR, WHITE)
                
                update_info_panel(
                    self.info_items_frame,
                    filename=filename,
                    upload_time=upload_time,
                    status="File uploaded - ready to generate",
                    white_color=WHITE,
                    good_color=GOOD_COLOR
                )
                
                self.generate_btn.configure(
                    state="normal",
                    fg_color=GOOD_COLOR,
                    hover_color="#437cf6",
                    text_color=WHITE
                )
            else:
                self._show_upload_message(
                    f"File Upload Failed: {validation_result['error']}",
                    success=False
                )

                # Clear stale data
                self.uploaded_data     = None
                self.observation_count = 0
                self.uploaded_filename = None
                self.upload_time       = None

                for widget in self.observationContainer.winfo_children():
                    widget.destroy()
                create_observation_display(self.observationContainer, 0, GOOD_COLOR, WHITE)
                update_info_panel(self.info_items_frame, white_color=WHITE, good_color=GOOD_COLOR)

                self.generate_btn.configure(
                    state="disabled",
                    fg_color="#3a3a3a",
                    hover_color="#3a3a3a",
                    text_color="#666666"
                )
    
    def _show_upload_message(self, message, success=True):
        import tkinter as tk
        from PIL import Image, ImageTk, ImageSequence

        def _categorise_error(msg: str):
            ml = msg.lower()
            if "missing columns" in ml or "unexpected columns" in ml:
                return "Column Error", msg
            elif "null" in ml or "nan" in ml or "missing value" in ml:
                return "Null Value Error", msg
            elif "non-numeric" in ml or "special character" in ml or "invalid" in ml:
                return "Invalid Data Error", msg
            elif "no observations" in ml or "zero" in ml:
                return "Empty Data Error", msg
            elif "error reading file" in ml:
                return "File Read Error", msg
            else:
                return "Upload Error", msg

        popup_width  = 350
        popup_height = 230

        popup = ctk.CTkToplevel(self)
        popup.title("Success" if success else "Error")
        popup.resizable(False, False)
        popup.configure(fg_color=BG_MAIN)
        popup.transient(self.master)
        popup.grab_set()
        popup.protocol("WM_DELETE_WINDOW", lambda: None)

        popup.update_idletasks()
        app = self.master.master
        app.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width()  - popup_width)  // 2
        y = app.winfo_rooty() + (app.winfo_height() - popup_height) // 2.8
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        popup.grid_rowconfigure(0, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(popup, fg_color=BG_MAIN, corner_radius=10)
        content.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # ---> THIS IS THE FIX (added get_resource_path wrapper) <---
        gif_path = get_resource_path("icons/success.gif" if success else "icons/error.gif")
        try:
            gif_image = Image.open(gif_path)
            frames = []
            for frame in ImageSequence.Iterator(gif_image):
                frame_resized = frame.copy().convert("RGBA").resize((80, 80), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame_resized))

            gif_label = tk.Label(
                content, bg=BG_MAIN, borderwidth=0, highlightthickness=0
            )
            gif_label.pack(pady=(15, 8))
            current_frame = [0]

            def animate_gif():
                if popup.winfo_exists():
                    gif_label.configure(image=frames[current_frame[0]])
                    current_frame[0] = (current_frame[0] + 1) % len(frames)
                    popup.after(50, animate_gif)

            animate_gif()

        except Exception as e:
            print(f"Could not load notification GIF ({gif_path}): {e}")
            ctk.CTkLabel(
                content,
                text="\u2705" if success else "\u274c",
                font=ctk.CTkFont(size=40),
                text_color=WHITE
            ).pack(pady=(15, 8))

        if success:
            ctk.CTkLabel(
                content,
                text=message,
                font=ctk.CTkFont(size=13),
                text_color=WHITE,
                wraplength=280,
                justify="center"
            ).pack(pady=(0, 8))
        else:
            raw_msg = message.replace("File Upload Failed: ", "").strip()
            category, _ = _categorise_error(raw_msg)
            ctk.CTkLabel(
                content,
                text=category,
                font=ctk.CTkFont(size=13),
                text_color=WHITE,
                wraplength=280,
                justify="center"
            ).pack(pady=(0, 8))

        if success:
            ctk.CTkLabel(
                content,
                text="This window will close automatically.",
                font=ctk.CTkFont(size=12),
                text_color="#FFFFFF"
            ).pack()
            popup.after(3000, lambda: popup.destroy() if popup.winfo_exists() else None)
        else:
            ctk.CTkButton(
                content,
                text="Try Again",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=GOOD_COLOR,
                hover_color="#437cf6",
                text_color=WHITE,
                height=36,
                corner_radius=8,
                command=lambda: popup.destroy() if popup.winfo_exists() else None
            ).pack(fill="x", padx=10, pady=(4, 0))

    def _generate(self):
        if not hasattr(self, 'uploaded_data') or self.uploaded_data is None:
            return

        chemical_cols = ["sival", "alval", "naval", "mag", "h20", "ohval"]
        zero_rows = []
        for idx, row in self.uploaded_data.iterrows():
            if all(float(row.get(col, 0)) == 0.0 for col in chemical_cols):
                zero_rows.append(idx + 1)

        if zero_rows:
            if len(zero_rows) == len(self.uploaded_data):
                self._show_zero_error_popup(
                    "All rows in the file have zero values.\n\n"
                    "Please upload a file with valid non-zero input values."
                )
            else:
                row_list = ", ".join(str(r) for r in zero_rows[:5])
                if len(zero_rows) > 5:
                    row_list += f" … (+{len(zero_rows) - 5} more)"
                self._show_zero_error_popup(
                    f"{len(zero_rows)} row(s) have all-zero values:\n"
                    f"Row(s): {row_list}\n\n"
                    "Please fix the data before generating."
                )
            return

        self._lock_ui_for_processing()
        self._show_processing_popup()

    def _show_zero_error_popup(self, message):
        import tkinter as tk
        from PIL import Image, ImageTk, ImageSequence

        popup_width  = 370
        popup_height = 270

        popup = ctk.CTkToplevel(self)
        popup.title("Invalid Input")
        popup.resizable(False, False)
        popup.configure(fg_color=BG_MAIN)
        popup.transient(self.master)
        popup.grab_set()
        popup.protocol("WM_DELETE_WINDOW", lambda: None)

        popup.update_idletasks()
        try:
            app = self.master.master
        except Exception:
            app = self.master
        app.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width()  - popup_width)  // 2
        y = app.winfo_rooty() + (app.winfo_height() - popup_height) // 2.8
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        popup.grid_rowconfigure(0, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(popup, fg_color=BG_MAIN, corner_radius=10)
        content.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # ---> THIS IS THE FIX (added get_resource_path wrapper) <---
        gif_path = get_resource_path("icons/error.gif")
        try:
            gif_image = Image.open(gif_path)
            frames = []
            for frame in ImageSequence.Iterator(gif_image):
                frames.append(ImageTk.PhotoImage(frame_resized))
                frame_resized = frame.copy().convert("RGBA").resize((70, 70), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame_resized))

            gif_label = tk.Label(content, bg=BG_MAIN, borderwidth=0, highlightthickness=0)
            gif_label.pack(pady=(12, 6))
            current_frame = [0]

            def animate_gif():
                if popup.winfo_exists():
                    gif_label.configure(image=frames[current_frame[0]])
                    current_frame[0] = (current_frame[0] + 1) % len(frames)
                    popup.after(50, animate_gif)

            animate_gif()
        except Exception:
            ctk.CTkLabel(content, text="⚠", font=ctk.CTkFont(size=36),
                         text_color="#ef4444").pack(pady=(12, 6))

        ctk.CTkLabel(
            content,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=WHITE,
            wraplength=300,
            justify="center"
        ).pack(pady=(0, 10))

        ctk.CTkButton(
            content,
            text="OK",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=GOOD_COLOR,
            hover_color="#437cf6",
            text_color=WHITE,
            height=36,
            corner_radius=8,
            command=lambda: popup.destroy() if popup.winfo_exists() else None
        ).pack(fill="x", padx=20, pady=(0, 4))
    
    def _lock_ui_for_processing(self):
        for btn in (self.import_btn, self.generate_btn, self.download_btn, self.reset_btn):
            btn.configure(
                state="disabled",
                fg_color="#3a3a3a",
                hover_color="#3a3a3a",
                text_color="#666666"
            )
        self._bar_overlay = None

    def _remove_bar_overlay(self):
        if self._bar_overlay is not None and self._bar_overlay.winfo_exists():
            self._bar_overlay.destroy()
        self._bar_overlay = None

    def _unlock_ui_after_processing(self, success: bool):
        if success:
            self.import_btn.configure(
                state="disabled", fg_color="#4a4a4a",
                hover_color="#4a4a4a", text_color="#808080"
            )
            self.generate_btn.configure(
                state="disabled", fg_color="#4a4a4a",
                hover_color="#4a4a4a", text_color="#808080"
            )
            self.download_btn.configure(
                state="disabled", fg_color="#3a3a3a",
                hover_color="#3a3a3a", text_color="#666666"
            )
            self.reset_btn.configure(
                state="normal", fg_color="#ef4444",
                hover_color="#dc2626", text_color=WHITE
            )
        else:
            self.import_btn.configure(
                state="normal", fg_color=GOOD_COLOR,
                hover_color="#437cf6", text_color=WHITE
            )
            self.generate_btn.configure(
                state="normal", fg_color=GOOD_COLOR,
                hover_color="#437cf6", text_color=WHITE
            )
            self.download_btn.configure(
                state="disabled", fg_color="#3a3a3a",
                hover_color="#3a3a3a", text_color="#666666"
            )
            self.reset_btn.configure(
                state="normal", fg_color="#ef4444",
                hover_color="#dc2626", text_color=WHITE
            )

    def _enable_download_button(self):
        self.download_btn.configure(
            state="normal", fg_color=GOOD_COLOR,
            hover_color="#437cf6", text_color=WHITE
        )

    def _enable_download_and_reset(self):
        self.download_btn.configure(
            state="normal", fg_color=GOOD_COLOR,
            hover_color="#437cf6", text_color=WHITE
        )
        self.reset_btn.configure(
            state="normal", fg_color="#ef4444",
            hover_color="#dc2626", text_color=WHITE
        )

    def _show_processing_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Processing...")
        popup.resizable(False, False)
        popup.configure(fg_color=BG_MAIN)
        popup.transient(self.master)
        popup.grab_set()

        popup_width  = 350
        popup_height = 250

        popup.update_idletasks()

        app = self.master.master
        app.update_idletasks()
        app_x = app.winfo_rootx()
        app_y = app.winfo_rooty()
        app_w = app.winfo_width()
        app_h = app.winfo_height()

        x = app_x + (app_w - popup_width)  // 2
        y = app_y + (app_h - popup_height) // 2.8

        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        popup.grid_rowconfigure(0, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        content_frame = ctk.CTkFrame(popup, fg_color=BG_MAIN, corner_radius=10)
        content_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        def _on_x_close():
            self.model_complete = True          
            self.bulk_results      = None
            self.all_model_results = None
            popup.destroy()
            self._unlock_ui_after_processing(success=False)
            self._remove_bar_overlay()
            self._reset_bulk_process()

        popup.protocol("WM_DELETE_WINDOW", _on_x_close)
        try:
            import tkinter as tk
            frames = app.gif_frames if hasattr(app, 'gif_frames') and app.gif_frames else None

            if frames:
                gif_label = tk.Label(
                    content_frame, bg=BG_MAIN, borderwidth=0, highlightthickness=0
                )
                gif_label.pack(expand=True, pady=(20, 10))
                current_frame = [0]

                def animate_gif():
                    if popup.winfo_exists():
                        gif_label.configure(image=frames[current_frame[0]])
                        current_frame[0] = (current_frame[0] + 1) % len(frames)
                        popup.after(50, animate_gif)

                animate_gif()
            else:
                raise Exception("Frames not pre-loaded")

        except Exception as e:
            print(f"Using fallback (no GIF): {e}")
            ctk.CTkLabel(
                content_frame,
                text="Loading...",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=WHITE
            ).pack(expand=True, pady=(30, 10))

        status_label = ctk.CTkLabel(
            content_frame, text="Processing...",
            font=ctk.CTkFont(size=12), text_color="#e5e7eb"
        )
        status_label.pack(expand=True, pady=(0, 20))

        progress_bar = ctk.CTkProgressBar(
            content_frame, mode="determinate",
            progress_color=GOOD_COLOR, fg_color="#1a1a1a", height=10
        )
        progress_bar.pack(fill="x", padx=40, pady=(0, 30))
        progress_bar.set(0)

        self._run_bulk_processing(popup, progress_bar, status_label)
        popup.wait_window()

    def _run_bulk_processing(self, popup, progress_bar, status_label):
        self.bulk_results   = None
        self.model_complete = False

        self._progress_value = [0.0]   
        self._status_text    = ["Starting..."]

        def poll_progress():
            if not popup.winfo_exists():
                return
            progress_bar.set(self._progress_value[0])
            status_label.configure(text=self._status_text[0])
            if self.model_complete:
                self._close_processing_popup(popup)
            else:
                popup.after(80, poll_progress)

        def run_model():
            try:
                all_versions = list(ModelSelector.MODEL_CONFIGS.keys())
                n_models     = len(all_versions)

                model = BulkZeoliteModel()

                _action_phrases = [
                    "Processing input data...",
                    "Analyzing chemical parameters...",
                    "Generating predictions...",
                    "Evaluating framework candidates...",
                    "Calibrating confidence scores...",
                    "Finalizing synthesis outputs...",
                ]

                def on_model_done(model_idx, label):
                    completed = model_idx + 1
                    self._progress_value[0] = completed / n_models
                    if completed < n_models:
                        phrase = _action_phrases[completed % len(_action_phrases)]
                        self._status_text[0] = phrase
                    else:
                        self._status_text[0] = "Almost done — wrapping up..."

                all_results = model.process_all_models(
                    self.uploaded_data, n=5, progress_callback=on_model_done
                )
                self.all_model_results = all_results

                active_version = ModelSelector.get_current_version()
                self.bulk_results = all_results.get(active_version) if all_results else None

                self._progress_value[0] = 1.0
                self._status_text[0]    = "All models complete!"
                self.model_complete     = True

            except Exception as e:
                self._status_text[0] = f"Error: {str(e)}"
                self.model_complete  = True

        self._status_text[0] = "Processing input data..."

        threading.Thread(target=run_model, daemon=True).start()
        popup.after(80, poll_progress)
    
    def _close_processing_popup(self, popup):
        popup.destroy()

        if self.bulk_results and self.bulk_results.get("success"):
            from bulk_model import BulkZeoliteModel

            total_obs = self.bulk_results["total_observations"]
            model     = BulkZeoliteModel()
            framework_freq = model.get_framework_frequencies(self.bulk_results)

            for widget in self.observationContainer.winfo_children():
                widget.destroy()
            create_observation_display(self.observationContainer, total_obs, GOOD_COLOR, WHITE)

            self._unlock_ui_after_processing(success=True)

            if framework_freq:
                self._remove_bar_overlay()
                self._bar_chart.animate_to(
                    framework_freq,
                    on_complete=self._enable_download_button,
                )
            else:
                self._remove_bar_overlay()
                self._enable_download_button()

            update_info_panel(
                self.info_items_frame,
                filename=getattr(self, 'uploaded_filename', None),
                upload_time=getattr(self, 'upload_time', None),
                status="Ready to download",
                white_color=WHITE,
                good_color=GOOD_COLOR
            )

        else:
            self._unlock_ui_after_processing(success=False)
            self._remove_bar_overlay()

    def _download_file(self):
        from model_selector import ModelSelector

        active_version = ModelSelector.get_current_version()
        active_label   = ModelSelector.get_display_label()

        results_to_save = None
        if self.all_model_results:
            results_to_save = self.all_model_results.get(active_version)

        if results_to_save is None:
            results_to_save = getattr(self, "bulk_results", None)

        if not results_to_save or not results_to_save.get("success"):
            self._show_upload_message(
                f"No results available for {active_label}. Please Generate first.",
                success=False
            )
            return

        default_name = f"bulk_zeolite_{active_version.lower()}_results.xlsx"
        file_path = filedialog.asksaveasfilename(
            title=f"Save {active_label} Results As",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=default_name
        )

        if file_path:
            model   = BulkZeoliteModel()
            success = model.save_results_to_excel(results_to_save, file_path)
            if success:
                self._show_upload_message(
                    f"Saved {active_label} results successfully", success=True
                )
            else:
                self._show_upload_message("Failed to save file", success=False)

    def switch_to_version(self, version_key: str):
        if not self.all_model_results:
            return  

        result = self.all_model_results.get(version_key)
        if result is None or not result.get("success"):
            return

        from model_selector import ModelSelector
        from bulk_model import BulkZeoliteModel

        lbl = ModelSelector.MODEL_CONFIGS[version_key].get("display_label", version_key)
        self.bulk_results = result

        self.download_btn.configure(
            state="disabled", fg_color="#3a3a3a",
            hover_color="#3a3a3a", text_color="#666666"
        )
        self.reset_btn.configure(
            state="disabled", fg_color="#4a4a4a",
            hover_color="#4a4a4a", text_color="#808080"
        )

        model = BulkZeoliteModel()
        framework_freq = model.get_framework_frequencies(result)
        if framework_freq:
            self._bar_chart.animate_to(
                framework_freq,
                on_complete=self._enable_download_and_reset,
            )
        else:
            self._enable_download_and_reset()

        total_obs = result.get("total_observations", 0)
        for widget in self.observationContainer.winfo_children():
            widget.destroy()
        create_observation_display(self.observationContainer, total_obs, GOOD_COLOR, WHITE)

        update_info_panel(
            self.info_items_frame,
            filename=getattr(self, "uploaded_filename", None),
            upload_time=getattr(self, "upload_time", None),
            status=f"Showing: {lbl} — Ready to download",
            white_color=WHITE,
            good_color=GOOD_COLOR
        )

    def _reset_bulk_process(self):
        self.uploaded_data     = None
        self.observation_count = 0
        self.bulk_results      = None
        self.all_model_results = None
        self.uploaded_filename = None
        self.upload_time       = None
        
        for widget in self.observationContainer.winfo_children():
            widget.destroy()
        create_observation_display(self.observationContainer, 0, GOOD_COLOR, WHITE)
        
        self._bar_chart.animate_to_zero(duration_ms=500)
        
        update_info_panel(self.info_items_frame, white_color=WHITE, good_color=GOOD_COLOR)
        
        self.import_btn.configure(
            state="normal", fg_color=GOOD_COLOR,
            hover_color="#437cf6", text_color=WHITE
        )
        self.generate_btn.configure(
            state="disabled", fg_color="#3a3a3a",
            hover_color="#3a3a3a", text_color="#666666"
        )
        self.download_btn.configure(
            state="disabled", fg_color="#3a3a3a",
            hover_color="#3a3a3a", text_color="#666666"
        )