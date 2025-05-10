import os
import json
import argparse
from PIL import Image, UnidentifiedImageError, ImageStat
from collections import Counter
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

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

def get_mean_color(image_path):
    """Opens an image and returns its mean color as an RGB tuple."""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        stat = ImageStat.Stat(img)
        mean_color_tuple = tuple(map(int, stat.mean)) # Convert float means to int
        return mean_color_tuple
    except FileNotFoundError:
        print(f"Error: Image file not found at '{image_path}'.")
        return None
    except UnidentifiedImageError:
        print(f"Error: Cannot identify image file '{image_path}'.")
        return None
    except Exception as e:
        print(f"Error processing image '{image_path}': {e}")
        return None

def analyze_and_save_mean_colors(
    resized_images_base_folder: str, 
    metadata_json_path: str, 
    output_json_filename: str = "images_color_rgb.json"
):
    """
    Analyzes images listed in a metadata JSON to find their mean color
    and saves the results to a new JSON file.

    Args:
        resized_images_base_folder: Path to the folder containing the subfolder with resized images.
                                     (e.g., your main output_dir from image_processor.py)
        metadata_json_path: Path to the montage_metadata.json file.
        output_json_filename: Name of the JSON file to save mean color data.
    """

    if not os.path.isdir(resized_images_base_folder):
        print(f"Error: Base folder for resized images '{resized_images_base_folder}' not found.")
        return None, None # Return None for data and output_dir

    if not os.path.isfile(metadata_json_path):
        print(f"Error: Metadata JSON file '{metadata_json_path}' not found.")
        return None, None # Return None for data and output_dir

    try:
        with open(metadata_json_path, 'r') as f:
            metadata_list = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{metadata_json_path}'.")
        return None, None # Return None for data and output_dir
    except Exception as e:
        print(f"Error reading metadata file '{metadata_json_path}': {e}")
        return None, None # Return None for data and output_dir

    if not metadata_list:
        print("No image metadata found in the JSON file.")
        return None, None # Return None for data and output_dir
    
    print(f"Analyzing images from folder: '{resized_images_base_folder}'")

    # Step 1: Collect all unique resized filenames and calculate their mean colors once.
    unique_resized_filenames_from_metadata = set()
    for item in metadata_list:
        if "resized_filename" in item:
            unique_resized_filenames_from_metadata.add(item["resized_filename"])

    if not unique_resized_filenames_from_metadata:
        print("No resized filenames found in metadata. Cannot proceed.")
        return None, None # Return None for data and output_dir
        
    print(f"Found {len(unique_resized_filenames_from_metadata)} unique resized image files referenced in metadata.")

    resized_image_mean_color_cache = {} # Cache: {resized_filename: [R,G,B] or None}
    processed_for_color_count = 0
    failed_to_get_color_count = 0

    for resized_filename in unique_resized_filenames_from_metadata:
        image_full_path = os.path.join(resized_images_base_folder, resized_filename)
        # print(f"Calculating mean color for: {resized_filename}") # Can be verbose
        mean_color = get_mean_color(image_full_path)
        if mean_color:
            resized_image_mean_color_cache[resized_filename] = list(mean_color) 
            processed_for_color_count += 1
        else:
            resized_image_mean_color_cache[resized_filename] = None # Mark as failed
            failed_to_get_color_count +=1
            
    print(f"Successfully calculated mean colors for {processed_for_color_count} unique resized images.")
    if failed_to_get_color_count > 0:
        print(f"Failed to determine mean color for {failed_to_get_color_count} unique resized images.")

    # Step 2: Create the final list of dictionaries in the desired format.
    output_data_list = []
    items_added_to_output = 0
    for item in metadata_list:
        original_filename = item.get("original_filename")
        resized_filename = item.get("resized_filename")

        if not original_filename or not resized_filename:
            print(f"Warning: Skipping metadata item due to missing original or resized filename: {item}")
            continue
            
        # Get the pre-calculated mean color from our cache
        mean_color_rgb = resized_image_mean_color_cache.get(resized_filename)

        if mean_color_rgb: # Only include if color was successfully found for its resized version
            output_data_list.append({
                "image": original_filename,
                "x": mean_color_rgb[0], # R component
                "y": mean_color_rgb[1], # G component
                "z": mean_color_rgb[2]  # B component
            })
            items_added_to_output += 1
        # else: # Optional: handle cases where mean color for the resized image was None
            # print(f"Mean color for {resized_filename} (original: {original_filename}) not found or failed. Not adding to output.")

    print(f"Added {items_added_to_output} entries to the final JSON output list.")

    if not output_data_list:
        print("No data to save after processing. Output JSON will not be created.")
        return None, None # Return None for data and output_dir

    # Output JSON will be saved in the same directory as the metadata_json_path by default
    output_dir = os.path.dirname(metadata_json_path) 
    # Or, if we want it in `resized_images_base_folder`'s parent:
    # output_dir = os.path.dirname(resized_images_base_folder) # if images_base_folder is .../output/images
    
    # Let's save it in the same directory as the input metadata JSON, which is likely the main output folder.
    final_output_json_path = os.path.join(output_dir, output_json_filename)

    try:
        with open(final_output_json_path, 'w') as f:
            json.dump(output_data_list, f, indent=4)
        print(f"Mean color data saved to '{final_output_json_path}'")
        return output_data_list, output_dir # Return data and output_dir
    except Exception as e:
        print(f"Error saving output JSON to '{final_output_json_path}': {e}")
        return None, None # Return None for data and output_dir

def save_pca_transformed_colors(mean_color_data_list, output_dir, pca_output_filename="images_color_rgb_2D.json"):
    """
    Performs PCA on the mean color data and saves the 2D transformed data to a JSON file.

    Args:
        mean_color_data_list: List of dictionaries with original image filenames and mean RGB colors.
                              (Output from analyze_and_save_mean_colors)
        output_dir: The directory where the PCA output JSON file should be saved.
        pca_output_filename: Name of the JSON file for PCA results.
    """
    if not mean_color_data_list:
        print("No mean color data provided for PCA. Skipping PCA.")
        return

    if not output_dir or not os.path.isdir(output_dir):
        print(f"Output directory '{output_dir}' for PCA results is invalid. Skipping PCA.")
        return

    print("Starting PCA transformation of mean colors...")

    # Extract RGB values and corresponding image filenames
    rgb_values = []
    image_filenames = []
    for item in mean_color_data_list:
        rgb_values.append([item['x'], item['y'], item['z']])
        image_filenames.append(item['image'])

    if not rgb_values:
        print("No RGB values extracted for PCA. Skipping.")
        return

    try:
        rgb_array = np.array(rgb_values, dtype=float) # Ensure dtype is float for calculations

        # Check for NaN or Inf values
        if np.isnan(rgb_array).any() or np.isinf(rgb_array).any():
            print("Warning: NaN or Inf values found in RGB data. PCA might produce unexpected results.")
            # Optionally, handle or clean these values here, e.g., replace with mean or remove rows
            # For now, we'll proceed but the warnings are important.
            rgb_array = np.nan_to_num(rgb_array) # Example: replace NaN with 0, Inf with large finite numbers

        # Check for zero variance columns (features)
        if np.any(np.var(rgb_array, axis=0) == 0):
            print("Warning: One or more color channels have zero variance across all images. PCA might be unstable.")
            # If this is an issue, PCA might not be appropriate or data needs cleaning/
            # For instance, if all images have the same Red value, that channel has 0 variance.

        # Standardize the data (mean=0, variance=1)
        scaler = StandardScaler()
        scaled_rgb_array = scaler.fit_transform(rgb_array)

        # Check if scaling resulted in NaN/Inf (e.g., if variance was zero for a feature)
        if np.isnan(scaled_rgb_array).any() or np.isinf(scaled_rgb_array).any():
            print("Warning: NaN or Inf values found after scaling. This might happen if a feature had zero variance.")
            # Fallback: use original array if scaling fails catastrophically, or handle more gracefully
            # For now, we'll try to clean it up.
            scaled_rgb_array = np.nan_to_num(scaled_rgb_array)
            if np.any(np.var(scaled_rgb_array, axis=0) == 0) and scaled_rgb_array.shape[1] > 1:
                 print("Warning: After attempting to fix NaN/Inf from scaling, zero variance still detected in some features. PCA might still be problematic.")

        # Initialize PCA to reduce to 2 components
        # If, after scaling and cleaning, we still have issues (e.g. all data became zero), PCA might still warn.
        if scaled_rgb_array.shape[0] < 2:
            print("Warning: Not enough samples for PCA after processing. Skipping PCA.")
            return
            
        pca = PCA(n_components=2)
        # Ensure that n_components is not greater than number of samples or features if they are very small
        n_samples, n_features = scaled_rgb_array.shape
        current_n_components = min(2, n_samples, n_features)
        if current_n_components < 1:
            print("Warning: Not enough features/samples to perform PCA. Skipping PCA.")
            return
        if current_n_components < 2:
            print(f"Warning: Reducing PCA components to {current_n_components} due to limited data.")
        
        pca = PCA(n_components=current_n_components)
        pca_transformed_data = pca.fit_transform(scaled_rgb_array)
        
        # Prepare data for JSON output
        pca_output_list = []
        for i, filename in enumerate(image_filenames):
            pca_output_list.append({
                "image": filename,
                "x": pca_transformed_data[i, 0],
                "y": pca_transformed_data[i, 1]
            })
            
        final_pca_json_path = os.path.join(output_dir, pca_output_filename)
        with open(final_pca_json_path, 'w') as f:
            json.dump(pca_output_list, f, indent=4)
        print(f"PCA transformed color data saved to '{final_pca_json_path}'")
        
    except Exception as e:
        print(f"Error during PCA transformation or saving: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Analyzes resized images to find their mean color, saves this to a JSON file, "
                    "and then performs PCA on these colors, saving the 2D results to another JSON file."
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
        help="Name for the output JSON file storing mean colors (default: images_color_rgb.json). "
             "This file will be saved in the same directory as the --metadata_json file."
    )
    parser.add_argument(
        "--pca_output_json",
        type=str,
        default="images_color_rgb_2D.json",
        help="Name for the output JSON file storing 2D PCA transformed mean colors (default: images_color_rgb_2D.json). "
             "This file will also be saved in the same directory as the --metadata_json file."
    )

    args = parser.parse_args()

    print("Starting mean color analysis...")
    mean_color_data, out_dir = analyze_and_save_mean_colors(
        resized_images_base_folder=args.resized_images_dir,
        metadata_json_path=args.metadata_json,
        output_json_filename=args.output_json
    )
    
    if mean_color_data and out_dir:
        save_pca_transformed_colors(
            mean_color_data_list=mean_color_data,
            output_dir=out_dir,
            pca_output_filename=args.pca_output_json
        )
    else:
        print("Skipping PCA transformation due to issues in mean color analysis.")
        
    print("Color analysis script finished.") 