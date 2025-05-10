import os
import json
import argparse
from PIL import Image, UnidentifiedImageError
from collections import Counter

def get_dominant_color(image_path):
    """Opens an image and returns its most frequent color as an RGB tuple."""
    try:
        img = Image.open(image_path)
        # Ensure image is in RGB format to get (R, G, B) tuples
        img = img.convert('RGB')
        
        # Get colors and their counts. For performance, can optionally resize first,
        # but 128x128 should be manageable.
        # img_for_colors = img.resize((10,10)) # Optional: resize for faster getcolors
        colors = img.getcolors(img.size[0] * img.size[1]) # maxcolors = width * height
        
        if not colors:
            # This can happen if the image has too many colors for getcolors to handle
            # without quantization, or if it's a very simple image like pure black/white
            # where getcolors might behave unexpectedly if not returning a list.
            # A fallback could be to take the color of a central pixel or average.
            # For simplicity, let's try to get the color of the pixel at (0,0)
            print(f"Warning: getcolors() returned None for {os.path.basename(image_path)}. Trying pixel (0,0).")
            return img.getpixel((0,0))
            
        # Sort by count (descending) and get the color with the highest count
        dominant_color_tuple = max(colors, key=lambda item: item[0])[1]
        return dominant_color_tuple
    except FileNotFoundError:
        print(f"Error: Image file not found at '{image_path}'.")
        return None
    except UnidentifiedImageError:
        print(f"Error: Cannot identify image file '{image_path}'.")
        return None
    except Exception as e:
        print(f"Error processing image '{image_path}': {e}")
        return None

def analyze_and_save_dominant_colors(
    resized_images_base_folder: str, 
    metadata_json_path: str, 
    output_json_filename: str = "images_color_rgb.json"
):
    """
    Analyzes images listed in a metadata JSON to find their dominant color
    and saves the results to a new JSON file.

    Args:
        resized_images_base_folder: Path to the folder containing the subfolder with resized images.
                                     (e.g., your main output_dir from image_processor.py)
        metadata_json_path: Path to the montage_metadata.json file.
        output_json_filename: Name of the JSON file to save dominant color data.
    """

    if not os.path.isdir(resized_images_base_folder):
        print(f"Error: Base folder for resized images '{resized_images_base_folder}' not found.")
        return

    if not os.path.isfile(metadata_json_path):
        print(f"Error: Metadata JSON file '{metadata_json_path}' not found.")
        return

    try:
        with open(metadata_json_path, 'r') as f:
            metadata_list = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{metadata_json_path}'.")
        return
    except Exception as e:
        print(f"Error reading metadata file '{metadata_json_path}': {e}")
        return

    if not metadata_list:
        print("No image metadata found in the JSON file.")
        return
    
    # The image_processor.py saves resized images in a subfolder (default "images")
    # We need to find this subfolder. We can assume it's the one referenced in metadata, 
    # or more robustly, derive it if possible or require it as an arg.
    # For now, let's try to get it from the first metadata entry if paths are absolute.
    # A better approach might be to require the specific resized images folder path.

    # Let's assume the `resized_images_subfolder_name` is 'images' as per previous script default
    # Or, we could try to be smarter if paths in JSON are absolute.
    # For now, this script assumes the resized images are directly in a subfolder *of* `resized_images_base_folder`,
    # and that subfolder's name is part of the path in `resized_full_path` in the JSON.
    # To simplify, we will assume `resized_images_base_folder` IS the folder containing the actual image files.

    print(f"Analyzing images from folder: '{resized_images_base_folder}'")
    image_colors_map = {}
    processed_count = 0
    failed_count = 0

    # Using a set to avoid processing the same image multiple times if it appears in multiple montages
    # but the metadata points to the same resized file.
    unique_resized_filenames = set()
    for item in metadata_list:
        if "resized_filename" in item:
            unique_resized_filenames.add(item["resized_filename"])
        # If using full path, this would be:
        # if "resized_full_path" in item:
        #     unique_resized_full_paths.add(item["resized_full_path"])

    print(f"Found {len(unique_resized_filenames)} unique resized images in metadata to process.")

    for resized_filename in unique_resized_filenames:
        # Construct the full path to the resized image
        # Assumes `resized_images_base_folder` is the directory containing the resized images
        # (e.g., .../output_dir/images/)
        image_full_path = os.path.join(resized_images_base_folder, resized_filename)
        
        print(f"Processing: {resized_filename}")
        dominant_color = get_dominant_color(image_full_path)
        
        if dominant_color:
            # Convert to list [R, G, B] for JSON serialization if it's a tuple
            image_colors_map[resized_filename] = list(dominant_color) 
            processed_count += 1
        else:
            failed_count +=1
            image_colors_map[resized_filename] = None # Indicate failure for this image
    
    print(f"Successfully processed {processed_count} images. Failed to process {failed_count} images.")

    if not image_colors_map:
        print("No dominant colors were extracted. Output JSON will not be created.")
        return

    # Output JSON will be saved in the same directory as the metadata_json_path by default
    output_dir = os.path.dirname(metadata_json_path) 
    # Or, if we want it in `resized_images_base_folder`'s parent:
    # output_dir = os.path.dirname(resized_images_base_folder) # if images_base_folder is .../output/images
    
    # Let's save it in the same directory as the input metadata JSON, which is likely the main output folder.
    final_output_json_path = os.path.join(output_dir, output_json_filename)

    try:
        with open(final_output_json_path, 'w') as f:
            json.dump(image_colors_map, f, indent=4)
        print(f"Dominant color data saved to '{final_output_json_path}'")
    except Exception as e:
        print(f"Error saving output JSON to '{final_output_json_path}': {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Analyzes resized images to find their dominant color based on metadata, "
                    "and saves this information to a new JSON file."
    )
    parser.add_argument(
        "--resized_images_dir", 
        type=str, 
        required=True,
        help="Path to the directory containing the actual resized image files (e.g., output_folder/images)."
    )
    parser.add_argument(
        "--metadata_json", 
        type=str, 
        required=True,
        help="Path to the input montage_metadata.json file."
    )
    parser.add_argument(
        "--output_json", 
        type=str, 
        default="images_color_rgb.json", 
        help="Name for the output JSON file storing dominant colors (default: images_color_rgb.json). "
             "This file will be saved in the same directory as the --metadata_json file."
    )

    args = parser.parse_args()

    print("Starting dominant color analysis...")
    analyze_and_save_dominant_colors(
        resized_images_base_folder=args.resized_images_dir,
        metadata_json_path=args.metadata_json,
        output_json_filename=args.output_json
    )
    print("Color analysis script finished.") 