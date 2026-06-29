import customtkinter as ctk
from main_feature import (
    create_bar_graph,
    create_animated_bar_graph,
    create_circular_confidence,
    create_animated_circular_confidence,
    create_condition_inputs,
    create_weight_container,
    PersistentBarChart,
    PersistentCircularChart,
    FIXED_FRAMEWORKS,
)
from main_model import ZeoliteModel
import threading

from model_selector import get_resource_path

# -------------------- GLOBAL SETTINGS ----------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BG_MAIN = "#0f0f0f"
WHITE = "#ffffff"
LIGHT_GREY = "#e5e7eb"
GRAPH_CONTAINER = "#1B1B1B"
GRID_COLOR = "#4A4A4A"
GOOD_COLOR = "#5087ff"   
BAD_COLOR = "#a78bfa"    
PROGRESS_BG_COLOR = GRAPH_CONTAINER  
PARAM_COLOR = "#848484"
SCROLLBAR_COLOR = "#3a3a3a"  
SCROLLBAR_HOVER_COLOR = "#4a4a4a"  

# -------------------- MAIN APP ----------------
class ZeofyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Zeofy")
        self.geometry("1400x800")
        self.minsize(1100, 650)

        self.configure(fg_color=BG_MAIN, bg_color=BG_MAIN)

        self.grid_rowconfigure(0, weight=1)

        # Sidebar column (fixed width)
        self.grid_columnconfigure(0, weight=0, minsize=60)

        # Main panel column (expands)
        self.grid_columnconfigure(1, weight=1)

        # ---------------- CREATE SIDEBAR ----------------
        from sidebar import Sidebar   # if in separate file
        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # ---------------- CREATE MAIN PANEL ----------------
        self.main_panel = MainPanel(self)
        self.main_panel.grid(row=0, column=1, sticky="nsew")




# -------------------- MAIN PANEL ----------------
class MainPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color=BG_MAIN)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Create model instance — files are loaded lazily on first prediction
        from model_selector import ModelSelector
        print("\n" + "=" * 60)
        print("  MODEL INSTANCE CREATED (lazy load)")
        print("=" * 60)
        print(f"  Default version : {ModelSelector.get_current_version()}")
        print(f"  Files will load on first Generate click.")
        print("=" * 60)
        self.model = ZeoliteModel()
        print(f"  ✓ Model instance ready\n")

        # Cache: { version_key: result_dict } — populated on first Generate
        self.all_model_results = None

        self._create_header()
        self._create_content()

    # ---------------- HEADER ----------------
    def _create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=BG_MAIN)
        header_frame.grid(row=0, column=0, padx=30, pady=(40, 15), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=0)
        header_frame.grid_columnconfigure(2, weight=0)
        header_frame.grid_columnconfigure(3, weight=1)

        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="Synthesize Zeolite",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Version badge button (small, non-clickable, blue, white text)
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
        # Hidden by default - will be shown/hidden by sidebar checkbox
        self.version_badge.grid_remove()
        
        # ZLF badge button — wider to fit sub-model names like "ZLF · Random Forest"
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
        # Hidden by default - will be shown/hidden by sidebar checkbox
        self.zlf_badge.grid_remove()

    # ---------------- CONTENT ----------------
    def _create_content(self):
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, padx=30, pady=(10, 30), sticky="nsew")

        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=8)
        content_frame.grid_columnconfigure(1, weight=1)

        # ================= LEFT CONTAINER =================
        self.leftContainer = ctk.CTkFrame(
            content_frame,
            fg_color=BG_MAIN,
            corner_radius=10
        )
        self.leftContainer.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.leftContainer.grid_rowconfigure(0, weight=1)
        self.leftContainer.grid_rowconfigure(1, weight=1)
        self.leftContainer.grid_columnconfigure(0, weight=1)

        # ---------------- GRAPH CONTAINER ----------------
        self.graphContainer = ctk.CTkFrame(
            self.leftContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.graphContainer.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        
        # Configure grid for responsive content
        self.graphContainer.grid_rowconfigure(0, weight=1)
        self.graphContainer.grid_columnconfigure(0, weight=1)
        
        self._create_bar_graph()

        # ---------------- OUTPUT CONTAINER ----------------
        self.outputContainer = ctk.CTkFrame(
            self.leftContainer,
            fg_color=BG_MAIN,
            corner_radius=10
        )
        self.outputContainer.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.outputContainer.grid_rowconfigure(0, weight=1)
        self.outputContainer.grid_columnconfigure(0, weight=1)
        self.outputContainer.grid_columnconfigure(1, weight=20)

        # ---------------- CONFIDENCE CONTAINER ----------------
        self.confidenceContainer = ctk.CTkFrame(
            self.outputContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.confidenceContainer.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=0)
        
        # Configure grid for responsive content
        self.confidenceContainer.grid_rowconfigure(0, weight=1)
        self.confidenceContainer.grid_columnconfigure(0, weight=1)
        
        # Create persistent circular chart once
        self._circ_chart = PersistentCircularChart(
            self.confidenceContainer,
            good_color=GOOD_COLOR,
            bad_color=BAD_COLOR,
            bg_color=PROGRESS_BG_COLOR,
            white_color=WHITE,
        )
        self._create_circular_confidence(0, "Unknown")

        # ---------------- WEIGHT CONTAINER ----------------
        self.weightContainer = ctk.CTkFrame(
            self.outputContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.weightContainer.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=0)
        
        # Configure grid for responsive content
        self.weightContainer.grid_rowconfigure(0, weight=1)
        self.weightContainer.grid_columnconfigure(0, weight=1)
        
        self._create_weight_container()

        # ================= RIGHT CONTAINER =================
        self.rightContainer = ctk.CTkFrame(
            content_frame,
            fg_color=BG_MAIN,
            corner_radius=12
        )
        self.rightContainer.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        # ---------------- RIGHT CONTAINER INTERNAL ROWS ----------------
        self.rightContainer.grid_rowconfigure(0, weight=25)  
        self.rightContainer.grid_rowconfigure(1, weight=1) 
        self.rightContainer.grid_columnconfigure(0, weight=1)

        # ---------------- CONDITION CONTAINER ----------------
        self.conditionContainer = ctk.CTkFrame(
            self.rightContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.conditionContainer.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 8))
        
        # Configure grid for responsive content
        self.conditionContainer.grid_rowconfigure(0, weight=1)
        self.conditionContainer.grid_columnconfigure(0, weight=1)
        
        self._create_condition_inputs()

        # ---------------- GENERATE CONTAINER ----------------
        self.generateContainer = ctk.CTkFrame(
            self.rightContainer,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.generateContainer.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8,0))
        
        # Configure grid for responsive content
        self.generateContainer.grid_rowconfigure(0, weight=1)
        self.generateContainer.grid_rowconfigure(1, weight=1)
        self.generateContainer.grid_columnconfigure(0, weight=1)

        # Generate button (initially disabled)
        self.generate_btn = ctk.CTkButton(
            self.generateContainer,
            text="Generate",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#666666",
            fg_color="#3a3a3a",
            hover_color="#3a3a3a",
            height=35,
            state="disabled",
            command=self.generate_action
        )
        self.generate_btn.pack(padx=15, pady=(15, 6), fill="x")

        # Reset button (initially disabled — only active after Generate completes)
        self.reset_btn = ctk.CTkButton(
            self.generateContainer,
            text="Reset",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#666666",
            fg_color="#3a3a3a",
            hover_color="#3a3a3a",
            height=35,
            state="disabled",
            command=self._reset_action
        )
        self.reset_btn.pack(padx=15, pady=(0, 15), fill="x")
        
        # Now that buttons exist, do initial validation
        self._validate_inputs()

    # ---------------- BAR GRAPH ----------------
    def _create_bar_graph(self):
        # Create the persistent chart once — it will live for the panel lifetime.
        self._bar_chart = PersistentBarChart(
            self.graphContainer,
            threshold=50,
            good_color=GOOD_COLOR,
            bad_color=BAD_COLOR,
            bg_color=GRAPH_CONTAINER,
            grid_color=GRID_COLOR,
        )

    # ---------------- CIRCULAR CONFIDENCE ----------------
    def _create_circular_confidence(self, percentage, zeolite_text):
        # Delegate to the persistent widget
        self._circ_chart.animate_to(percentage, zeolite_text, duration_ms=0)

    def _create_animated_circular_confidence(self, percentage, zeolite_text, on_complete=None):
        self._circ_chart.animate_to(
            percentage,
            zeolite_text,
            on_complete=on_complete,
        )

    # ---------------- CONDITION INPUT FIELDS ----------------
    def _create_condition_inputs(self):
        result = create_condition_inputs(
            self.conditionContainer,
            PARAM_COLOR,
            WHITE,
            SCROLLBAR_COLOR,
            SCROLLBAR_HOVER_COLOR
        )
        self.param_entries = result['entries']
        self.scroll_frame = result['scroll_frame']
        
        # Bind focus events to auto-scroll
        for i, entry in enumerate(self.param_entries):
            entry.bind("<FocusIn>", lambda e, idx=i: self._scroll_to_entry(idx))
            # Bind key release to validate inputs
            entry.bind("<KeyRelease>", lambda e: self._validate_inputs())

    def _scroll_to_entry(self, index):
        # Calculate the position of the entry
        total_entries = len(self.param_entries)
        scroll_position = index / (total_entries - 1) if total_entries > 1 else 0
        
        # Scroll to the entry position
        self.scroll_frame._parent_canvas.yview_moveto(scroll_position)
    
    def _validate_inputs(self):
        all_filled = True
        
        for entry in self.param_entries:
            val = entry.get().strip()
            # Check if empty or still has placeholder
            if val == "" or val == "Enter a value":
                all_filled = False
                break
        
        # Update button state
        if all_filled:
            self.generate_btn.configure(
                state="normal",
                fg_color="#2563eb",
                hover_color="#437cf6",
                text_color=WHITE
            )
        else:
            self.generate_btn.configure(
                state="disabled",
                fg_color="#3a3a3a",
                hover_color="#3a3a3a",
                text_color="#666666"
            )

    # ---------------- WEIGHT CONTAINER ----------------
    def _create_weight_container(self):
        create_weight_container(
            self.weightContainer,
            WHITE,
            LIGHT_GREY,
            SCROLLBAR_COLOR,
            SCROLLBAR_HOVER_COLOR
        )
    
    # ---------------- CALCULATE CHEMICAL OUTPUTS ----------------
    def _calculate_chemical_outputs(self, param_data):
        
        try:
            # Extract parameters
            sival = param_data.get("sival", 0.0)
            alval = param_data.get("alval", 0.0)
            naval = param_data.get("naval", 0.0)
            mag   = param_data.get("mag",   0.0)
            h20   = param_data.get("h20",   0.0)
            ohval = param_data.get("ohval", 0.0)
            gMK   = param_data.get("metakaolin", 0.0)

            # mol_total matches _build_feature_vector — all 6 chemical inputs
            mol_total = sival + alval + naval + mag + h20 + ohval

            print("\n" + "="*60)
            print("CALCULATING AMOUNT")
            print("="*60)
            print(f"mol_total = {sival} + {alval} + {naval} + {mag} + {h20} + {ohval} = {mol_total}")

            # Avoid division by zero
            if mol_total == 0:
                print("Warning: mol_total is 0, using default values")
                return {
                    "Metakaolin": gMK,
                    "RHA": 0.0,
                    "Al203": 0.0,
                    "Sodium Silicate": 0.0,
                    "NaOH": 0.0,
                    "Water": 0.0
                }

            # Normalized fractions — identical to _build_feature_vector
            G = sival / mol_total   # sival_n
            H = alval / mol_total   # alval_n
            I = h20   / mol_total   # h20_n
            J = naval / mol_total   # naval_n
            K = ohval / mol_total   # ohval_n

            print(f"G (sival_n) = {G:.6f}")
            print(f"H (alval_n) = {H:.6f}")
            print(f"I (h20_n)   = {I:.6f}")
            print(f"J (naval_n) = {J:.6f}")
            print(f"K (ohval_n) = {K:.6f}")

            # Calculate gSS first (needed for other calculations)
            gSS = (J - K) / 2 * 61.98 * 100 / 10.95
            print(f"\ngSS = ({J} - {K}) / 2 * 61.98 * 100 / 10.95 = {gSS:.6f}")

            # Calculate gRHA
            gRHA = (G - (gMK) * (0.54/60.08) - (gSS) * (0.3308/60.08)) * (100/39.6) * 28.09
            print(f"gRHA = ({G} - {gMK} * (0.54/60.08) - {gSS} * (0.3308/60.08)) * (100/39.6) * 28.09 = {gRHA:.6f}")

            # Calculate gNaOH
            gNaOH = K * 40
            print(f"gNaOH = {K} * 40 = {gNaOH:.6f}")

            # Calculate gWater
            gWater = (I - (gSS) * 55.97/100/18.015) * 18.015
            print(f"gWater = ({I} - {gSS} * 55.97/100/18.015) * 18.015 = {gWater:.6f}")

            # Calculate gAO (Al203)
            gAO = ((H/2) - (gMK) * (0.43/101.96) - (gRHA) * (0.579/100) / 226.98 / 2) * 101.96
            print(f"gAO = (({H}/2) - {gMK} * (0.43/101.96) - {gRHA} * (0.579/100) / 226.98 / 2) * 101.96 = {gAO:.6f}")
            
            print("="*60 + "\n")
            
            # Return chemical outputs
            outputs = {
                "Metakaolin": gMK,
                "RHA": gRHA,
                "Al203": gAO,
                "Sodium Silicate": gSS,
                "NaOH": gNaOH,
                "Water": gWater
            }
            
            print("Final Amount:")
            for chemical, value in outputs.items():
                print(f"  {chemical}: {value:.4f}")
            print()
            
            return outputs
            
        except Exception as e:
            print(f"Error calculating Amounts: {e}")
            import traceback
            traceback.print_exc()
            return {
                "Metakaolin": 0.0,
                "RHA": 0.0,
                "Al203": 0.0,
                "Sodium Silicate": 0.0,
                "NaOH": 0.0,
                "Water": 0.0
            }

    # ---------------- BUTTON ACTIONS ----------------
    def generate_action(self):
        var_names = ["sival", "alval", "naval", "h20", "mag", "ohval", "time", "temper", "metakaolin"]
        
        param_data = {}
        for i, entry in enumerate(self.param_entries):
            val = entry.get().strip()
            if val == "" or val == "Enter a value":
                param_data[var_names[i]] = 0.0
            else:
                try:
                    param_data[var_names[i]] = float(val)
                except ValueError:
                    print(f"Warning: Could not convert '{val}' to number for {var_names[i]}, using 0.0")
                    param_data[var_names[i]] = 0.0
        
        print("Generate clicked!")
        print("Parameter data (in-memory):")
        for k, v in param_data.items():
            print(f"  {k}: {v} (type: {type(v).__name__})")

        # ── Zero-input guard ─────────────────────────────────────────────
        # Check only the 6 chemical composition inputs — time and temper can
        # legitimately be the only non-zero fields but predictions require
        # at least one chemical input to be non-zero.
        chemical_keys = ["sival", "alval", "naval", "mag", "h20", "ohval"]
        if all(param_data.get(k, 0.0) == 0.0 for k in chemical_keys):
            self._show_zero_error_popup(
                "All chemical input values are zero.\n\nPlease enter valid non-zero values for at least one chemical parameter before generating."
            )
            return
        # ─────────────────────────────────────────────────────────────────

        chemical_outputs = self._calculate_chemical_outputs(param_data)
        self.chemical_outputs = chemical_outputs

        self._disable_generate_button()
        self.all_model_results = None
        self._open_results_popup(param_data)
    
    def _open_results_popup(self, param_data):
        """Open a popup window showing the results with PRE-LOADED animated GIF"""
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title("Generating...")
        popup.resizable(False, False)

        # Configure colors
        popup.configure(fg_color=BG_MAIN)

        # Make it modal (disable main window until popup is closed)
        popup.transient(self.master)
        popup.grab_set()

        # ---- Center popup relative to the APP WINDOW (not the screen) ----
        popup_width  = 350
        popup_height = 250   # Smaller now — no Done button

        popup.update_idletasks()

        # Get the app window's position and size
        app = self.master.master          # ZeofyApp instance
        app.update_idletasks()
        app_x = app.winfo_rootx()
        app_y = app.winfo_rooty()
        app_w = app.winfo_width()
        app_h = app.winfo_height()

        # Calculate center relative to app window
        x = app_x + (app_w - popup_width)  // 2
        y = app_y + (app_h - popup_height) // 2.8

        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        # Configure grid — only 1 content row now (no button row)
        popup.grid_rowconfigure(0, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        # Content frame
        content_frame = ctk.CTkFrame(popup, fg_color=BG_MAIN, corner_radius=10)
        content_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # ========== ANIMATED GIF LABEL (USE PRE-LOADED FRAMES) ==========
        try:
            import tkinter as tk

            #USE PRE-LOADED GIF FRAMES from app (NO LOADING DELAY!)
            frames = app.gif_frames if hasattr(app, 'gif_frames') and app.gif_frames else None

            if frames:
                gif_label = tk.Label(
                    content_frame,
                    bg=BG_MAIN,
                    borderwidth=0,
                    highlightthickness=0
                )
                gif_label.pack(expand=True, pady=(20, 10))

                current_frame = [0]

                def animate_gif():
                    """Animate the GIF using pre-loaded frames"""
                    if popup.winfo_exists():
                        gif_label.configure(image=frames[current_frame[0]])
                        current_frame[0] = (current_frame[0] + 1) % len(frames)
                        popup.after(50, animate_gif)

                animate_gif()
            else:
                raise Exception("Frames not pre-loaded")

        except Exception as e:
            print(f"Using fallback (no GIF): {e}")
            fallback_label = ctk.CTkLabel(
                content_frame,
                text="Loading...",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=WHITE
            )
            fallback_label.pack(expand=True, pady=(30, 10))

        # Status label
        status_label = ctk.CTkLabel(
            content_frame,
            text="Processing...",
            font=ctk.CTkFont(size=12),
            text_color=LIGHT_GREY
        )
        status_label.pack(expand=True, pady=(0, 20))

        # Progress bar
        progress_bar = ctk.CTkProgressBar(
            content_frame,
            mode="determinate",
            progress_color=GOOD_COLOR,
            fg_color="#1a1a1a",
            height=10
        )
        progress_bar.pack(fill="x", padx=40, pady=(0, 30))
        progress_bar.set(0)

        # Start the progress simulation — no done_btn passed anymore

        # ---- Guard against manual X-button close ----
        self._cancelled = False

        def on_popup_close():
            self._cancelled = True
            if popup.winfo_exists():
                popup.destroy()
            # Cancelled mid-generate: restore Generate, keep Reset disabled
            self._enable_generate_button()
            self._disable_reset_button()

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)
        self._simulate_progress(popup, progress_bar, status_label, param_data)

        # Wait for the popup to be closed before continuing
        popup.wait_window()
    
    def _simulate_progress(self, popup, progress_bar, status_label, param_data):
        """Run model processing with timer-based progress — auto-closes when done."""

        #USE PRE-LOADED MODEL - No initialization delay!
        model = self.model

        # Store results
        self.model_results = None
        self.model_complete = False

        # Timer settings
        total_duration   = 2000   # ms — visual progress bar fill duration
        update_interval  = 100    # ms per tick
        total_steps      = total_duration // update_interval
        current_step     = [0]

        # Status messages with timing
        status_timeline = [
            (0, 1, "Running prediction..."),
            (1, 2, "Finalizing results..."),
        ]

        def get_status_text(elapsed_seconds):
            for start, end, text in status_timeline:
                if start <= elapsed_seconds < end:
                    return text
            return "Complete!"

        def update_progress_timer():
            if not popup.winfo_exists():
                return
                return

            current_step[0] += 1
            progress        = (current_step[0] / total_steps) * 100
            elapsed_seconds = (current_step[0] * update_interval) / 1000

            # Update progress bar and status text
            progress_bar.set(progress / 100)
            status_label.configure(text=get_status_text(elapsed_seconds))

            if current_step[0] >= total_steps:
                # Visual progress bar is full — check if model thread is done
                if self.model_complete:
                    # ✅ Both done: auto-close and update UI
                    self._close_popup_and_update(popup)
                else:
                    # Model still working — keep waiting
                    status_label.configure(text="Processing... (almost done)")
                    popup.after(100, update_progress_timer)
            else:
                popup.after(update_interval, update_progress_timer)

        def run_model():
            try:
                from model_selector import ModelSelector
                print("\n" + "=" * 60)
                print("  PREDICTION STARTED — running all 6 models")
                print("=" * 60)

                # Run every model version on the same input and cache results
                all_results = model.predict_all_models(params=param_data, n=5)

                if self._cancelled:
                    return

                self.all_model_results = all_results

                # Pick the currently selected version for the initial display
                active_version = ModelSelector.get_current_version()
                result = all_results.get(active_version) if all_results else None
                self.model_results = result
                self.model_complete = True

                if all_results:
                    print("\n" + "=" * 60)
                    print("  ✓ ALL MODELS COMPLETE")
                    print("=" * 60)
                    for vk, vr in all_results.items():
                        if vk == "errors" or vr is None:
                            continue
                        lbl = ModelSelector.MODEL_CONFIGS[vk].get("display_label", vk)
                        print(f"  {lbl:<30} → {vr['predicted_framework']} @ {vr['confidence']:.1f}%")
                    errors = all_results.get("errors", {})
                    if errors:
                        print("  Errors:", errors)
                    print("=" * 60 + "\n")

            except Exception as e:
                print(f"Error during model processing: {e}")
                import traceback
                traceback.print_exc()
                self.model_complete = True
                popup.after(0, lambda: status_label.configure(text=f"Error: {str(e)}"))

        # Start model processing in a background thread to keep UI responsive
        model_thread = threading.Thread(target=run_model, daemon=True)
        model_thread.start()

        # Start the progress timer
        update_progress_timer()
    
    # --------------------------------------------------
    # VERSION SWITCH — called by sidebar, re-renders from cache (no re-inference)
    # --------------------------------------------------
    def switch_to_version(self, version_key: str):
        """Re-render charts from the cached all_model_results for version_key.

        Called by the sidebar whenever the user selects a different model.
        If no cache exists yet (user hasn't clicked Generate), does nothing.
        """
        if not self.all_model_results:
            # Nothing to show yet — wait for first Generate
            return

        result = self.all_model_results.get(version_key)
        if result is None or not result.get("success"):
            lbl = version_key
            try:
                from model_selector import ModelSelector
                lbl = ModelSelector.MODEL_CONFIGS[version_key].get("display_label", version_key)
            except Exception:
                pass
            print(f"[MainPanel] No cached result for {lbl} — skipping re-render")
            return

        print(f"[MainPanel] Switching display to {version_key} (from cache)")
        self.model_results = result

        # Generate stays disabled; Reset stays active (results are still live)
        self._disable_generate_button()
        self._enable_reset_button()

        self._update_ui_with_results(result, animated=True)

    def _disable_generate_button(self):
        self.generate_btn.configure(
            state="disabled", fg_color="#3a3a3a",
            hover_color="#3a3a3a", text_color="#666666"
        )

    def _enable_generate_button(self):
        """Only called after Reset clears results."""
        self.generate_btn.configure(
            state="normal", fg_color="#2563eb",
            hover_color="#437cf6", text_color=WHITE
        )

    def _enable_reset_button(self):
        """Activated after Generate animations complete."""
        self.reset_btn.configure(
            state="normal", fg_color="#dc2626",
            hover_color="#b91c1c", text_color=WHITE
        )

    def _disable_reset_button(self):
        self.reset_btn.configure(
            state="disabled", fg_color="#3a3a3a",
            hover_color="#3a3a3a", text_color="#666666"
        )

    def _reset_action(self):
        """Clear all inputs and charts; return to pre-generate state."""
        for entry in self.param_entries:
            entry.delete(0, "end")

        self._bar_chart.animate_to({}, duration_ms=400)
        self._circ_chart.animate_to(0, "Unknown", duration_ms=400)

        for widget in self.weightContainer.winfo_children():
            widget.destroy()
        self._create_weight_container()

        self.all_model_results = None
        self.model_results     = None
        self.chemical_outputs  = None

        self._disable_reset_button()
        self._disable_generate_button()   # _validate_inputs re-enables if fields filled

    def _show_zero_error_popup(self, message):
        """Styled error popup for all-zero inputs."""
        import tkinter as tk
        from PIL import Image, ImageTk, ImageSequence

        popup_width, popup_height = 350, 260

        popup = ctk.CTkToplevel(self)
        popup.title("Invalid Input")
        popup.resizable(False, False)
        popup.configure(fg_color=BG_MAIN)
        popup.transient(self.master)
        popup.grab_set()
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

        try:
            # Wrap the path with get_resource_path()
            gif_image = Image.open(get_resource_path("icons/error.gif"))
            frames = []
            for frame in ImageSequence.Iterator(gif_image):
                frames.append(ImageTk.PhotoImage(
                    frame.copy().convert("RGBA").resize((70, 70), Image.Resampling.LANCZOS)
                ))
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
            content, text=message,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=WHITE, wraplength=280, justify="center"
        ).pack(pady=(0, 10))

        ctk.CTkButton(
            content, text="OK",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=GOOD_COLOR, hover_color="#437cf6",
            text_color=WHITE, height=36, corner_radius=8,
            command=lambda: popup.destroy() if popup.winfo_exists() else None
        ).pack(fill="x", padx=20, pady=(0, 4))

    def _close_popup_and_update(self, popup):
        popup.destroy()
        if self.model_results and self.model_results.get("success"):
            # Generate stays disabled; Reset enabled after animations finish
            self._disable_generate_button()
            self._disable_reset_button()
            self._update_ui_with_results(self.model_results)
    
    def _update_ui_with_results(self, results, animated=True):
        try:
            print("\n" + "="*60)
            print("UPDATING UI WITH RESULTS")
            print("="*60)
            
            predicted_framework = results.get("predicted_framework", "Unknown")
            confidence = results.get("confidence", 0)
            top_predictions = results.get("top_predictions", [])
            
            print(f"Framework: {predicted_framework}")
            print(f"Confidence: {confidence:.2f}%")

            # Track when both animations are done before enabling Reset
            animations_done = [0]
            total_animations = 2  # circular + bar graph

            def on_animation_complete():
                animations_done[0] += 1
                if animations_done[0] >= total_animations:
                    self._enable_reset_button()

            # ---- Circular confidence — tween, no destroy/recreate ----
            if animated:
                self._circ_chart.animate_to(
                    int(confidence),
                    predicted_framework,
                    on_complete=on_animation_complete,
                )
            else:
                self._circ_chart.animate_to(
                    int(confidence),
                    predicted_framework,
                    duration_ms=0,
                )
                on_animation_complete()
            self.confidenceContainer.update_idletasks()

            # ---- Bar graph — tween bars in fixed FAU/LTA/CHA/MOR/MFI order ----
            # Build a dict: framework → probability, covering only FIXED_FRAMEWORKS
            pred_map = {p["framework"]: p["probability"] for p in top_predictions}

            if animated:
                self._bar_chart.animate_to(
                    pred_map,
                    on_complete=on_animation_complete,
                )
            else:
                self._bar_chart.animate_to(
                    pred_map,
                    on_complete=on_animation_complete,
                    duration_ms=0,
                )
            self.graphContainer.update_idletasks()

            # ---- Weight container (no animation, update immediately) ----
            if hasattr(self, 'chemical_outputs') and self.chemical_outputs:
                for widget in self.weightContainer.winfo_children():
                    widget.destroy()
                
                create_weight_container(
                    self.weightContainer,
                    WHITE,
                    LIGHT_GREY,
                    SCROLLBAR_COLOR,
                    SCROLLBAR_HOVER_COLOR,
                    output_values=self.chemical_outputs
                )
                self.weightContainer.update_idletasks()

            print("UI updated successfully!")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"Error updating UI: {e}")
            import traceback
            traceback.print_exc()
            self._enable_generate_button()
            self._disable_reset_button()
    
# -------------------- MAIN EXECUTION ----------------
if __name__ == "__main__":
    app = ZeofyApp()
    app.mainloop()