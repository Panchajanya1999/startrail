# Star Trail Generator

A user-friendly desktop application for creating beautiful star trail images and timelapse GIFs from a series of night sky photographs.

![Star Trail Home Page](https://storage.panchajanya.dev/startrail/ssnewi.png)
![Star Trail Advanced Page](https://storage.panchajanya.dev/startrail/ssnewii.png)

## Features

- **Image Stacking:** Automatically combines multiple images to create stunning star trail effects
- **GIF Creation:** Generates timelapses showing the movement of stars across the night sky
- **Live Preview:** Watch your star trails form during processing
- **RAW Support:** Processes Sony ARW (RAW) files with customizable processing options
- **Simple Interface:** Easy-to-use GUI for photographers of all skill levels
- **Cross-Platform:** Works on Windows, macOS, and Linux

## Download & Installation

### Latest Release

Download the latest pre-built application for your platform from the [Releases](https://github.com/yourusername/star-trail-generator/releases) page.

### Windows
1. Download the `star-trail-generator-windows.zip` file
2. Extract the ZIP file to a location of your choice
3. Run `StarTrailGenerator_Windows.exe`

### macOS
1. Download the `star-trail-generator-macos.zip` file
2. Extract the ZIP file
3. Move `StarTrailGenerator_macOS.app` to your Applications folder
4. Right-click and select "Open" the first time you run it (to bypass Gatekeeper)

### Linux
1. Download the `star-trail-generator-linux.zip` file
2. Extract the archive
3. Make the executable file runnable: `chmod +x StarTrailGenerator_Linux`
4. Run the application: `./StarTrailGenerator_Linux`

## Usage Guide

### Basic Workflow

1. **Select Input Folder:** Click "Browse..." to select the folder containing your night sky images
   - Supported formats: JPG, JPEG, PNG, TIF, TIFF, ARW (Sony RAW)
   - Images should be sorted in chronological order (file names should sort correctly)

2. **Choose Output Location:** 
   - By default, this will be the same as your input folder
   - You can change the output folder and file names for both the star trail image and GIF

3. **Adjust Options:**
   - Set the GIF duration (in milliseconds) to control playback speed
   - Configure RAW processing options:
     - Use Camera White Balance: Uses the white balance settings from your camera
     - No Auto Brightness: Disables automatic brightness adjustment for RAW files

4. **Generate:** Click "Generate Star Trail" to start processing
   - The progress bar will show completion percentage
   - Live preview will update to show your star trail forming
   - Final files will be saved to your selected output location

![Star Trail Result - I](https://storage.panchajanya.dev/startrail/star_trail.jpg)
Caption: A star trail image created using the Star Trail Generator (Sony A6700 + Sony PZ 16-50mm f/3.5-5.6 OSS | 16mm | f/3.5 | ISO 400 | 20s x 100)

![Star Trail Result - II](https://storage.panchajanya.dev/startrail/star_trails_adobe.jpg)
Caption: A star trail image (LR Edited) created using the Star Trail Generator (Sony A6700 + Sony PZ 16-50mm f/3.5-5.6 OSS | 16mm | f/3.5 | ISO 400 | 20s x 100)

### Tips for Best Results

- Use a tripod and remote shutter to ensure images align properly
- Set your camera to manual mode with consistent settings for all shots
- Take at least 30 images for smoother trails (100+ is ideal)
- For best star trails, use exposure times of 15-30 seconds per image
- Shoot on clear nights away from light pollution
- Follow the rule of 500: divide 500 by your focal length to get the maximum exposure time before star trails appear.
 [Rule of the 500](https://astrobackyard.com/the-500-rule/)

## Development

### Requirements

- Python 3.7 or newer
- Required packages: numpy, opencv-python, Pillow, pyinstaller
- Git for version control

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/star-trail-generator.git
   cd star-trail-generator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python star_trail_app.py
   ```

### Building from Source

You can build the application locally using PyInstaller:

```bash
pyinstaller star_trail_generator.spec
```

The packaged application will be created in the `dist` directory.

### Release Process

This project uses an automated CI/CD pipeline with GitHub Actions. To create a new release:

1. Make your changes and commit them to the repository

2. Use the release script to bump the version and create a tag:
   ```bash
   # For a patch version (e.g., 1.0.0 → 1.0.1)
   ./release.py --patch -m "Fixed preview rendering issues"
   
   # For a minor version (e.g., 1.0.1 → 1.1.0)
   ./release.py --minor -m "Added new color adjustment features"
   
   # For a major version (e.g., 1.1.0 → 2.0.0)
   ./release.py --major -m "Complete UI redesign"
   
   # Or specify a specific version
   ./release.py --version 1.2.3 -m "Custom version release"
   ```

3. Push the changes and tag:
   ```bash
   git push origin main
   git push origin v1.0.0  # Replace with your actual version tag
   ```

4. GitHub Actions will automatically:
   - Build the application for Windows, macOS, and Linux
   - Create a new release on GitHub
   - Attach the built executables to the release

## How It Works

The Star Trail Generator uses the "maximum pixel value" stacking method, which:

1. Reads each image in sequence
2. For each pixel position, keeps the brightest value seen across all images
3. This creates light trails showing the path of stars due to Earth's rotation
4. The final result shows star trails as circular arcs around the celestial pole

## Troubleshooting

**Images don't align properly:**
- Make sure your camera was on a stable tripod
- Wind, slight tripod movement, or lens focusing changes can cause misalignment

**Preview is slow or unresponsive:**
- Reduce the number of images or use smaller image resolutions
- Close other memory-intensive applications

**Application crashes during processing:**
- Try processing fewer images at once
- Ensure you have enough free memory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Happy stargazing!*

