import customtkinter as ctk
import sys
import os
from pathlib import Path
import qrcode
from PIL import Image

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return Path(base_path) / relative_path

# -------------------- GLOBAL SETTINGS ----------------
BG_MAIN = "#0f0f0f"
WHITE = "#ffffff"
GRAPH_CONTAINER = "#1B1B1B"
GOOD_COLOR = "#2563eb"   

# -------------------- REVIEW PANEL ----------------
class ReviewPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color=BG_MAIN)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_content()

    # ---------------- HEADER ----------------
    def _create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=BG_MAIN)
        header_frame.grid(row=0, column=0, padx=30, pady=(40, 15), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="Review Zeofy",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, sticky="w")

    # ---------------- CONTENT ----------------
    def _create_content(self):
        content_frame = ctk.CTkFrame(self, fg_color=BG_MAIN)
        content_frame.grid(row=1, column=0, padx=30, pady=(10, 30), sticky="nsew")
        
        # Configure grid: 2 columns - About wide, QR narrow
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)  # About (wide, flexible)
        content_frame.grid_columnconfigure(1, weight=0, minsize=350)  # QR (narrow, fixed)
        
        # ================= INFO CONTAINER (COLUMN 0 - LEFT) =================
        self.infoContainer = ctk.CTkFrame(
            content_frame,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.infoContainer.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Info content (About This Survey)
        self._create_info_content()
        
        # ================= QR CODE CONTAINER (COLUMN 1 - RIGHT) =================
        self.qrcodeContainer = ctk.CTkFrame(
            content_frame,
            fg_color=GRAPH_CONTAINER,
            corner_radius=10
        )
        self.qrcodeContainer.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
        # QR Code content
        self._create_qr_code_content()
    
    def _create_qr_code_content(self):
        # Main container for all QR content - NO PADDING for row 2 to reach edges
        qr_content = ctk.CTkFrame(self.qrcodeContainer, fg_color="transparent")
        qr_content.pack(fill="both", expand=True)
        
        # Configure grid: 2 rows
        qr_content.grid_rowconfigure(0, weight=1)  # Row 1: QR + Button
        qr_content.grid_rowconfigure(1, weight=1)  # Row 2: Blank (full width)
        qr_content.grid_columnconfigure(0, weight=1)
        
        # ========== ROW CONTAINER 1: QR Code + Button ==========
        row_container1 = ctk.CTkFrame(qr_content, fg_color="transparent")
        row_container1.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        
        # QR Code (no title)
        self._create_qr_code(row_container1)
        
        # Caption
        qr_caption = ctk.CTkLabel(
            row_container1,
            text="Scan the QR code to access the survey",
            font=ctk.CTkFont(size=12),
            text_color="#9ca3af"
        )
        qr_caption.pack(pady=(10, 15))
        
        # Survey button
        self.survey_button = ctk.CTkButton(
            row_container1,
            text="Open Survey",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=GOOD_COLOR,
            hover_color="#437cf6",
            text_color=WHITE,
            height=40,
            corner_radius=8,
            command=self._open_survey_link
        )
        self.survey_button.pack(fill="x")
        
        # ========== ROW CONTAINER 2: Full Width (attached to edges) ==========
        row_container2 = ctk.CTkFrame(qr_content, fg_color=BG_MAIN, corner_radius=0)
        row_container2.grid(row=1, column=0, sticky="nsew")  # No padding - reaches edges!
        # Leave blank as requested
    
    def _create_info_content(self):
        # Container for all info content
        info_content = ctk.CTkFrame(self.infoContainer, fg_color="transparent")
        info_content.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Configure grid for better positioning
        info_content.grid_rowconfigure(0, weight=0)  # Title row
        info_content.grid_rowconfigure(1, weight=1)  # Content row
        info_content.grid_columnconfigure(0, weight=1)
        
        # Title - positioned at top left
        info_title = ctk.CTkLabel(
            info_content,
            text="About This Survey",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=WHITE,
            anchor="w"  # Align text to left
        )
        info_title.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 20))
        
        # Full paragraph text (3 paragraphs)
        paragraph_text = (
            "Thank you for taking the time to participate in our survey. Your feedback is invaluable in helping us understand how Zeofy is being used and where we can make improvements. This survey is designed to gather insights about your experience with the application, including its features, usability, and overall performance.\n\n"
            
            "The survey will take approximately 3-5 minutes to complete. We ask that you answer all questions honestly and thoroughly. Your responses will help us identify areas where Zeofy excels and areas where we need to focus our development efforts. Whether you're a new user or have been using Zeofy for a while, your perspective is important to us.\n\n"
            
            "Your privacy is our priority. All responses are completely anonymous and will be used solely for the purpose of improving the Zeofy application. We do not collect any personally identifiable information through this survey. The data gathered will be analyzed to inform future updates, new features, and enhancements to make Zeofy better for everyone. Thank you for helping us build a better product!"
        )
        
        # Create textbox for paragraph with responsive wrapping
        paragraph_textbox = ctk.CTkTextbox(
            info_content,
            fg_color="#1B1B1B",
            text_color="#d1d5db",
            font=ctk.CTkFont(size=13),
            wrap="word",
            activate_scrollbars=False
        )
        paragraph_textbox.grid(row=1, column=0, sticky="nsew")
        
        # Insert text and make read-only
        paragraph_textbox.insert("1.0", paragraph_text)
        paragraph_textbox.configure(state="disabled")
    
    def _create_qr_code(self, parent):
        try:
            # Read survey link from config file
            survey_link = self._get_survey_link()
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(survey_link)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color=WHITE, back_color=GRAPH_CONTAINER)
            qr_image = qr_image.resize((220, 220))  # QR code size
            
            # Convert PIL Image to CTkImage (proper way for CustomTkinter)
            ctk_image = ctk.CTkImage(
                light_image=qr_image,
                dark_image=qr_image,
                size=(220, 220)
            )
            
            # Display in label
            qr_label = ctk.CTkLabel(
                parent,
                image=ctk_image,
                text=""
            )
            qr_label.pack()
            
        except Exception as e:
            # Fallback if QR generation fails
            error_label = ctk.CTkLabel(
                parent,
                text="QR Code\nUnavailable",
                font=ctk.CTkFont(size=12),
                text_color="#6b7280"
            )
            error_label.pack(pady=30)
            print(f"QR Code generation error: {e}")
    
    def _get_survey_link(self):
        default_link = "https://forms.gle/dm8mAHxDsmfp1iTZA"
        try:
            # get_resource_path resolves to _MEIPASS when frozen, cwd otherwise
            bundled_path = get_resource_path("survey_link.txt")
            with open(bundled_path, "r") as f:
                link = f.read().strip()
                return link if link else default_link
        except FileNotFoundError:
            # Dev fallback: create file next to the script
            try:
                with open("survey_link.txt", "w") as f:
                    f.write(default_link)
            except Exception:
                pass
            return default_link
    
    def _open_survey_link(self):
        import webbrowser
        survey_link = self._get_survey_link()
        webbrowser.open(survey_link)

# --- Add testing block so you can run this script standalone ---
if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("1000x600")
    panel = ReviewPanel(app)
    panel.pack(fill="both", expand=True)
    app.mainloop()