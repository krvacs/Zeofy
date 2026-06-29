import customtkinter as ctk
from PIL import Image
import os
import sys
from pathlib import Path
from model_selector import ModelSelector


# ---------------------------------------------------------------------------
# Resource path helper (works both dev and PyInstaller)
# ---------------------------------------------------------------------------
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return Path(base_path) / relative_path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SIDEBAR_BG       = "#0f0f0f"
ACTIVE_COLOR     = "#2563eb"
HOVER_COLOR      = "#1d4ed8"
INACTIVE_TXT     = "#9ca3af"
ACTIVE_TXT       = "#ffffff"
COLLAPSED_WIDTH  = 64
EXPANDED_MIN     = 200          # wider min to fit sub-model labels
EXPANDED_MAX     = 280
COLLAPSE_BREAKPT = 900
WIDTH_RATIO      = 0.18


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
class Sidebar(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color=SIDEBAR_BG)

        self.is_collapsed = False
        self._resize_job  = None
        self._last_win_w  = None
        self._last_state  = None

        self.grid_propagate(False)
        self.configure(width=240)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)   # logo
        self.grid_rowconfigure(1, weight=0)   # nav buttons
        self.grid_rowconfigure(2, weight=0)   # versions section
        self.grid_rowconfigure(3, weight=1)   # bottom spacer

        self.icons     = self._load_icons()
        self.buttons   = []
        self._btn_meta = []

        self._build_logo()
        self._build_nav()
        self._build_versions()

        # Bind resize after window is fully drawn
        self.after(100, lambda: self.master.bind("<Configure>", self._on_window_configure))
        # Sync badges on startup (ZFY is selected by default)
        self.after(200, self._refresh_badges)

    # =========================================================================
    # BUILD SECTIONS
    # =========================================================================

    def _build_logo(self):
        self.logo_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_BG)
        self.logo_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(24, 16))
        self.logo_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.logo_frame,
            text="Zeofy",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ACTIVE_TXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

    def _build_nav(self):
        self.nav_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_BG)
        self.nav_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.nav_frame.grid_columnconfigure(0, weight=1)

        btn_data = [
            ("btn_synthesize", "  Synthesize",  "new",     True),
            ("btn_bulk",       "  Bulk Import", "sidebar", False),
            ("btn_review",     "  Review",      "review",  False),
        ]

        for row_idx, (attr, label, icon_key, active) in enumerate(btn_data):
            btn = self._make_nav_button(label, self.icons.get(icon_key), active)
            btn.grid(row=row_idx, column=0, pady=3, sticky="ew")
            setattr(self, attr, btn)
            self.buttons.append(btn)
            self._btn_meta.append((btn, label))

        self.active_button = self.btn_synthesize

    def _build_versions(self):
        """Build the Versions section: flat radio list of all 6 models."""
        self.check_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_BG)
        self.check_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.check_frame.grid_columnconfigure(0, weight=1)

        # Section label
        ctk.CTkLabel(
            self.check_frame,
            text="Versions",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ACTIVE_TXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(10, 6))

        # ── Shared checkbox style ─────────────────────────────────────────────
        _cb_style = dict(
            font=ctk.CTkFont(size=12),
            text_color=ACTIVE_TXT,
            fg_color=ACTIVE_COLOR,
            hover_color=HOVER_COLOR,
            border_color=ACTIVE_COLOR,
            border_width=2,
            corner_radius=100,
            checkbox_width=18,
            checkbox_height=18,
        )

        # ── Flat model list: (version_key, display_label) ────────────────────
        _all_models = [
            ("ZLF_XGBoost",      "XGBoost"),
            ("ZLF_RandomForest", "Random Forest"),
            ("ZLF_ExtraTrees",   "Extra Trees"),
            ("ZLF_SVM",          "SVM"),
            ("ZFY",              "ZFY"),
            ("ZLF_DecisionTree", "Decision Tree"),
        ]

        self._version_checkboxes = {}   # version_key -> CTkCheckBox

        for grid_row, (key, label) in enumerate(_all_models, start=1):
            cb = ctk.CTkCheckBox(
                self.check_frame,
                text=label,
                command=lambda k=key: self._on_version_selected(k),
                **_cb_style,
            )
            cb.grid(row=grid_row, column=0, sticky="w", padx=12, pady=3)
            self._version_checkboxes[key] = cb

        # XGBoost selected by default
        self._version_checkboxes["ZLF_XGBoost"].select()

        # Spacer at the bottom
        ctk.CTkLabel(
            self.check_frame, text="", height=8, fg_color=SIDEBAR_BG
        ).grid(row=len(_all_models) + 1, column=0)

    # =========================================================================
    # VERSION SELECTION LOGIC
    # =========================================================================

    def _on_version_selected(self, key):
        """Radio-select the clicked version: check it, uncheck all others."""
        cb = self._version_checkboxes[key]

        # Prevent unchecking the already-active item
        if not cb.get():
            cb.select()
            return

        # Deselect every other checkbox
        for k, other_cb in self._version_checkboxes.items():
            if k != key:
                other_cb.deselect()

        ModelSelector.set_version(key)
        self._refresh_badges()

        # ── Notify panels to re-render from their cached results ──────────
        app = self.master
        for panel_attr in ("main_panel", "bulk_panel"):
            panel = getattr(app, panel_attr, None)
            if panel is not None and hasattr(panel, "switch_to_version"):
                try:
                    panel.switch_to_version(key)
                except Exception as exc:
                    print(f"[Sidebar] switch_to_version error on {panel_attr}: {exc}")

    # =========================================================================
    # BADGE REFRESH — updates version labels in main_panel and bulk_panel
    # =========================================================================

    def _refresh_badges(self):
        """Push the active model label to header badges in all panels."""
        version    = ModelSelector.get_current_version()
        label      = ModelSelector.get_display_label()
        is_zfy     = (version == "ZFY")
        is_zlf_any = ModelSelector.is_zlf_version()

        print(f"[Sidebar] Active model → {version} ({label})")

        app = self.master
        for panel_attr in ("main_panel", "bulk_panel"):
            panel = getattr(app, panel_attr, None)
            if panel is None:
                continue

            # ── ZFY badge ──
            badge_zfy = getattr(panel, "version_badge", None)
            if badge_zfy:
                try:
                    badge_zfy.configure(text="ZFY")
                    badge_zfy.grid() if is_zfy else badge_zfy.grid_remove()
                except Exception as exc:
                    print(f"[Sidebar] ZFY badge error on {panel_attr}: {exc}")

            # ── ZLF badge (shows the sub-model name) ──
            badge_zlf = getattr(panel, "zlf_badge", None)
            if badge_zlf:
                try:
                    badge_zlf.configure(text=label)
                    badge_zlf.grid() if is_zlf_any else badge_zlf.grid_remove()
                except Exception as exc:
                    print(f"[Sidebar] ZLF badge error on {panel_attr}: {exc}")

    # =========================================================================
    # RESPONSIVE RESIZE
    # =========================================================================

    def _on_window_configure(self, event):
        if event.widget is not self.master:
            return

        try:
            current_state = self.master.state()
            if current_state == "iconic":
                self._last_state = current_state
                return
        except Exception:
            current_state = self._last_state

        if current_state != self._last_state:
            self._last_state = current_state
            if self._resize_job:
                self.after_cancel(self._resize_job)
                self._resize_job = None
            self._apply_resize()
            return

        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(16, self._apply_resize)

    def _apply_resize(self):
        self._resize_job = None
        win_w = self.master.winfo_width()

        if self._last_win_w is not None and abs(win_w - self._last_win_w) < 2:
            return
        self._last_win_w = win_w

        if win_w < COLLAPSE_BREAKPT:
            if not self.is_collapsed:
                self._collapse()
        else:
            if self.is_collapsed:
                self._expand(win_w)
            else:
                target = max(EXPANDED_MIN, min(EXPANDED_MAX, int(win_w * WIDTH_RATIO)))
                self.configure(width=target)

    def _collapse(self):
        if self.is_collapsed:
            return
        self.is_collapsed = True
        self.configure(width=COLLAPSED_WIDTH)

        for btn, _label in self._btn_meta:
            btn.configure(text="", anchor="center", width=COLLAPSED_WIDTH - 16)

        self.logo_frame.grid_remove()
        self.check_frame.grid_remove()

    def _expand(self, win_w=None):
        if not self.is_collapsed:
            return
        self.is_collapsed = False

        if win_w is None:
            win_w = self.master.winfo_width()
        target = max(EXPANDED_MIN, min(EXPANDED_MAX, int(win_w * WIDTH_RATIO)))

        self.logo_frame.grid()
        self.check_frame.grid()

        for btn, label in self._btn_meta:
            btn.configure(text=label, anchor="w", width=0)

        self.configure(width=target)

    # =========================================================================
    # BUTTON FACTORY & ACTIVE STATE
    # =========================================================================

    def _make_nav_button(self, text, icon, active=False):
        return ctk.CTkButton(
            self.nav_frame,
            text=text,
            image=icon,
            compound="left",
            height=38,
            corner_radius=8,
            border_width=0,
            fg_color=ACTIVE_COLOR if active else "transparent",
            hover_color=ACTIVE_COLOR,
            text_color=ACTIVE_TXT if active else INACTIVE_TXT,
            anchor="w",
        )

    def _set_active_button(self, btn):
        for b in self.buttons:
            active = (b is btn)
            b.configure(
                fg_color=ACTIVE_COLOR if active else "transparent",
                text_color=ACTIVE_TXT if active else INACTIVE_TXT,
            )
        self.active_button = btn

    # =========================================================================
    # ICON LOADING
    # =========================================================================

    def _load_icons(self):
        icon_map = {
            "new":     "icons/new.png",
            "sidebar": "icons/sidebar.png",
            "review":  "icons/review.png",
        }
        icons = {}
        for key, rel_path in icon_map.items():
            path = get_resource_path(rel_path)
            try:
                if path.exists():
                    icons[key] = ctk.CTkImage(Image.open(path), size=(15, 15))
                else:
                    print(f"[Sidebar] Icon not found: {path}")
            except Exception as exc:
                print(f"[Sidebar] Failed to load icon '{key}': {exc}")
        return icons