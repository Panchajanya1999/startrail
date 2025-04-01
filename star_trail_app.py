import os
import sys
import cv2
import numpy as np
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import rawpy
import imageio
import traceback
import platform

# Try to import the Sun Valley theme
try:
    import sv_ttk
except ImportError:
    print("Sun Valley theme not available. Using default theme.")
    sv_ttk = None

# Color scheme for light/dark modes
COLOR_SCHEME = {
    "light": {
        "bg": "#f5f5f5",
        "fg": "#333333",
        "accent": "#0078d7",
        "accent_hover": "#005fa3",
        "success": "#5cb85c",
        "warning": "#f0ad4e",
        "error": "#d9534f",
        "border": "#e0e0e0"
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#f5f5f5",
        "accent": "#2b88d8",
        "accent_hover": "#5ca8e0",
        "success": "#5cb85c",
        "warning": "#f0ad4e",
        "error": "#d9534f",
        "border": "#444444"
    }
}

class ModernTooltip:
    """Modern-looking tooltip for widgets"""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        frame = ttk.Frame(self.tooltip_window, style="Tooltip.TFrame", padding=8)
        frame.pack()
        
        label = ttk.Label(frame, text=self.text, style="Tooltip.TLabel", wraplength=250)
        label.pack()
        
        # Show tooltip with animation
        self.tooltip_window.attributes("-alpha", 0.0)
        self.fade_in()
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def fade_in(self, alpha=0.0):
        if self.tooltip_window:
            if alpha < 1.0:
                self.tooltip_window.attributes("-alpha", alpha)
                self.widget.after(20, self.fade_in, alpha + 0.1)

class CustomNotification:
    """Modern toast-like notification system"""
    
    def __init__(self, parent, message, type_="info", duration=3000):
        self.parent = parent
        self.duration = duration
        
        # Create notification window
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        
        # Determine notification style based on type
        bg_color = "#333333"
        icon = "ℹ️"
        
        if type_ == "success":
            bg_color = "#4caf50"
            icon = "✅"
        elif type_ == "warning":
            bg_color = "#ff9800"
            icon = "⚠️"
        elif type_ == "error":
            bg_color = "#f44336"
            icon = "❌"
        
        # Create notification content
        frame = tk.Frame(self.window, bg=bg_color, padx=15, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        icon_label = tk.Label(frame, text=icon, bg=bg_color, fg="white", font=("", 16))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        message_label = tk.Label(frame, text=message, bg=bg_color, fg="white", font=("", 10), wraplength=250)
        message_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        close_btn = tk.Label(frame, text="✕", bg=bg_color, fg="white", cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=(10, 0))
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        
        # Position the notification in bottom right
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        x = screen_width - width - 20
        y = screen_height - height - 40
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Apply rounded corners if possible (Windows and macOS)
        if platform.system() == "Windows":
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(self.window.winfo_id())
                style = windll.user32.GetWindowLongW(hwnd, -16)
                style |= 0x00080000  # WS_EX_LAYERED
                windll.user32.SetWindowLongW(hwnd, -16, style)
            except Exception:
                pass
        
        # Show with animation
        self.window.deiconify()
        self.fade_in()
        
        # Schedule auto-close
        self.parent.after(self.duration, self.fade_out)
    
    def fade_in(self, alpha=0.0):
        if alpha < 1.0:
            self.window.attributes("-alpha", alpha)
            self.parent.after(20, self.fade_in, alpha + 0.1)
    
    def fade_out(self, alpha=1.0):
        if alpha > 0.0:
            self.window.attributes("-alpha", alpha)
            self.parent.after(20, self.fade_out, alpha - 0.1)
        else:
            self.destroy()
    
    def destroy(self):
        self.window.destroy()

class CustomSwitch(ttk.Checkbutton):
    """Modern toggle switch widget"""
    
    def __init__(self, master=None, **kwargs):
        # Store original command if provided
        self.original_command = kwargs.pop('command', None)
        
        # Initialize the checkbutton
        super().__init__(master, style="Switch.TCheckbutton", **kwargs)


class StarTrailGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Star Trail Generator v1.0.2")
        self.root.geometry("1920x1080")
        self.root.minsize(800, 600)
        
        self.image_folder = ""
        self.image_files = []
        self.output_folder = ""
        self.final_image = None
        self.preview_image = None
        
        # Initialize variables
        self.use_camera_wb = tk.BooleanVar(value=False)
        self.no_auto_bright = tk.BooleanVar(value=True)
        self.resize_method_var = tk.StringVar(value="first")
        self.dark_mode = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")
        self.generate_gif = tk.BooleanVar(value=False)
        
        # Set icon (placeholder)
        if platform.system() == "Windows":
            try:
                self.root.iconbitmap("icon.ico")
            except:
                pass
        
        # Apply theme
        if sv_ttk:
            sv_ttk.set_theme("light")
        self.theme = "light"
        
        # Bind theme toggle
        self.dark_mode.trace_add("write", self.toggle_theme)
        
        # Set up the GUI
        self.setup_styles()
        self.create_menu()
        self.setup_ui()
        
        # Initialize control states based on the toggle
        self.update_gif_controls()
    
    def update_gif_controls(self, *args):
        """Enable or disable GIF-related controls based on toggle state"""
        if self.generate_gif.get():
            self.gif_filename.config(state="normal")
            self.gif_duration.config(state="normal")
        else:
            self.gif_filename.config(state="disabled")
            self.gif_duration.config(state="disabled")
    
    def toggle_theme(self, *args):
        """Toggle between light and dark themes"""
        if not sv_ttk:
            return
            
        if self.dark_mode.get():
            sv_ttk.set_theme("dark")
            self.theme = "dark"
        else:
            sv_ttk.set_theme("light")
            self.theme = "light"
    
    def setup_styles(self):
        """Configure custom styles for widgets"""
        style = ttk.Style()
        
        # Title label style
        style.configure("Title.TLabel", font=("", 14, "bold"))
        
        # Bold label style
        style.configure("Bold.TLabel", font=("", 10, "bold"))
        
        # Subtitle style
        style.configure("Subtitle.TLabel", font=("", 11))
        
        # Accent button style
        style.configure("Accent.TButton", font=("", 10))
        
        # Card frame style
        style.configure("Card.TFrame", borderwidth=1, relief="solid")
        
        # Image border style
        style.configure("ImageBorder.TFrame", borderwidth=1, relief="solid")
        
        # Tooltip styles
        style.configure("Tooltip.TFrame", background="#333333")
        style.configure("Tooltip.TLabel", background="#333333", foreground="white")
        
        # Custom switch style
        style.configure("Switch.TCheckbutton", indicatorsize=20)
        
        # Heading style
        style.configure("Heading.TLabel", font=("", 12, "bold"))
        
        # Info panel style
        style.configure("Info.TFrame", borderwidth=1, relief="solid")

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Input Folder", command=self.browse_folder, 
                             accelerator="Ctrl+O", compound=tk.LEFT)
        file_menu.add_command(label="Select Output Folder", command=self.browse_output, 
                             accelerator="Ctrl+S", compound=tk.LEFT)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy,
                             compound=tk.LEFT)
        
        # Process menu
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Process", menu=process_menu)
        process_menu.add_command(label="Generate Star Trail", command=self.process_images, 
                                accelerator="Ctrl+G", compound=tk.LEFT)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode, 
                                 compound=tk.LEFT)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about,
                             compound=tk.LEFT)
    
    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with app title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="Star Trail Generator", style="Title.TLabel").pack(side=tk.LEFT)
        
        # Create a notebook for tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Main tab
        main_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(main_tab, text="Main")
        
        # Options tab
        options_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(options_tab, text="Advanced Options")
        
        # ---- Main Tab Content ----
        # Folders card
        folder_card = ttk.Frame(main_tab, style="Card.TFrame", padding=15)
        folder_card.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(folder_card, text="Folders", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # Input folder row
        input_frame = ttk.Frame(folder_card)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Input Folder:").pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(input_frame)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        browse_btn = ttk.Button(input_frame, text="Browse...", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT)
        ModernTooltip(browse_btn, "Select folder containing your star images")
        
        # Format note
        format_frame = ttk.Frame(folder_card)
        format_frame.pack(fill=tk.X, pady=5)
        ttk.Label(format_frame, text="Supported formats:", font=("Default", 9)).pack(side=tk.LEFT)
        ttk.Label(format_frame, text=" JPG, JPEG, PNG, TIF, TIFF, ARW (Sony RAW)", 
                 font=("Default", 9, "italic")).pack(side=tk.LEFT)
        
        # Output folder row
        output_frame = ttk.Frame(folder_card)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Output Folder:").pack(side=tk.LEFT)
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        browse_output_btn = ttk.Button(output_frame, text="Browse...", command=self.browse_output)
        browse_output_btn.pack(side=tk.LEFT)
        ModernTooltip(browse_output_btn, "Select where to save your star trail images")

        # Output filenames card
        output_file_card = ttk.Frame(main_tab, style="Card.TFrame", padding=15)
        output_file_card.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(output_file_card, text="Output Files", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # Image filename row
        image_file_frame = ttk.Frame(output_file_card)
        image_file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(image_file_frame, text="Image Filename:").pack(side=tk.LEFT)
        self.image_filename = ttk.Entry(image_file_frame)
        self.image_filename.insert(0, "star_trail.jpg")
        self.image_filename.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # GIF filename row
        gif_file_frame = ttk.Frame(output_file_card)
        gif_file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(gif_file_frame, text="GIF Filename:").pack(side=tk.LEFT)
        self.gif_filename = ttk.Entry(gif_file_frame)
        self.gif_filename.insert(0, "star_trail_timelapse.gif")
        self.gif_filename.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Preview area card
        preview_card = ttk.Frame(main_tab, style="Card.TFrame", padding=15)
        preview_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        ttk.Label(preview_card, text="Preview", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.canvas = tk.Canvas(preview_card, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Process buttons and progress
        button_frame = ttk.Frame(main_tab)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress = ttk.Progressbar(button_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.process_button = ttk.Button(button_frame, text="Generate Star Trail", 
                                        command=self.process_images, style="Accent.TButton")
        self.process_button.pack(side=tk.RIGHT, padx=5)
        ModernTooltip(self.process_button, "Start processing images to create star trails")
        
        # Status bar
        status_bar = ttk.Label(main_tab, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ---- Options Tab Content ----
        options_frame = ttk.Frame(options_tab)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Options in a grid layout
        left_column = ttk.Frame(options_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_column = ttk.Frame(options_frame)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Left column - GIF Options card
        gif_card = ttk.Frame(left_column, style="Card.TFrame", padding=15)
        gif_card.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(gif_card, text="GIF Options", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # GIF Generation Toggle
        gif_toggle = CustomSwitch(gif_card, text="Generate GIF", variable=self.generate_gif)
        gif_toggle.pack(anchor=tk.W, pady=5)
        ModernTooltip(gif_toggle, "Enable/disable GIF creation [consumes high RAM]")

        # Bind trace to update control states
        self.generate_gif.trace_add("write", self.update_gif_controls)

        # GIF Duration
        duration_frame = ttk.Frame(gif_card)
        duration_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duration_frame, text="GIF Duration (ms):").pack(side=tk.LEFT)
        self.gif_duration = ttk.Spinbox(duration_frame, from_=10, to=1000, increment=10, width=5)
        self.gif_duration.insert(0, "50")
        self.gif_duration.pack(side=tk.LEFT, padx=10)
        
        # Left column - Image Size Options card
        size_card = ttk.Frame(left_column, style="Card.TFrame", padding=15)
        size_card.pack(fill=tk.X)
        
        ttk.Label(size_card, text="Image Size Options", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # Size options
        size_options_frame = ttk.Frame(size_card)
        size_options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(size_options_frame, text="Use First Image Size", 
                       variable=self.resize_method_var, value="first").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(size_options_frame, text="Use Smallest Image", 
                       variable=self.resize_method_var, value="smallest").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(size_options_frame, text="Use Largest Image", 
                       variable=self.resize_method_var, value="largest").pack(anchor=tk.W, pady=2)
        
        ttk.Label(size_card, text="Choose how to handle images with different dimensions",
                wraplength=300).pack(anchor=tk.W, pady=(5, 0))
        
        # Right column - RAW processing card
        raw_card = ttk.Frame(right_column, style="Card.TFrame", padding=15)
        raw_card.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(raw_card, text="RAW Processing Options", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        wb_switch = CustomSwitch(raw_card, text="Use Camera White Balance", variable=self.use_camera_wb)
        wb_switch.pack(anchor=tk.W, pady=5)
        
        bright_switch = CustomSwitch(raw_card, text="No Auto Brightness", variable=self.no_auto_bright)
        bright_switch.pack(anchor=tk.W, pady=5)
        
        ttk.Label(raw_card, text="These settings control how RAW files (ARW) are processed. Adjust them to get the best results for your specific camera and photography conditions.",
                wraplength=300).pack(anchor=tk.W, pady=(5, 0))
        
        # Right column - About card
        about_card = ttk.Frame(right_column, style="Card.TFrame", padding=15)
        about_card.pack(fill=tk.X)
        
        ttk.Label(about_card, text="About", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        about_text = """Star Trail Generator automatically combines multiple night sky images to create stunning star trail effects.

The application works by finding the brightest pixel values across your image sequence, revealing the movement of stars due to Earth's rotation.

For best results, use a tripod and consistent camera settings for all source images."""
        
        ttk.Label(about_card, text=about_text, wraplength=300).pack(anchor=tk.W)
    
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Star Trail Generator")
        about_window.geometry("590x490")
        about_window.resizable(False, False)
        
        # Center on parent
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Content
        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # App icon (placeholder)
        app_icon_label = ttk.Label(frame, text="🌌", font=("", 48))
        app_icon_label.pack(pady=(10, 0))
        
        ttk.Label(frame, text="Star Trail Generator", style="Title.TLabel").pack(pady=5)
        ttk.Label(frame, text="Copyright 2025 Panchajanya1999").pack()
        ttk.Label(frame, text="Version 1.0.0").pack()
        
        # Description
        desc_frame = ttk.Frame(frame, style="Card.TFrame", padding=15)
        desc_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(desc_frame, text="A professional tool for creating beautiful star trail images and timelapse GIFs from a series of night sky photographs.", 
                 wraplength=380, justify=tk.CENTER).pack()
        
        # Technologies
        tech_frame = ttk.Frame(frame)
        tech_frame.pack(fill=tk.X)
        
        ttk.Label(tech_frame, text="Technologies:", style="Bold.TLabel").pack(anchor=tk.W)
        ttk.Label(tech_frame, text="• OpenCV for image processing\n• Rawpy for RAW file support\n• Python tkinter for the interface").pack(anchor=tk.W, padx=15)
        
        # Close button with accent style
        ttk.Button(frame, text="Close", command=about_window.destroy, style="Accent.TButton").pack(pady=15)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing images")
        if folder:
            self.image_folder = folder
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            self.output_folder = folder
            
            # Count images in folder
            self.image_files = sorted([os.path.join(folder, f) for f in os.listdir(folder) 
                                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.arw'))])
            self.status_var.set(f"Found {len(self.image_files)} images in selected folder")
            
            # Show notification
            if len(self.image_files) > 0:
                CustomNotification(self.root, f"Found {len(self.image_files)} images", "info")
            else:
                CustomNotification(self.root, "No supported images found in folder", "warning")
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder = folder
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            CustomNotification(self.root, f"Output folder set", "info")
    
    def update_preview(self, img):
        if img is None:
            return
            
        try:
            # Make a copy to avoid any threading issues
            img = img.copy()
            
            # Resize for preview while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Use default size if canvas not yet sized
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 640
                canvas_height = 480
            
            img_height, img_width = img.shape[:2]
            
            # Calculate scaling factor
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # Resize image for display
            if scale < 1:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            else:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # Convert from BGR to RGB for PIL
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage
            pil_img = Image.fromarray(rgb_image)
            self.preview_image = ImageTk.PhotoImage(image=pil_img)
            
            # Clear canvas and display new image
            self.canvas.delete("all")
            
            # Center the image
            x_pos = (canvas_width - self.preview_image.width()) // 2
            y_pos = (canvas_height - self.preview_image.height()) // 2
            
            self.canvas.create_image(x_pos, y_pos, anchor=tk.NW, image=self.preview_image)
            
        except Exception as e:
            print(f"Preview update error: {str(e)}")
            # Don't let preview errors crash the application
    
    def process_images(self):
        if not self.image_files:
            CustomNotification(self.root, "No images selected. Please select a folder with images.", "error")
            return
        
        if not self.output_folder:
            CustomNotification(self.root, "No output folder selected.", "error")
            return
        
        # Disable button during processing
        self.process_button.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        # Start processing in a separate thread
        threading.Thread(target=self._process_thread, daemon=True).start()
    
    def read_image(self, img_path):
        """Read an image file, handling both regular formats and ARW raw files"""
        try:
            if img_path.lower().endswith('.arw'):
                # Handle ARW (Sony RAW) file
                self.status_var.set(f"Processing RAW file: {os.path.basename(img_path)}")
                with rawpy.imread(img_path) as raw:
                    # Get RAW processing options from the UI
                    use_camera_wb = self.use_camera_wb.get()
                    no_auto_bright = self.no_auto_bright.get()
                    
                    # Process the raw data to get an RGB image with user-specified parameters
                    rgb = raw.postprocess(
                        use_camera_wb=use_camera_wb,
                        half_size=False,  # Full resolution
                        no_auto_bright=no_auto_bright,
                        bright=1.0,  # Default brightness
                        highlight_mode=rawpy.HighlightMode.Clip  # Preserve highlights
                    )
                    # Convert from RGB to BGR for OpenCV compatibility
                    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR).astype(np.float32)
            else:
                # Handle regular image formats
                img = cv2.imread(img_path)
                if img is None:
                    raise IOError(f"Could not read image file: {img_path}")
                return img.astype(np.float32)
        except Exception as e:
            self.status_var.set(f"Error reading {os.path.basename(img_path)}: {str(e)}")
            traceback.print_exc()
            # Return a black image of default size as fallback
            return np.zeros((1080, 1920, 3), dtype=np.float32)

    def _process_thread(self):
        try:
            self.status_var.set("Reading images...")
            
            if not self.image_files:
                raise ValueError("No image files found in the selected folder")
                
            # Read the first image as base
            base_img = self.read_image(self.image_files[0])
            self.progress['value'] = 1
            
            # Update preview with first image
            first_img_preview = base_img.copy().astype(np.uint8)
            self.root.after(0, lambda: self.update_preview(first_img_preview))
            self.root.update_idletasks()
            
            # Stack images using maximum pixel value
            total_images = len(self.image_files)
            for i, img_path in enumerate(self.image_files[1:], 1):
                try:
                    img = self.read_image(img_path)
                    base_img = np.maximum(base_img, img)  # Keep the brightest pixels
                    
                    # Update progress bar
                    progress_value = int((i / total_images) * 100)
                    self.progress['value'] = progress_value
                    self.status_var.set(f"Processing image {i}/{total_images} ({progress_value}%)")
                    
                    # Update preview periodically (every 5 images or final image)
                    if i % 5 == 0 or i == len(self.image_files) - 1:
                        current_preview = np.uint8(base_img.copy())
                        self.root.after(0, lambda img=current_preview: self.update_preview(img))
                    
                    self.root.update_idletasks()
                except Exception as e:
                    # Log the error but continue processing other images
                    error_msg = f"Error processing {os.path.basename(img_path)}: {str(e)}"
                    print(error_msg)
                    self.status_var.set(error_msg)
                    traceback.print_exc()
            
            # Convert back to 8-bit image format
            self.final_image = np.uint8(base_img)
            
            # Save the output image
            output_path = os.path.join(self.output_folder, self.image_filename.get())
            cv2.imwrite(output_path, self.final_image)
            
            # Update preview with final image
            self.root.after(0, lambda: self.update_preview(self.final_image))
            
            # Create GIF if enabled
            if self.generate_gif.get():
                self.status_var.set("Creating GIF...")
                gif_path = os.path.join(self.output_folder, self.gif_filename.get())
                
                try:
                    duration = int(self.gif_duration.get())
                except ValueError:
                    duration = 50  # Default if invalid input
                    
                # Open all images with PIL and create GIF
                pil_images = []
                for img_path in self.image_files:
                    try:
                        pil_images.append(Image.open(img_path))
                    except Exception as e:
                        self.status_var.set(f"Warning: Could not open {os.path.basename(img_path)}: {str(e)}")
                        continue
                
                if pil_images:
                    pil_images[0].save(
                        gif_path, 
                        save_all=True, 
                        append_images=pil_images[1:], 
                        duration=duration, 
                        loop=0
                    )
                    
                    self.status_var.set(f"Completed! Files saved to {self.output_folder}")
                    CustomNotification(self.root, f"Star trail and GIF created successfully!", "success")
                else:
                    self.status_var.set("Error: No valid images found for GIF creation")
                    CustomNotification(self.root, "Could not create GIF: No valid images found", "error")
            else:
                # Skip GIF creation
                self.status_var.set(f"Completed! Star trail image saved to {self.output_folder}")
                CustomNotification(self.root, f"Star trail image created successfully!", "success")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            CustomNotification(self.root, f"An error occurred: {str(e)}", "error")
        
        finally:
            # Re-enable button
            self.process_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    
    # Set theme first if available
    if sv_ttk:
        sv_ttk.set_theme("light")
    
    # Create app
    app = StarTrailGenerator(root)
    
    # Set window icon (if available)
    if platform.system() == "Windows":
        try:
            root.iconbitmap("icon.ico")
        except:
            pass
    
    root.mainloop()

if __name__ == "__main__":
    main()
