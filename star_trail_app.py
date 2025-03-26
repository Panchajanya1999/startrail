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

class StarTrailGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Star Trail Generator")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        self.image_folder = ""
        self.image_files = []
        self.output_folder = ""
        self.final_image = None
        self.preview_image = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Set theme for better appearance
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add file format info to the title
        self.root.title("Star Trail Generator v1.0.0 - Supports JPG, PNG, TIF, ARW")
        
        # Set minimum size for better appearance
        self.root.minsize(850, 650)
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Image Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.folder_entry = ttk.Entry(input_frame, width=50)
        self.folder_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse...", command=self.browse_folder).grid(row=0, column=2, pady=5)
        
        # Format note
        format_frame = ttk.Frame(input_frame)
        format_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        ttk.Label(format_frame, text="Supported formats:", font=("Default", 9)).pack(side=tk.LEFT)
        ttk.Label(format_frame, text=" JPG, JPEG, PNG, TIF, TIFF, ARW (Sony RAW)", 
                 font=("Default", 9, "italic")).pack(side=tk.LEFT)
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.output_entry = ttk.Entry(output_frame, width=50)
        self.output_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).grid(row=0, column=2, pady=5)
        
        ttk.Label(output_frame, text="Image Filename:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.image_filename = ttk.Entry(output_frame, width=50)
        self.image_filename.insert(0, "star_trail.jpg")
        self.image_filename.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        ttk.Label(output_frame, text="GIF Filename:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.gif_filename = ttk.Entry(output_frame, width=50)
        self.gif_filename.insert(0, "star_trail_timelapse.gif")
        self.gif_filename.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, pady=5)
        
        # Row 0: GIF Duration
        ttk.Label(options_frame, text="GIF Duration (ms):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.gif_duration = ttk.Spinbox(options_frame, from_=10, to=1000, increment=10, width=5)
        self.gif_duration.insert(0, "50")
        self.gif_duration.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Row 1: RAW Processing Options
        ttk.Label(options_frame, text="RAW Processing:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        raw_options_frame = ttk.Frame(options_frame)
        raw_options_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.use_camera_wb = tk.BooleanVar(value=False)
        ttk.Checkbutton(raw_options_frame, text="Use Camera White Balance", 
                       variable=self.use_camera_wb).pack(side=tk.LEFT, padx=(0, 10))
        
        self.no_auto_bright = tk.BooleanVar(value=True)
        ttk.Checkbutton(raw_options_frame, text="No Auto Brightness", 
                       variable=self.no_auto_bright).pack(side=tk.LEFT)
        
        # Process buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.progress = ttk.Progressbar(button_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.process_button = ttk.Button(button_frame, text="Generate Star Trail", command=self.process_images)
        self.process_button.pack(side=tk.RIGHT, padx=5)
        
        # Preview area
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(preview_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
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
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder = folder
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
    
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
            messagebox.showerror("Error", "No images selected. Please select a folder with images.")
            return
        
        if not self.output_folder:
            messagebox.showerror("Error", "No output folder selected.")
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
            
            # Create GIF
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
                messagebox.showinfo("Success", f"Star trail image and GIF have been created successfully in {self.output_folder}")
            else:
                self.status_var.set("Error: No valid images found for GIF creation")
                messagebox.showerror("Error", "Could not create GIF: No valid images found")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            # Re-enable button
            self.process_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = StarTrailGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
