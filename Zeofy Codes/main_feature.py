import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Wedge


# ============================================================
#  FIXED FRAMEWORK ORDER — bars always appear in this sequence
# ============================================================
FIXED_FRAMEWORKS = ["FAU", "LTA", "CHA", "MOR", "MFI"]

class PersistentBarChart:
    """
    A bar chart that lives for the entire lifetime of the panel.
    Bars are always in FIXED_FRAMEWORKS order.
    Calling animate_to() smoothly tweens heights from current → target.
    """

    FPS              = 60
    FRAME_MS         = 1000 // FPS   # ~16 ms
    INITIAL_DURATION = 1500          # ms for the very first fill
    UPDATE_DURATION  = 600           # ms for model-switch tweens

    def __init__(self, master, threshold, good_color, bad_color,
                 bg_color, grid_color):
        self._master      = master
        self._threshold   = threshold
        self._good_color  = good_color
        self._bad_color   = bad_color
        self._bg_color    = bg_color
        self._grid_color  = grid_color

        # Current displayed heights (start at zero)
        self._current_vals = [0.0] * len(FIXED_FRAMEWORKS)
        self._target_vals  = [0.0] * len(FIXED_FRAMEWORKS)
        # Live values for tooltip (kept in sync with current_vals)
        self._live_vals    = list(self._current_vals)

        self._anim_job   = None   # pending after() id
        self._anim_frame = 0
        self._anim_total = 1

        # Build the figure
        self._fig = Figure(figsize=(6, 4), dpi=100, frameon=False)
        self._ax  = self._fig.add_subplot(111)

        colors = [good_color if v >= threshold else bad_color
                  for v in self._current_vals]
        self._bars = self._ax.bar(FIXED_FRAMEWORKS, self._current_vals,
                                  color=colors)

        self._ax.set_title("Zeolite Frameworks")
        self._ax.set_ylabel("Percentage (%)")
        self._ax.set_ylim(0, 100)

        for spine in self._ax.spines.values():
            spine.set_visible(False)

        self._ax.grid(axis="y", color=grid_color, alpha=0.3,
                      linestyle="--", linewidth=0.5)
        self._ax.set_axisbelow(True)
        self._ax.set_facecolor(bg_color)
        self._fig.patch.set_facecolor(bg_color)
        self._ax.tick_params(axis="x", colors="white")
        self._ax.tick_params(axis="y", colors="white")
        self._ax.title.set_color("white")
        self._ax.yaxis.label.set_color("white")
        self._fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.15)

        self._canvas = FigureCanvasTkAgg(self._fig, master=master)
        self._canvas.draw()
        widget = self._canvas.get_tk_widget()
        widget.configure(bg=bg_color, highlightthickness=0, bd=0, relief="flat")
        widget.pack(fill="both", expand=True, padx=8, pady=8)

        self._setup_tooltip()

    # ----------------------------------------------------------
    def animate_to(self, values_dict: dict, on_complete=None,
                   duration_ms: int = None):
        if duration_ms is None:
            # Use longer duration if bars are currently all-zero (first fill)
            all_zero = all(v == 0.0 for v in self._current_vals)
            duration_ms = self.INITIAL_DURATION if all_zero else self.UPDATE_DURATION

        # Cancel any in-flight animation
        if self._anim_job is not None:
            try:
                self._master.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

        self._start_vals  = list(self._current_vals)
        self._target_vals = [float(values_dict.get(fw, 0.0))
                             for fw in FIXED_FRAMEWORKS]
        self._anim_frame  = 0
        self._anim_total  = max(1, duration_ms // self.FRAME_MS)
        self._on_complete = on_complete

        self._tick()

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
                color = self._good_color if self._target_vals[i] >= self._threshold else self._bad_color
                bar.set_facecolor(color)
                self._current_vals[i] = h
                self._live_vals[i]    = h

            self._canvas.draw_idle()
            self._anim_frame += 1
            self._anim_job = self._master.after(self.FRAME_MS, self._tick)
        else:
            # Snap to exact targets
            for i, bar in enumerate(self._bars):
                bar.set_height(self._target_vals[i])
                color = self._good_color if self._target_vals[i] >= self._threshold else self._bad_color
                bar.set_facecolor(color)
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
            bbox=dict(boxstyle="round, pad=0.8", fc="#ffffff", ec="#ffffff",
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
                    cont, _ = bar.contains(event)
                    if cont:
                        hovering = True
                        x = bar.get_x() + bar.get_width() / 2
                        y = bar.get_height()
                        annot.xy = (x, y)
                        annot.set_text(f"{FIXED_FRAMEWORKS[i]}\n{self._live_vals[i]:.2f}%")
                        annot.get_bbox_patch().set_facecolor("#ffffff")
                        annot.get_bbox_patch().set_edgecolor("#ffffff")
                        annot.set_visible(True)
                        bar.set_edgecolor("#232323")
                        bar.set_linewidth(2)
                        canvas.draw_idle()
                        break
                if not hovering:
                    annot.set_visible(False)
                    for bar in self._bars:
                        bar.set_edgecolor("none")
                        bar.set_linewidth(0)
                    canvas.draw_idle()
            else:
                if annot.get_visible():
                    annot.set_visible(False)
                    for bar in self._bars:
                        bar.set_edgecolor("none")
                        bar.set_linewidth(0)
                    canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", on_hover)


class PersistentCircularChart:

    FPS              = 60
    FRAME_MS         = 1000 // FPS
    INITIAL_DURATION = 800
    UPDATE_DURATION  = 500

    def __init__(self, master, good_color, bad_color, bg_color, white_color):
        self._master      = master
        self._good_color  = good_color
        self._bad_color   = bad_color
        self._bg_color    = bg_color
        self._white_color = white_color

        self._current_pct = 0.0
        self._target_pct  = 0.0
        self._anim_job    = None
        self._anim_frame  = 0
        self._anim_total  = 1
        self._on_complete = None

        master.grid_rowconfigure(0, weight=2)
        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)

        self._num_frame  = ctk.CTkFrame(master, fg_color="transparent")
        self._num_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=0)

        self._name_frame = ctk.CTkFrame(master, fg_color="transparent")
        self._name_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))

        self._fig = Figure(figsize=(2, 2), dpi=100)
        self._fig.patch.set_facecolor(bg_color)
        ax = self._fig.add_subplot(111)
        ax.axis("equal")
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis("off")
        ax.set_facecolor(bg_color)
        self._ax = ax

        ax.add_patch(Wedge((0, 0), 1, 0, 360, width=0.15, facecolor=bg_color))
        self._arc = Wedge((0, 0), 1, 0, 0, width=0.15, facecolor=good_color)
        ax.add_patch(self._arc)

        self._pct_text = ax.text(0, 0, "0%", ha="center", va="center",
                                 fontsize=20, fontweight="bold",
                                 color=good_color)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self._num_frame)
        self._canvas.draw()
        w = self._canvas.get_tk_widget()
        w.configure(bg=bg_color, highlightthickness=0, bd=0, relief="flat")
        w.pack(fill="both", expand=True)

        self._label = ctk.CTkLabel(
            self._name_frame,
            text="Unknown",
            font=ctk.CTkFont(size=16),
            text_color=white_color,
            wraplength=150,
        )
        self._label.pack(anchor="center", pady=(5, 5))

    # ----------------------------------------------------------
    def animate_to(self, percentage: float, zeolite_text: str,
                   on_complete=None, duration_ms: int = None):
        if duration_ms is None:
            all_zero = (self._current_pct == 0.0)
            duration_ms = self.INITIAL_DURATION if all_zero else self.UPDATE_DURATION

        if self._anim_job is not None:
            try:
                self._master.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

        self._start_pct  = self._current_pct
        self._target_pct = float(percentage)
        self._anim_frame = 0
        self._anim_total = max(1, duration_ms // self.FRAME_MS)
        self._on_complete = on_complete

        # Update label immediately
        self._label.configure(text=zeolite_text)

        # Update arc colour based on target
        color = self._good_color if percentage >= 50 else self._bad_color
        self._arc.set_facecolor(color)
        self._pct_text.set_color(color)

        self._tick()

    # ----------------------------------------------------------
    def _ease_out_quad(self, t):
        return 1 - (1 - t) * (1 - t)

    def _tick(self):
        w = self._canvas.get_tk_widget()
        if not w.winfo_exists():
            return

        if self._anim_frame <= self._anim_total:
            t = self._anim_frame / self._anim_total
            e = self._ease_out_quad(t)
            pct = self._start_pct + (self._target_pct - self._start_pct) * e
            self._arc.set_theta2(360 * pct / 100)
            self._pct_text.set_text(f"{int(pct)}%")
            self._current_pct = pct
            self._canvas.draw_idle()
            self._anim_frame += 1
            self._anim_job = self._master.after(self.FRAME_MS, self._tick)
        else:
            self._arc.set_theta2(360 * self._target_pct / 100)
            self._pct_text.set_text(f"{int(self._target_pct)}%")
            self._current_pct = self._target_pct
            self._canvas.draw_idle()
            self._anim_job = None
            if self._on_complete:
                self._on_complete()


def create_bar_graph(master, labels, values, threshold, good_color, bad_color, graph_container, grid_color):
    bar_colors = [good_color if v >= threshold else bad_color for v in values]

    fig = Figure(figsize=(6, 4), dpi=100, frameon=False)
    ax = fig.add_subplot(111)

    # Create bars
    bars = ax.bar(labels, values, color=bar_colors)

    ax.set_title("Zeolite Frameworks")
    ax.set_ylabel("Percentage (%)")
    ax.set_ylim(0, 100)

    for spine in ax.spines.values():
        spine.set_visible(False)

    # REMOVED: Grid lines are now disabled
    # ax.grid(axis="y", color=grid_color, alpha=0.25, linestyle="--")
    ax.grid(axis="y", color=grid_color, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)
    
    ax.set_facecolor(graph_container)
    fig.patch.set_facecolor(graph_container)

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    ax.title.set_color("white")
    ax.yaxis.label.set_color("white")

    fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.15)

    canvas = FigureCanvasTkAgg(fig, master=master)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=graph_container, highlightthickness=0, bd=0, relief="flat")
    widget.pack(fill="both", expand=True, padx=8, pady=8)

    # ========== INTERACTIVE TOOLTIP ==========
    # Create annotation (tooltip) - initially invisible
    annot = ax.annotate(
        "", 
        xy=(0, 0), 
        xytext=(0, 10),
        textcoords="offset points",
        bbox=dict(boxstyle="round, pad=0.8", fc="#ffffff", ec="#ffffff", lw=2, alpha=0.95),
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
        
        # Format tooltip text
        text = f"{label}\n{value:.2f}%"
        annot.set_text(text)
        
        # Position tooltip above bar
        annot.get_bbox_patch().set_facecolor("#ffffff")
        annot.get_bbox_patch().set_edgecolor("#ffffff")

    def on_hover(event):
        if event.inaxes == ax:
            # Check if hovering over any bar
            hovering = False
            for i, bar in enumerate(bars):
                cont, _ = bar.contains(event)
                if cont:
                    hovering = True
                    update_annot(bar, labels[i], values[i])
                    annot.set_visible(True)
                    
                    # Highlight the bar
                    bar.set_alpha(1.0)
                    bar.set_edgecolor("#232323")
                    bar.set_linewidth(2)
                    
                    canvas.draw_idle()
                    break  # Only highlight one bar at a time
            
            # If not hovering over any bar, hide tooltip and reset ALL bars
            if not hovering:
                annot.set_visible(False)
                for bar in bars:
                    bar.set_alpha(1.0)
                    bar.set_edgecolor("none")
                    bar.set_linewidth(0)
                canvas.draw_idle()
        else:
            # Mouse is outside the axes area - hide tooltip
            if annot.get_visible():
                annot.set_visible(False)
                for bar in bars:
                    bar.set_alpha(1.0)
                    bar.set_edgecolor("none")
                    bar.set_linewidth(0)
                canvas.draw_idle()

    # Connect hover event
    canvas.mpl_connect("motion_notify_event", on_hover)


def create_animated_bar_graph(master, labels, values, threshold, good_color, bad_color, graph_container, grid_color, animation_duration=1500, on_complete=None):
    bar_colors = [good_color if v >= threshold else bad_color for v in values]

    fig = Figure(figsize=(6, 4), dpi=100, frameon=False)
    ax = fig.add_subplot(111)

    # Create bars starting at 0 height
    bars = ax.bar(labels, [0] * len(values), color=bar_colors)

    ax.set_title("Zeolite Frameworks")
    ax.set_ylabel("Percentage (%)")
    ax.set_ylim(0, 100)

    for spine in ax.spines.values():
        spine.set_visible(False)
    
    ax.set_facecolor(graph_container)
    fig.patch.set_facecolor(graph_container)

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    ax.title.set_color("white")
    ax.yaxis.label.set_color("white")

    fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.15)

    canvas = FigureCanvasTkAgg(fig, master=master)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=graph_container, highlightthickness=0, bd=0, relief="flat")
    widget.pack(fill="both", expand=True, padx=8, pady=8)

    # ========== ANIMATION VARIABLES ==========
    fps = 60  # Frames per second
    frame_interval = 1000 // fps  # ~16ms per frame
    total_frames = (animation_duration // frame_interval)  # Number of frames
    current_frame = [0]  # Use list to modify in nested function
    
    # Animation using easing function (ease-out quad for smooth deceleration)
    def ease_out_quad(t):
        return 1 - (1 - t) * (1 - t)
    
    def animate_bars():
        if not widget.winfo_exists():
            return
        
        if current_frame[0] < total_frames:
            # Calculate progress (0 to 1)
            progress = current_frame[0] / total_frames
            eased_progress = ease_out_quad(progress)
            
            # Update each bar height
            for i, (bar, target_value) in enumerate(zip(bars, values)):
                current_height = target_value * eased_progress
                bar.set_height(current_height)
            
            # Redraw canvas
            canvas.draw_idle()
            
            # Increment frame
            current_frame[0] += 1
            
            # Schedule next frame
            master.after(frame_interval, animate_bars)
        else:
            # Animation complete - ensure bars are at exact final values
            for bar, target_value in zip(bars, values):
                bar.set_height(target_value)
            canvas.draw_idle()
            
            # Now enable tooltips after animation completes
            setup_tooltips()

            # Notify caller that bar animation is done
            if on_complete:
                on_complete()
    
    def setup_tooltips():
        # Create annotation (tooltip) - initially invisible
        annot = ax.annotate(
            "", 
            xy=(0, 0), 
            xytext=(0, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round, pad=0.8", fc="#ffffff", ec="#ffffff", lw=2, alpha=0.95),
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
            
            # Format tooltip text
            text = f"{label}\n{value:.2f}%"
            annot.set_text(text)
            
            # Position tooltip above bar
            annot.get_bbox_patch().set_facecolor("#ffffff")
            annot.get_bbox_patch().set_edgecolor("#ffffff")

        def on_hover(event):
            """Handle mouse hover events - tooltip disappears when not hovering"""
            if event.inaxes == ax:
                # Check if hovering over any bar
                hovering = False
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        hovering = True
                        update_annot(bar, labels[i], values[i])
                        annot.set_visible(True)
                        
                        # Highlight the bar
                        bar.set_alpha(1.0)
                        bar.set_edgecolor("#232323")
                        bar.set_linewidth(2)
                        
                        canvas.draw_idle()
                        break  
                
                # If not hovering over any bar, hide tooltip and reset ALL bars
                if not hovering:
                    annot.set_visible(False)
                    for bar in bars:
                        bar.set_alpha(1.0)
                        bar.set_edgecolor("none")
                        bar.set_linewidth(0)
                    canvas.draw_idle()
            else:
                # Mouse is outside the axes area - hide tooltip
                if annot.get_visible():
                    annot.set_visible(False)
                    for bar in bars:
                        bar.set_alpha(1.0)
                        bar.set_edgecolor("none")
                        bar.set_linewidth(0)
                    canvas.draw_idle()

        # Connect hover event
        canvas.mpl_connect("motion_notify_event", on_hover)
    
    # Start the animation
    animate_bars()



def create_circular_confidence(master, percentage, zeolite_text, good_color, bad_color, 
                               progress_bg_color, white_color):
    color = good_color if percentage >= 50 else bad_color

    master.grid_rowconfigure(0, weight=2)
    master.grid_rowconfigure(1, weight=1)
    master.grid_columnconfigure(0, weight=1)

    # Number container for circular bar
    numberContainer = ctk.CTkFrame(master, fg_color="transparent")
    numberContainer.grid(row=0, column=0, sticky="nsew", padx=10, pady=0)

    # Name container for label
    nameContainer = ctk.CTkFrame(master, fg_color="transparent")
    nameContainer.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))

    # Circular bar figure
    fig = Figure(figsize=(2, 2), dpi=100)
    fig.patch.set_facecolor(progress_bg_color)
    ax = fig.add_subplot(111)
    ax.axis("equal")
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis("off")
    ax.set_facecolor(progress_bg_color)

    # Background ring
    background_circle = Wedge(center=(0, 0), r=1, theta1=0, theta2=360, width=0.15, facecolor=progress_bg_color)
    ax.add_patch(background_circle)

    # Progress ring
    progress_circle = Wedge(center=(0, 0), r=1, theta1=0, theta2=(360 * percentage / 100), width=0.15, facecolor=color)
    ax.add_patch(progress_circle)

    # Percentage text
    ax.text(0, 0, f"{percentage}%", ha="center", va="center", fontsize=20, fontweight="bold", color=color)

    canvas = FigureCanvasTkAgg(fig, master=numberContainer)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=progress_bg_color, highlightthickness=0, bd=0, relief="flat")
    widget.pack(fill="both", expand=True)

    # Zeolite label with wraplength
    label = ctk.CTkLabel(
        nameContainer,
        text=zeolite_text,
        font=ctk.CTkFont(size=16),
        text_color=white_color,
        wraplength=150
    )
    label.pack(anchor="center", pady=(5, 5))


def create_animated_circular_confidence(master, percentage, zeolite_text, good_color, bad_color,
                                       progress_bg_color, white_color, animation_duration=800,
                                       on_complete=None):
    color = good_color if percentage >= 50 else bad_color

    master.grid_rowconfigure(0, weight=2)
    master.grid_rowconfigure(1, weight=1)
    master.grid_columnconfigure(0, weight=1)

    numberContainer = ctk.CTkFrame(master, fg_color="transparent")
    numberContainer.grid(row=0, column=0, sticky="nsew", padx=10, pady=0)

    nameContainer = ctk.CTkFrame(master, fg_color="transparent")
    nameContainer.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))

    fig = Figure(figsize=(2, 2), dpi=100)
    fig.patch.set_facecolor(progress_bg_color)
    ax = fig.add_subplot(111)
    ax.axis("equal")
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis("off")
    ax.set_facecolor(progress_bg_color)

    background_circle = Wedge(center=(0, 0), r=1, theta1=0, theta2=360, width=0.15, facecolor=progress_bg_color)
    ax.add_patch(background_circle)

    progress_circle = Wedge(center=(0, 0), r=1, theta1=0, theta2=0, width=0.15, facecolor=color)
    ax.add_patch(progress_circle)

    percentage_text = ax.text(0, 0, "0%", ha="center", va="center", fontsize=20, fontweight="bold", color=color)

    canvas = FigureCanvasTkAgg(fig, master=numberContainer)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=progress_bg_color, highlightthickness=0, bd=0, relief="flat")
    widget.pack(fill="both", expand=True)

    label = ctk.CTkLabel(
        nameContainer,
        text=zeolite_text,
        font=ctk.CTkFont(size=16),
        text_color=white_color,
        wraplength=150
    )
    label.pack(anchor="center", pady=(5, 5))

    # ========== ANIMATION ==========
    fps = 60
    frame_interval = 1000 // fps
    total_frames = max(1, animation_duration // frame_interval)
    current_frame = [0]

    def ease_out_quad(t):
        return 1 - (1 - t) * (1 - t)

    def animate_circle():
        if not widget.winfo_exists():
            return

        if current_frame[0] < total_frames:
            progress = current_frame[0] / total_frames
            eased_progress = ease_out_quad(progress)

            current_percentage = percentage * eased_progress
            current_angle = 360 * (current_percentage / 100)

            progress_circle.set_theta2(current_angle)
            percentage_text.set_text(f"{int(current_percentage)}%")
            canvas.draw_idle()

            current_frame[0] += 1
            master.after(frame_interval, animate_circle)
        else:
            # Snap to exact final values
            final_angle = 360 * (percentage / 100)
            progress_circle.set_theta2(final_angle)
            percentage_text.set_text(f"{int(percentage)}%")
            canvas.draw_idle()

            # Notify caller that animation is complete
            if on_complete:
                on_complete()

    animate_circle()


def validate_numeric_input(new_value):
    if new_value == "" or new_value == "Enter a value":
        return True
    
    # Allow numbers, one decimal point, and optional negative sign at start
    if new_value == "-":
        return True
    
    try:
        float(new_value)
        return True
    except ValueError:
        return False


def attach_placeholder_behavior(entry_widget, placeholder_text="Enter a value", placeholder_color="grey"):
    # Set initial placeholder
    if entry_widget.get().strip() == "":
        entry_widget.insert(0, placeholder_text)
        entry_widget.configure(text_color=placeholder_color)

    def on_focus_in(event):
        if entry_widget.get() == placeholder_text:
            entry_widget.delete(0, "end")
            entry_widget.configure(text_color="white")

    def on_focus_out(event):
        if entry_widget.get().strip() == "":
            entry_widget.insert(0, placeholder_text)
            entry_widget.configure(text_color=placeholder_color)

    entry_widget.bind("<FocusIn>", on_focus_in)
    entry_widget.bind("<FocusOut>", on_focus_out)


def create_condition_inputs(master, param_color, white_color, scrollbar_color, scrollbar_hover_color):
    # Scrollable frame for parameters with custom scrollbar
    scrollFrame = ctk.CTkScrollableFrame(
        master,
        fg_color="transparent",
        scrollbar_button_color=scrollbar_color,
        scrollbar_button_hover_color=scrollbar_hover_color,
        scrollbar_fg_color="transparent"
    )
    scrollFrame.pack(fill="both", expand=True, padx=15, pady=15)

    # Customize scrollbar width (access internal scrollbar widget)
    scrollFrame._scrollbar.configure(width=8)

    # Store entry widgets
    param_entries = []
    
    # Parameter names
    param_names = [
        "Silicon",
        "Aluminum",
        "Sodium",
        "Water Content",
        "Extra-Framework cations",
        "Hydroxyl concentration",
        "Time (Hours)",
        "Temperature",
        "Metakaolin"  
    ]

    # Create 9 parameter input fields (8 for model + 1 for Metakolin)
    for i in range(9):
        # Parameter label
        param_label = ctk.CTkLabel(
            scrollFrame,
            text=param_names[i],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=param_color,
            anchor="w"
        )
        param_label.pack(anchor="w", pady=(5 if i > 0 else 0, 5))

        # Entry field with validation
        param_entry = ctk.CTkEntry(
            scrollFrame,
            placeholder_text="",  
            height=35,
            fg_color="#1a1a1a",
            border_color="#3a3a3a",
            text_color=white_color
        )
        
        # Register validation function
        vcmd = param_entry.register(validate_numeric_input)
        param_entry.configure(validate="key", validatecommand=(vcmd, "%P"))
        
        # Attach placeholder behavior
        attach_placeholder_behavior(param_entry, "Enter a value", param_color)
        
        param_entry.pack(fill="x", pady=(0, 5))
        param_entries.append(param_entry)

    return {
        'entries': param_entries,
        'scroll_frame': scrollFrame
    }


def create_weight_container(master, white_color, light_grey, scrollbar_color, scrollbar_hover_color, output_values=None):
    # Single scrollable frame wrapper with custom scrollbar
    scrollWrapper = ctk.CTkScrollableFrame(
        master,
        fg_color="transparent",
        scrollbar_button_color=scrollbar_color,
        scrollbar_button_hover_color=scrollbar_hover_color,
        scrollbar_fg_color="transparent"
    )
    scrollWrapper.pack(fill="both", expand=True, padx=15, pady=15)

    # Customize scrollbar width
    scrollWrapper._scrollbar.configure(width=8)

    # Configure grid inside scrollable frame: 1 row, 2 columns
    scrollWrapper.grid_columnconfigure(0, weight=1)
    scrollWrapper.grid_columnconfigure(1, weight=1)

    # ============= CHEMICAL CONTAINER (LEFT) =============
    chemicalContainer = ctk.CTkFrame(
        scrollWrapper,
        fg_color="transparent"
    )
    chemicalContainer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    chemicalContainer.grid_columnconfigure(0, weight=1)

    chemicalLabel = ctk.CTkLabel(
        chemicalContainer,
        text="Material",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=white_color,
        wraplength=200,
        anchor="w"
    )
    chemicalLabel.grid(row=0, column=0, sticky="w", pady=(0, 10))

    chemicals = ["Metakaolin", "RHA", "Al203", "Sodium Silicate", "NaOH", "Water"]
    for idx, chemical in enumerate(chemicals, start=1):
        itemLabel = ctk.CTkLabel(
            chemicalContainer,
            text=chemical,
            font=ctk.CTkFont(size=12),
            text_color=light_grey,
            wraplength=200,
            anchor="w"
        )
        itemLabel.grid(row=idx, column=0, sticky="w", pady=2)

    # ============= RATIO CONTAINER (RIGHT) =============
    ratioContainer = ctk.CTkFrame(
        scrollWrapper,
        fg_color="transparent"
    )
    ratioContainer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    ratioContainer.grid_columnconfigure(0, weight=1)

    ratioLabel = ctk.CTkLabel(
        ratioContainer,
        text="Amount in Grams",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=white_color,
        wraplength=200,
        anchor="w"
    )
    ratioLabel.grid(row=0, column=0, sticky="w", pady=(0, 10))

    # Display output values or placeholder
    if output_values:
        # Display calculated values
        for idx, chemical in enumerate(chemicals, start=1):
            value = output_values.get(chemical, 0.0)
            # Use light red for negative values, default white for positive/zero
            try:
                is_negative = float(value) < 0
            except (TypeError, ValueError):
                is_negative = False
            value_color = "#ff6b6b" if is_negative else white_color
            valueLabel = ctk.CTkLabel(
                ratioContainer,
                text=f"{value:.4f}",
                font=ctk.CTkFont(size=12),
                text_color=value_color,
                wraplength=200,
                anchor="w"
            )
            valueLabel.grid(row=idx, column=0, sticky="w", pady=2)
    else:
        # Display placeholder
        ratioPlaceholder = ctk.CTkLabel(
            ratioContainer,
            text="Output data will appear here...",
            font=ctk.CTkFont(size=12),
            text_color="#6b7280",
            wraplength=200,
            anchor="w"
        )
        ratioPlaceholder.grid(row=1, column=0, sticky="w", pady=2)