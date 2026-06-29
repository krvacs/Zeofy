import pandas as pd
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches


# ============================================================
#  FIXED FRAMEWORK ORDER — same as main panel
# ============================================================
FIXED_FRAMEWORKS = ["FAU", "LTA", "CHA", "MOR", "MFI"]


# ============================================================
#  PersistentBulkBarChart
#  Frequency/count bar chart that lives for the panel lifetime.
#  Bars are always in FIXED_FRAMEWORKS order.
#  animate_to(counts_dict) tweens heights up/down without reset.
# ============================================================
class PersistentBulkBarChart:

    FPS              = 60
    FRAME_MS         = 1000 // FPS
    INITIAL_DURATION = 1500   # ms — first fill after Generate
    UPDATE_DURATION  = 600    # ms — model-switch tween

    def __init__(self, master, good_color, bg_color, grid_color):
        self._master     = master
        self._good_color = good_color
        self._bg_color   = bg_color
        self._grid_color = grid_color

        self._current_vals = [0.0] * len(FIXED_FRAMEWORKS)
        self._target_vals  = [0.0] * len(FIXED_FRAMEWORKS)
        self._live_vals    = list(self._current_vals)

        self._anim_job   = None
        self._anim_frame = 0
        self._anim_total = 1
        self._on_complete = None

        # Build figure
        self._fig = Figure(figsize=(6, 4), dpi=100, frameon=False)
        self._ax  = self._fig.add_subplot(111)

        x_pos = range(len(FIXED_FRAMEWORKS))
        bar_colors = [bg_color] * len(FIXED_FRAMEWORKS)   # all invisible at start
        self._bars = self._ax.bar(x_pos, self._current_vals,
                                  color=bar_colors, width=0.6, linewidth=0.5)

        self._ax.set_xticks(list(x_pos))
        self._ax.set_xticklabels(FIXED_FRAMEWORKS)
        self._ax.set_title("Framework Frequency Distribution",
                           color="white", fontsize=12, pad=10)
        self._ax.set_ylabel("Count", color="white")
        self._ax.set_ylim(0, 10)   # placeholder; updated on animate_to

        # y-axis gridlines invisible (same as background), x-axis gridlines visible
        self._ax.yaxis.grid(True, color=grid_color,   alpha=0.3, linestyle="--", linewidth=0.5)
        self._ax.xaxis.grid(True, color=bg_color, alpha=1.0, linestyle="--", linewidth=0.5)
        self._ax.set_axisbelow(True)

        for spine in self._ax.spines.values():
            spine.set_visible(False)

        self._ax.set_facecolor(bg_color)
        self._fig.patch.set_facecolor(bg_color)
        self._ax.tick_params(axis="x", colors="white")
        self._ax.tick_params(axis="y", colors="white")

        self._legend_patch = mpatches.Patch(color=good_color, label="Framework Count")
        self._ax.legend(
            handles=[self._legend_patch], loc="upper right",
            framealpha=0.9, facecolor=bg_color, edgecolor=bg_color,
            labelcolor="white", fontsize=9,
        )

        self._fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.15)

        self._canvas = FigureCanvasTkAgg(self._fig, master=master)
        self._canvas.draw()
        widget = self._canvas.get_tk_widget()
        widget.configure(bg=bg_color, highlightthickness=0, bd=0, relief="flat")
        widget.pack(fill="both", expand=True, padx=8, pady=8)

        self._setup_tooltip()

    # ----------------------------------------------------------
    def animate_to(self, counts_dict: dict, on_complete=None,
                   duration_ms: int = None):
        """
        Tween bars from current counts to new values.
        counts_dict maps framework name → integer count.
        Frameworks not in the dict animate to 0.
        """
        if duration_ms is None:
            all_zero = all(v == 0.0 for v in self._current_vals)
            duration_ms = self.INITIAL_DURATION if all_zero else self.UPDATE_DURATION

        # Cancel any running animation
        if self._anim_job is not None:
            try:
                self._master.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

        self._start_vals  = list(self._current_vals)
        self._target_vals = [float(counts_dict.get(fw, 0))
                             for fw in FIXED_FRAMEWORKS]
        self._anim_frame  = 0
        self._anim_total  = max(1, duration_ms // self.FRAME_MS)
        self._on_complete = on_complete

        # Update y-axis ceiling to fit new targets (instant, no flicker)
        max_val = max(self._target_vals) if any(v > 0 for v in self._target_vals) else 10
        self._ax.set_ylim(0, max(max_val * 1.2, 1))

        # Colour bars: good_color if target > 0, else invisible
        for i, bar in enumerate(self._bars):
            color = self._good_color if self._target_vals[i] > 0 else self._bg_color
            bar.set_facecolor(color)

        self._tick()

    # ----------------------------------------------------------
    def animate_to_zero(self, duration_ms: int = 500, on_complete=None):
        """Animate bars downward to zero (used by Reset button)."""
        zero_dict = {fw: 0 for fw in FIXED_FRAMEWORKS}
        self.animate_to(zero_dict, on_complete=on_complete, duration_ms=duration_ms)

    # ----------------------------------------------------------
    def reset_to_zero(self):
        """Snap all bars to zero immediately (used by Reset button)."""
        if self._anim_job is not None:
            try:
                self._master.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

        for i, bar in enumerate(self._bars):
            bar.set_height(0)
            bar.set_facecolor(self._bg_color)
            self._current_vals[i] = 0.0
            self._live_vals[i]    = 0.0
            self._target_vals[i]  = 0.0

        self._ax.set_ylim(0, 10)
        self._canvas.draw_idle()

    # ----------------------------------------------------------
    def _ease_out_quad(self, t):
        return 1 - (1 - t) * (1 - t)

    def _tick(self):
        widget = self._canvas.get_tk_widget()
        if not widget.winfo_exists():
            return

        if self._anim_frame <= self._anim_total:
            t = self._anim_frame / self._anim_total
            e = self._ease_out_quad(t)

            for i, bar in enumerate(self._bars):
                h = self._start_vals[i] + (self._target_vals[i] - self._start_vals[i]) * e
                bar.set_height(h)
                self._current_vals[i] = h
                self._live_vals[i]    = h

            self._canvas.draw_idle()
            self._anim_frame += 1
            self._anim_job = self._master.after(self.FRAME_MS, self._tick)
        else:
            # Snap to exact targets
            for i, bar in enumerate(self._bars):
                bar.set_height(self._target_vals[i])
                self._current_vals[i] = self._target_vals[i]
                self._live_vals[i]    = self._target_vals[i]

            self._canvas.draw_idle()
            self._anim_job = None

            if self._on_complete:
                self._on_complete()

    # ----------------------------------------------------------
    def _setup_tooltip(self):
        ax     = self._ax
        canvas = self._canvas

        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.8", fc="#ffffff", ec="#ffffff",
                      lw=2, alpha=0.95),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0",
                            color="#ffffff", lw=2),
            fontsize=7,
            color="black",
            ha="center",
            zorder=1000,
        )
        annot.set_visible(False)

        def on_hover(event):
            if event.inaxes == ax:
                hovering = False
                for i, bar in enumerate(self._bars):
                    if self._live_vals[i] > 0:
                        cont, _ = bar.contains(event)
                        if cont:
                            hovering = True
                            x = bar.get_x() + bar.get_width() / 2
                            y = bar.get_height()
                            annot.xy = (x, y)
                            annot.set_text(
                                f"{FIXED_FRAMEWORKS[i]}\nCount: {int(self._live_vals[i])}"
                            )
                            annot.get_bbox_patch().set_facecolor("#ffffff")
                            annot.get_bbox_patch().set_edgecolor("#ffffff")
                            annot.set_visible(True)
                            bar.set_alpha(0.8)
                            bar.set_edgecolor("#2563eb")
                            bar.set_linewidth(2)
                            canvas.draw_idle()
                            break
                if not hovering:
                    annot.set_visible(False)
                    for i, bar in enumerate(self._bars):
                        if self._live_vals[i] > 0:
                            bar.set_alpha(1.0)
                            bar.set_edgecolor("white")
                            bar.set_linewidth(0.5)
                    canvas.draw_idle()
            else:
                if annot.get_visible():
                    annot.set_visible(False)
                    for i, bar in enumerate(self._bars):
                        if self._live_vals[i] > 0:
                            bar.set_alpha(1.0)
                            bar.set_edgecolor("white")
                            bar.set_linewidth(0.5)
                    canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", on_hover)


def validate_excel_file(file_path):
    try:
        # Accept both .xlsx/.xls and .csv — read everything as raw strings first
        if file_path.lower().endswith(".csv"):
            df_raw = pd.read_csv(file_path, dtype=str)
        else:
            df_raw = pd.read_excel(file_path, dtype=str)

        expected_columns = ['sival', 'alval', 'naval', 'h20', 'mag', 'ohval', 'time', 'temper', 'metakaolin']

        # Check 1: column names — still a hard reject, can't guess intent
        actual_columns = df_raw.columns.tolist()
        missing = [c for c in expected_columns if c not in actual_columns]
        extra   = [c for c in actual_columns if c not in expected_columns]
        if missing or extra:
            msg = ""
            if missing:
                msg += f"Missing columns: {', '.join(missing)}. "
            if extra:
                msg += f"Unexpected columns: {', '.join(extra)}."
            return {"valid": False, "error": msg.strip(), "observations": 0, "data": None}

        df_raw = df_raw[expected_columns]

        if len(df_raw) == 0:
            return {"valid": False, "error": "No observations found", "observations": 0, "data": None}

        # Keep a copy of the original raw strings for output preservation
        df_original = df_raw.copy()

        # Coerce to numeric — bad cells become NaN
        df_numeric = df_raw.copy()
        for col in expected_columns:
            df_numeric[col] = pd.to_numeric(df_raw[col], errors="coerce")

        # Replace inf/-inf with NaN so they are also flagged
        for col in expected_columns:
            df_numeric[col] = df_numeric[col].replace([float('inf'), float('-inf')], float('nan'))

        # Flag rows that have ANY bad cell
        bad_mask = df_numeric.isnull().any(axis=1)
        df_numeric["_row_error"] = bad_mask

        # Store original raw strings in hidden columns (_orig_<col>) so _run_bulk
        # can write them straight to the output Excel without any modification.
        for col in expected_columns:
            df_numeric[f"_orig_{col}"] = df_original[col]

        # Fill bad numeric cells with 0.0 only for model computation — originals
        # are preserved in the _orig_* columns and will appear in the output file.
        df_numeric[expected_columns] = df_numeric[expected_columns].fillna(0.0)

        n_bad = int(bad_mask.sum())
        print(f"[validate_excel_file] {len(df_numeric)} rows, {n_bad} flagged as invalid")

        return {
            "valid": True,
            "error": None,
            "observations": len(df_numeric),
            "bad_rows": n_bad,
            "data": df_numeric,
        }

    except Exception as e:
        return {"valid": False, "error": f"Error reading file: {str(e)}", "observations": 0, "data": None}


def create_observation_display(container, number, good_color, white_color):

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    # Container for content
    content_container = ctk.CTkFrame(container, fg_color="transparent")
    content_container.grid(row=0, column=0)
    content_container.grid_rowconfigure(0, weight=0)
    content_container.grid_rowconfigure(1, weight=0)
    content_container.grid_columnconfigure(0, weight=1)

    # Number label (large, blue)
    number_label = ctk.CTkLabel(
        content_container,
        text=str(number),
        font=ctk.CTkFont(size=48, weight="bold"),
        text_color=white_color
    )
    number_label.grid(row=0, column=0, pady=(0, 5))

    # "Observations" label (blue)
    text_label = ctk.CTkLabel(
        content_container,
        text="Observations",
        font=ctk.CTkFont(size=16),
        text_color=white_color
    )
    text_label.grid(row=1, column=0, pady=(5, 0))


def create_info_panel(container, white_color):

    # Configure grid
    container.grid_rowconfigure(0, weight=0)  # Title
    container.grid_rowconfigure(1, weight=1)  # Content area
    container.grid_columnconfigure(0, weight=1)
    
    # Title
    title_label = ctk.CTkLabel(
        container,
        text="File Information",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=white_color
    )
    title_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
    
    # Content frame
    content_frame = ctk.CTkFrame(container, fg_color="transparent")
    content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
    
    # Info items container
    info_items_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    info_items_frame.pack(fill="both", expand=True)
    
    return info_items_frame


def update_info_panel(info_items_frame, filename=None, upload_time=None, status="No file uploaded", 
                     white_color="#ffffff", good_color="#60a5fa"):
    
    # Clear existing content
    for widget in info_items_frame.winfo_children():
        widget.destroy()
    
    # File Name
    file_label = ctk.CTkLabel(
        info_items_frame,
        text="File Name:",
        font=ctk.CTkFont(size=12),
        text_color="#9ca3af",
        anchor="w"
    )
    file_label.pack(fill="x", padx=5, pady=(0, 5))
    
    file_value = ctk.CTkLabel(
        info_items_frame,
        text=filename if filename else "—",
        font=ctk.CTkFont(size=11),
        text_color=white_color,
        anchor="w",
        wraplength=200
    )
    file_value.pack(fill="x", padx=5, pady=(0, 15))
    
    # Upload Date/Time
    time_label = ctk.CTkLabel(
        info_items_frame,
        text="Uploaded:",
        font=ctk.CTkFont(size=12),
        text_color="#9ca3af",
        anchor="w"
    )
    time_label.pack(fill="x", padx=5, pady=(0, 5))
    
    time_value = ctk.CTkLabel(
        info_items_frame,
        text=upload_time if upload_time else "—",
        font=ctk.CTkFont(size=11),
        text_color=white_color,
        anchor="w"
    )
    time_value.pack(fill="x", padx=5, pady=(0, 15))
    
    # Status
    status_label = ctk.CTkLabel(
        info_items_frame,
        text="Status:",
        font=ctk.CTkFont(size=12),
        text_color="#9ca3af",
        anchor="w"
    )
    status_label.pack(fill="x", padx=5, pady=(0, 5))
    
    # Determine status color
    if status == "Ready to download":
        status_color = good_color
    elif status == "Processing...":
        status_color = "#fbbf24"
    elif status == "No file uploaded":
        status_color = "#6b7280" 
    else:
        status_color = white_color
    
    status_value = ctk.CTkLabel(
        info_items_frame,
        text=status,
        font=ctk.CTkFont(size=11),
        text_color=status_color,
        anchor="w"
    )
    status_value.pack(fill="x", pady=(0, 0))


def create_frequency_bar_graph(container, labels, values, good_color, graph_container, grid_color):

    # Ensure we always have 5 slots (pad with empty if needed)
    display_labels = labels[:5] if len(labels) >= 5 else labels + ["--"] * (5 - len(labels))
    display_values = values[:5] if len(values) >= 5 else values + [0] * (5 - len(values))
    
    # All bars blue (non-empty ones only show with color)
    bar_colors = [good_color if v > 0 else graph_container for v in display_values]
    
    fig = Figure(figsize=(6, 4), dpi=100, frameon=False)
    ax = fig.add_subplot(111)
    
    # Create bars with fixed positions
    x_pos = range(5)  # Always 5 positions
    bars = ax.bar(x_pos, display_values, color=bar_colors, width=0.6, edgecolor='white', linewidth=0.5)
    
    # Set x-axis labels
    ax.set_xticks(x_pos)
    ax.set_xticklabels(display_labels)
    
    ax.set_title("Framework Frequency Distribution", color="white", fontsize=12, pad=10)
    ax.set_ylabel("Count", color="white")
    
    # Set y-limit based on max value (ensure at least some height is visible)
    max_val = max(display_values) if any(v > 0 for v in display_values) else 10
    ax.set_ylim(0, max(max_val * 1.2, 1))  # At least 1 for visibility
    
    # Add grid for better readability
    ax.grid(axis="y", color=grid_color, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    ax.set_facecolor(graph_container)
    fig.patch.set_facecolor(graph_container)
    
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    
    # Add legend
    blue_patch = mpatches.Patch(color=good_color, label='Framework Count')
    ax.legend(handles=[blue_patch], loc='upper right', framealpha=0.9, 
             facecolor=graph_container, edgecolor=graph_container, 
             labelcolor='white', fontsize=9)
    
    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.15)
    
    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=graph_container, highlightthickness=0, bd=0, relief="flat")
    widget.pack(fill="both", expand=True, padx=8, pady=8)
    
    # Add hover functionality
    annot = ax.annotate(
        "", 
        xy=(0, 0), 
        xytext=(0, 10),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.8", fc="#ffffff", ec="#ffffff", lw=2, alpha=0.95),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color="#ffffff", lw=2),
        fontsize=7,
        color="black",
        ha="center",
        zorder=1000
    )
    annot.set_visible(False)
    
    def update_annot(bar, label, value):
        x = bar.get_x() + bar.get_width() / 2
        y = bar.get_height()
        annot.xy = (x, y)
        text = f"{label}\nCount: {int(value)}"
        annot.set_text(text)
        annot.get_bbox_patch().set_facecolor("#ffffff")
        annot.get_bbox_patch().set_edgecolor("#ffffff")
    
    def on_hover(event):
        if event.inaxes == ax:
            hovering = False
            for i, bar in enumerate(bars):
                # Only show tooltip for non-empty bars
                if display_values[i] > 0:
                    cont, _ = bar.contains(event)
                    if cont:
                        hovering = True
                        update_annot(bar, display_labels[i], display_values[i])
                        annot.set_visible(True)
                        # Highlight the bar
                        bar.set_alpha(0.8)
                        bar.set_edgecolor("#60a5fa")
                        bar.set_linewidth(2)
                        canvas.draw_idle()
                        break
            
            if not hovering:
                annot.set_visible(False)
                # Reset all bars to normal
                for i, bar in enumerate(bars):
                    if display_values[i] > 0:
                        bar.set_alpha(1.0)
                        bar.set_edgecolor("white")
                        bar.set_linewidth(0.5)
                canvas.draw_idle()
        else:
            if annot.get_visible():
                annot.set_visible(False)
                # Reset all bars
                for i, bar in enumerate(bars):
                    if display_values[i] > 0:
                        bar.set_alpha(1.0)
                        bar.set_edgecolor("white")
                        bar.set_linewidth(0.5)
                canvas.draw_idle()
    
    canvas.mpl_connect("motion_notify_event", on_hover)


def create_animated_frequency_bar_graph(container, labels, values, good_color, graph_container, grid_color, animation_duration=1500, on_complete=None):

    # Ensure we always have 5 slots (pad with empty if needed)
    display_labels = labels[:5] if len(labels) >= 5 else labels + ["--"] * (5 - len(labels))
    display_values = values[:5] if len(values) >= 5 else values + [0] * (5 - len(values))
    
    # All bars blue (non-empty ones only show with color)
    bar_colors = [good_color if v > 0 else graph_container for v in display_values]
    
    fig = Figure(figsize=(6, 4), dpi=100, frameon=False)
    ax = fig.add_subplot(111)
    
    # Create bars starting at 0 height
    x_pos = range(5)  
    bars = ax.bar(x_pos, [0] * 5, color=bar_colors, width=0.6, linewidth=0.5)
    
    # Set x-axis labels
    ax.set_xticks(x_pos)
    ax.set_xticklabels(display_labels)
    
    ax.set_title("Framework Frequency Distribution", color="white", fontsize=12, pad=10)
    ax.set_ylabel("Count", color="white")
    
    # Set y-limit based on max value
    max_val = max(display_values) if any(v > 0 for v in display_values) else 10
    ax.set_ylim(0, max(max_val * 1.2, 1))
    
    # Add grid for better readability
    ax.grid(axis="y", color=grid_color, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    ax.set_facecolor(graph_container)
    fig.patch.set_facecolor(graph_container)
    
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    
    # Add legend
    blue_patch = mpatches.Patch(color=good_color, label='Framework Count')
    ax.legend(handles=[blue_patch], loc='upper right', framealpha=0.9, 
             facecolor=graph_container, edgecolor=graph_container, 
             labelcolor='white', fontsize=9)
    
    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.15)
    
    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=graph_container, highlightthickness=0, bd=0, relief="flat")
    widget.pack(fill="both", expand=True, padx=8, pady=8)
    
    # ========== ANIMATION VARIABLES ==========
    fps = 60
    frame_interval = 1000 // fps
    total_frames = (animation_duration // frame_interval)
    current_frame = [0]
    
    def ease_out_quad(t):
        return 1 - (1 - t) * (1 - t)
    
    def animate_bars():
        if not widget.winfo_exists():
            return
        
        if current_frame[0] < total_frames:
            progress = current_frame[0] / total_frames
            eased_progress = ease_out_quad(progress)
            
            # Update each bar height
            for i, (bar, target_value) in enumerate(zip(bars, display_values)):
                current_height = target_value * eased_progress
                bar.set_height(current_height)
            
            canvas.draw_idle()
            current_frame[0] += 1
            container.after(frame_interval, animate_bars)
        else:
            # Animation complete
            for bar, target_value in zip(bars, display_values):
                bar.set_height(target_value)
            canvas.draw_idle()
            setup_tooltips()

            # Notify caller that animation is done
            if on_complete:
                on_complete()
    
    def setup_tooltips():
        annot = ax.annotate(
            "", 
            xy=(0, 0), 
            xytext=(0, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.8", fc="#ffffff", ec="#ffffff", lw=2, alpha=0.95),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color="#ffffff", lw=2),
            fontsize=7,
            color="black",
            ha="center",
            zorder=1000
        )
        annot.set_visible(False)
        
        def update_annot(bar, label, value):
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            annot.xy = (x, y)
            text = f"{label}\nCount: {int(value)}"
            annot.set_text(text)
            annot.get_bbox_patch().set_facecolor("#ffffff")
            annot.get_bbox_patch().set_edgecolor("#ffffff")
        
        def on_hover(event):
            if event.inaxes == ax:
                hovering = False
                for i, bar in enumerate(bars):
                    if display_values[i] > 0:
                        cont, _ = bar.contains(event)
                        if cont:
                            hovering = True
                            update_annot(bar, display_labels[i], display_values[i])
                            annot.set_visible(True)
                            bar.set_alpha(0.8)
                            bar.set_edgecolor("#2563eb")
                            bar.set_linewidth(2)
                            canvas.draw_idle()
                            break
                
                if not hovering:
                    annot.set_visible(False)
                    for i, bar in enumerate(bars):
                        if display_values[i] > 0:
                            bar.set_alpha(1.0)
                            bar.set_edgecolor("#2563eb")
                            bar.set_linewidth(0.5)
                    canvas.draw_idle()
            else:
                if annot.get_visible():
                    annot.set_visible(False)
                    for i, bar in enumerate(bars):
                        if display_values[i] > 0:
                            bar.set_alpha(1.0)
                            bar.set_edgecolor("white")
                            bar.set_linewidth(0.5)
                    canvas.draw_idle()
        
        canvas.mpl_connect("motion_notify_event", on_hover)
    
    # Start animation
    animate_bars()