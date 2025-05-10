# Image Montage and Color Analyzer

This project provides a two-step pipeline to process a collection of images:
1.  **Image Processing & Montage Creation**: Resizes images, generates one or more montages, and creates a JSON metadata file.
2.  **Dominant Color Analysis**: Analyzes the resized images to find their most frequent color and saves this information to a new JSON file.

## Table of Contents

- [Image Montage and Color Analyzer](#image-montage-and-color-analyzer)
  - [Table of Contents](#table-of-contents)
  - [Folder Structure](#folder-structure)
  - [Setup](#setup)
    - [Prerequisites](#prerequisites)
    - [Environment Setup](#environment-setup)
  - [Usage](#usage)
    - [Step 1: Image Processing and Montage Creation (`image_processor.py`)](#step-1-image-processing-and-montage-creation-image_processorpy)
    - [Step 2: Dominant Color Analysis (`color_analyzer.py`)](#step-2-dominant-color-analysis-color_analyzerpy)
  - [Script Details](#script-details)
    - [`image_processor.py`](#image_processorpy)
    - [`color_analyzer.py`](#color_analyzerpy)

## Folder Structure

It's recommended to organize your project as follows:

```
your_project_root/
├── images/                   # Directory for your original input images
├── output/                   # Default output directory for processed files
│   ├── images/               # Resized images (e.g., 128x128)
│   ├── montage_0.png         # First montage image
│   ├── montage_1.png         # Second montage image (and so on)
│   ├── montage_metadata.json # JSON metadata for all images and montages
│   └── images_color_rgb.json # JSON with dominant colors for each image
├── image_processor.py        # Script for resizing, montage creation, and metadata
├── color_analyzer.py         # Script for dominant color analysis
└── README.md                 # This file
```

## Setup

### Prerequisites

*   [Conda](https://docs.conda.io/en/latest/miniconda.html) (or Anaconda) for environment management.
*   Python (the scripts are tested with Python 3.9).

### Environment Setup

1.  **Create a new Conda environment:**
    Open your terminal and run:
    ```bash
    conda create -n tsne python=3.9 -y
    ```

2.  **Activate the environment:**
    ```bash
    conda activate tsne
    ```

3.  **Install necessary libraries:**
    The primary dependency is Pillow (PIL Fork) for image manipulation.
    ```bash
    conda install -n tsne pillow -y
    ```
    Alternatively, after activating the environment, you can use pip:
    ```bash
    pip install Pillow
    ```

## Usage

Ensure your `tsne` conda environment is activated before running the scripts.

### Step 1: Image Processing and Montage Creation (`image_processor.py`)

This script takes a folder of your original images, resizes them, creates montages, and generates a `montage_metadata.json` file.

**Command:**

```bash
python image_processor.py --input_dir <path_to_original_images> --output_dir <path_to_output_directory> [options]
```

**Example (based on your usage):**

If your original images are in a folder named `images` within your project root, and you want the output to go into a folder named `output`:

```bash
python image_processor.py --input_dir images --output_dir output
```

**Optional Arguments for `image_processor.py`:**

*   `--montage_cols`: Number of columns in the montage grid (default: 15).
*   `--montage_rows`: Number of rows in the montage grid (default: 15).
*   `--img_width`: Target width for resized images (default: 128).
*   `--img_height`: Target height for resized images (default: 128).

Example with custom options:
```bash
python image_processor.py --input_dir images --output_dir output --montage_cols 10 --montage_rows 10 --img_width 64 --img_height 64
```

This will create:
*   `<path_to_output_directory>/images/` (with resized images)
*   `<path_to_output_directory>/montage_N.png` (montage files)
*   `<path_to_output_directory>/montage_metadata.json`

### Step 2: Dominant Color Analysis (`color_analyzer.py`)

This script uses the resized images and the `montage_metadata.json` (produced by `image_processor.py`) to calculate the most frequent color in each image. It saves this information into a new JSON file.

**Command:**

```bash
python color_analyzer.py --resized_images_dir <path_to_resized_images_folder> --metadata_json <path_to_metadata_file> [options]
```

**Example (based on your usage):**

Assuming the output from Step 1 was to the `output` directory:

```bash
python color_analyzer.py --resized_images_dir output/images --metadata_json output/montage_metadata.json
```

**Optional Arguments for `color_analyzer.py`:**

*   `--output_json`: Name for the output JSON file storing dominant colors (default: `images_color_rgb.json`). This file will be saved in the same directory as the `--metadata_json` file.

Example specifying output file name:
```bash
python color_analyzer.py --resized_images_dir output/images --metadata_json output/montage_metadata.json --output_json dominant_colors.json
```

This will create:
*   `<directory_of_metadata_json>/images_color_rgb.json` (or your specified `--output_json` name).
    The structure of this file is a list of objects:
    ```json
    [
      {
        "image": "original_image_filename.jpg",
        "x": R_value,
        "y": G_value,
        "z": B_value
      },
      ...
    ]
    ```

## Script Details

### `image_processor.py`

*   **Input**: A folder containing original images.
*   **Processing**:
    *   Reads image files (PNG, JPG, JPEG, BMP, GIF, TIFF).
    *   Resizes each image to a specified resolution (default 128x128 pixels).
    *   Saves resized images into a subfolder (default `images`) within the output directory.
    *   Generates one or more montage images from the resized images. If the number of images exceeds the capacity of a single montage grid (default 15x15), multiple montage files (`montage_0.png`, `montage_1.png`, etc.) are created.
    *   The last montage file's height is adjusted if it's not fully populated.
*   **Output**:
    *   Resized images in the specified subfolder.
    *   Montage image(s).
    *   A `montage_metadata.json` file containing details for each image: original path, resized path, montage name, and its index/position within the montage.

### `color_analyzer.py`

*   **Input**:
    *   The directory containing the resized images (created by `image_processor.py`).
    *   The `montage_metadata.json` file (created by `image_processor.py`).
*   **Processing**:
    *   Reads the list of unique resized images from the metadata JSON.
    *   For each unique resized image, it calculates the most frequent (dominant) color.
    *   It maps the original image filename to its dominant RGB color.
*   **Output**:
    *   A JSON file (default `images_color_rgb.json`) containing a list of dictionaries. Each dictionary holds the original image filename and its dominant color as `{"image": "name.jpg", "x": R, "y": G, "z": B}`.
