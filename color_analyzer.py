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
    
    print(f"Analyzing images from folder: '{resized_images_base_folder}'")

    # Step 1: Collect all unique resized filenames and calculate their dominant colors once.
    unique_resized_filenames_from_metadata = set()
    for item in metadata_list:
        if "resized_filename" in item:
            unique_resized_filenames_from_metadata.add(item["resized_filename"])

    if not unique_resized_filenames_from_metadata:
        print("No resized filenames found in metadata. Cannot proceed.")
        return
        
    print(f"Found {len(unique_resized_filenames_from_metadata)} unique resized image files referenced in metadata.")

    resized_image_dominant_color_cache = {} # Cache: {resized_filename: [R,G,B] or None}
    processed_for_color_count = 0
    failed_to_get_color_count = 0

    for resized_filename in unique_resized_filenames_from_metadata:
        image_full_path = os.path.join(resized_images_base_folder, resized_filename)
        # print(f"Calculating dominant color for: {resized_filename}") # Can be verbose
        dominant_color = get_dominant_color(image_full_path)
        if dominant_color:
            resized_image_dominant_color_cache[resized_filename] = list(dominant_color) 
            processed_for_color_count += 1
        else:
            resized_image_dominant_color_cache[resized_filename] = None # Mark as failed
            failed_to_get_color_count +=1
            
    print(f"Successfully calculated dominant colors for {processed_for_color_count} unique resized images.")
    if failed_to_get_color_count > 0:
        print(f"Failed to determine dominant color for {failed_to_get_color_count} unique resized images.")

    # Step 2: Create the final list of dictionaries in the desired format.
    output_data_list = []
    items_added_to_output = 0
    for item in metadata_list:
        original_filename = item.get("original_filename")
        resized_filename = item.get("resized_filename")

        if not original_filename or not resized_filename:
            print(f"Warning: Skipping metadata item due to missing original or resized filename: {item}")
            continue
            
        # Get the pre-calculated dominant color from our cache
        dominant_color_rgb = resized_image_dominant_color_cache.get(resized_filename)

        if dominant_color_rgb: # Only include if color was successfully found for its resized version
            output_data_list.append({
                "image": original_filename,
                "x": dominant_color_rgb[0], # R component
                "y": dominant_color_rgb[1], # G component
                "z": dominant_color_rgb[2]  # B component
            })
            items_added_to_output += 1
        # else: # Optional: handle cases where dominant color for the resized image was None
            # print(f"Dominant color for {resized_filename} (original: {original_filename}) not found or failed. Not adding to output.")

    print(f"Added {items_added_to_output} entries to the final JSON output list.")

    if not output_data_list:
        print("No data to save after processing. Output JSON will not be created.")
        return

    # Output JSON will be saved in the same directory as the metadata_json_path by default
    output_dir = os.path.dirname(metadata_json_path) 
    # Or, if we want it in `resized_images_base_folder`'s parent:
    # output_dir = os.path.dirname(resized_images_base_folder) # if images_base_folder is .../output/images
    
    # Let's save it in the same directory as the input metadata JSON, which is likely the main output folder.
    final_output_json_path = os.path.join(output_dir, output_json_filename)

    try:
        with open(final_output_json_path, 'w') as f:
            json.dump(output_data_list, f, indent=4)
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