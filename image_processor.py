import os
import json
from PIL import Image, UnidentifiedImageError

def create_image_montage(
    input_folder_path: str,
    output_folder_path: str,
    resized_images_subfolder_name: str = "images",
    montage_filename: str = "montage.png",
    json_metadata_filename: str = "montage_metadata.json",
    target_resolution: tuple[int, int] = (128, 128),
    montage_grid_size: tuple[int, int] = (15, 15)
):
    """
    Processes images from an input folder: resizes them, creates montages,
    and generates a JSON metadata file. If there are more images than can fit
    in a single montage (based on montage_grid_size), multiple montages
    will be created.

    Args:
        input_folder_path: Path to the folder containing original images.
        output_folder_path: Path to the base directory where all outputs will be stored.
        resized_images_subfolder_name: Name of the subfolder for resized images (default: "images").
        montage_filename: Filename for the output montage image (default: "montage.png").
        json_metadata_filename: Filename for the JSON metadata (default: "montage_metadata.json").
        target_resolution: Tuple (width, height) for resizing images (default: (128, 128)).
        montage_grid_size: Tuple (columns, rows) for the montage grid (default: (15, 15)).
    """

    # 1. Validate inputs and create output directories
    if not os.path.isdir(input_folder_path):
        print(f"Error: Input folder '{input_folder_path}' not found.")
        return

    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
        print(f"Created output folder: '{output_folder_path}'")

    resized_images_dir = os.path.join(output_folder_path, resized_images_subfolder_name)
    if not os.path.exists(resized_images_dir):
        os.makedirs(resized_images_dir)
        print(f"Created resized images folder: '{resized_images_dir}'")

    # 2. List and filter image files
    valid_image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
    original_image_paths = []
    for filename in os.listdir(input_folder_path):
        if filename.lower().endswith(valid_image_extensions):
            original_image_paths.append(os.path.join(input_folder_path, filename))

    if not original_image_paths:
        print(f"No images found in '{input_folder_path}'.")
        return

    print(f"Found {len(original_image_paths)} images in '{input_folder_path}'.")

    # 3. Resize images and store their paths
    resized_image_data = [] # List to store (original_path, resized_path)
    
    print(f"Resizing images to {target_resolution[0]}x{target_resolution[1]}...")
    for i, original_path in enumerate(original_image_paths):
        try:
            img = Image.open(original_path)
            img_resized = img.resize(target_resolution, Image.Resampling.LANCZOS)
            
            original_basename, original_ext = os.path.splitext(os.path.basename(original_path))
            # Ensure resized images are saved in a common format like PNG for consistency in montage
            resized_filename = f"{original_basename}_resized_{i}.png" 
            resized_path = os.path.join(resized_images_dir, resized_filename)
            
            img_resized.save(resized_path)
            resized_image_data.append({
                "original_full_path": os.path.abspath(original_path),
                "original_filename": os.path.basename(original_path),
                "resized_full_path": os.path.abspath(resized_path),
                "resized_filename": resized_filename
            })
        except FileNotFoundError:
            print(f"Warning: Original image not found at '{original_path}'. Skipping.")
        except UnidentifiedImageError:
            print(f"Warning: Cannot identify image file '{original_path}'. Skipping.")
        except Exception as e:
            print(f"Warning: Could not process image '{original_path}': {e}. Skipping.")

    if not resized_image_data:
        print("No images were successfully resized. Aborting montage creation.")
        return
    
    print(f"Successfully resized {len(resized_image_data)} images.")

    # 4. Create montage(s)
    montage_cols, montage_rows = montage_grid_size
    images_per_montage = montage_cols * montage_rows
    
    if images_per_montage <= 0:
        print(f"Error: Invalid montage grid size {montage_grid_size}. Number of images per montage must be positive.")
        return

    base_montage_filename, montage_ext = os.path.splitext(montage_filename)
    if not montage_ext: # Ensure there's an extension, default to .png
        montage_ext = ".png"
        print(f"Warning: Montage filename '{montage_filename}' had no extension. Defaulting to '{montage_ext}'.")


    all_montage_metadata = [] # To store metadata from all montages

    num_montages_to_create = (len(resized_image_data) + images_per_montage - 1) // images_per_montage
    print(f"Preparing to create {num_montages_to_create} montage(s), each with up to {images_per_montage} images.")

    for montage_idx in range(num_montages_to_create):
        start_image_index = montage_idx * images_per_montage
        end_image_index = start_image_index + images_per_montage
        current_montage_images_data = resized_image_data[start_image_index:end_image_index]

        if not current_montage_images_data:
            print(f"No images for montage {montage_idx}. Skipping.")
            continue

        current_montage_filename = f"{base_montage_filename}_{montage_idx}{montage_ext}"
        
        montage_width = montage_cols * target_resolution[0]
        montage_height = montage_rows * target_resolution[1]
        
        # Determine actual rows needed for this specific montage if it's the last one and not full
        actual_images_in_this_montage = len(current_montage_images_data)
        actual_rows_for_this_montage = (actual_images_in_this_montage + montage_cols -1) // montage_cols
        montage_actual_height = actual_rows_for_this_montage * target_resolution[1]


        montage_image = Image.new('RGB', (montage_width, montage_actual_height), (255, 255, 255)) # White background
        print(f"Creating montage {montage_idx+1}/{num_montages_to_create} ('{current_montage_filename}') of size {montage_width}x{montage_actual_height}...")

        for i, img_data in enumerate(current_montage_images_data):
            try:
                img_to_paste = Image.open(img_data["resized_full_path"])
                # If image is RGBA, convert to RGB to avoid issues with pasting on RGB background
                if img_to_paste.mode == 'RGBA':
                    img_to_paste = img_to_paste.convert('RGB')

                col = i % montage_cols
                row = i // montage_cols
                x_offset = col * target_resolution[0]
                y_offset = row * target_resolution[1]
                montage_image.paste(img_to_paste, (x_offset, y_offset))

                # Collect metadata for JSON
                all_montage_metadata.append({
                    "original_filename": img_data["original_filename"],
                    "original_full_path": img_data["original_full_path"],
                    "resized_filename": img_data["resized_filename"],
                    "resized_full_path": img_data["resized_full_path"],
                    "montage_name": current_montage_filename,
                    "montage_group_index": montage_idx, # Index of the montage file
                    "image_index_in_montage": i,        # Index of this image within its montage
                    "montage_row_in_group": row,
                    "montage_col_in_group": col
                })
            except FileNotFoundError:
                print(f"Warning: Resized image not found at '{img_data['resized_full_path']}' during montage creation for {current_montage_filename}. Skipping this image.")
            except Exception as e:
                print(f"Warning: Could not paste image '{img_data['resized_full_path']}' into montage {current_montage_filename}: {e}. Skipping.")

        # Save current montage
        current_montage_output_path = os.path.join(output_folder_path, current_montage_filename)
        try:
            montage_image.save(current_montage_output_path)
            print(f"Montage {current_montage_filename} saved to '{current_montage_output_path}'")
        except Exception as e:
            print(f"Error: Could not save montage image {current_montage_filename}: {e}")
            # Continue to save JSON if possible, but this montage might be missing.

    # 5. Save JSON metadata (consolidated for all montages)
    json_output_path = os.path.join(output_folder_path, json_metadata_filename)
    try:
        with open(json_output_path, 'w') as f:
            json.dump(all_montage_metadata, f, indent=4)
        print(f"Consolidated JSON metadata saved to '{json_output_path}'")
    except Exception as e:
        print(f"Error: Could not save JSON metadata: {e}")

    print("Processing complete.")

if __name__ == '__main__':
    # Example usage:
    # Create dummy folders and images for testing
    print("Setting up a dummy test environment...")
    if not os.path.exists("sample_input_images"):
        os.makedirs("sample_input_images")
    if not os.path.exists("sample_output_data"):
        os.makedirs("sample_output_data")

    # Create a few dummy images (requires Pillow to create, or you can place your own)
    try:
        # Test case 1: More images than fit in one montage
        print("\n--- Test Case 1: Multiple Montages ---")
        num_total_images_case1 = 10
        grid_size_case1 = (2,2) # 4 images per montage
        input_dir_case1 = "sample_input_images_multi"
        output_dir_case1 = "sample_output_data_multi"

        if os.path.exists(input_dir_case1):
            import shutil
            shutil.rmtree(input_dir_case1)
        os.makedirs(input_dir_case1)
        if os.path.exists(output_dir_case1):
            import shutil
            shutil.rmtree(output_dir_case1)
        os.makedirs(output_dir_case1)

        for i in range(num_total_images_case1): 
            img = Image.new('RGB', (60, 40), color = (i*20, i*15, i*25))
            img.save(os.path.join(input_dir_case1, f"multi_test_image_{i+1}.png"))
        print(f"Dummy images for multi-montage test created in '{input_dir_case1}'.")
        
        create_image_montage(
            input_folder_path=input_dir_case1,
            output_folder_path=output_dir_case1,
            resized_images_subfolder_name="resized_imgs",
            montage_filename="multi_montage.png", # Base name
            json_metadata_filename="multi_montage_info.json",
            target_resolution=(50, 50),
            montage_grid_size=grid_size_case1 
        )

        # Test case 2: Fewer images than grid (original test)
        print("\n--- Test Case 2: Single Montage (Fewer Images than Grid) ---")
        input_dir_case2 = "sample_input_images_single_small"
        output_dir_case2 = "sample_output_data_single_small"
        if os.path.exists(input_dir_case2):
            import shutil
            shutil.rmtree(input_dir_case2)
        os.makedirs(input_dir_case2)
        if os.path.exists(output_dir_case2):
            import shutil
            shutil.rmtree(output_dir_case2)
        os.makedirs(output_dir_case2)

        img = Image.new('RGB', (100,100), color='blue')
        img.save(os.path.join(input_dir_case2, "small_img1.png"))
        img = Image.new('RGB', (100,100), color='red')
        img.save(os.path.join(input_dir_case2, "small_img2.png"))
        print(f"Dummy images for single-small-montage test created in '{input_dir_case2}'.")
        create_image_montage(
            input_folder_path=input_dir_case2,
            output_folder_path=output_dir_case2,
            montage_grid_size=(2,2) # 2x2 grid, but only 2 images
        )

        # Test case 3: Exact number of images for one montage
        print("\n--- Test Case 3: Single Montage (Exact Fit) ---")
        num_total_images_case3 = 4
        grid_size_case3 = (2,2) # 4 images per montage
        input_dir_case3 = "sample_input_images_exact"
        output_dir_case3 = "sample_output_data_exact"

        if os.path.exists(input_dir_case3):
            import shutil
            shutil.rmtree(input_dir_case3)
        os.makedirs(input_dir_case3)
        if os.path.exists(output_dir_case3):
            import shutil
            shutil.rmtree(output_dir_case3)
        os.makedirs(output_dir_case3)

        for i in range(num_total_images_case3): 
            img = Image.new('RGB', (70, 70), color = (100+i*10, 50+i*20, 200-i*15))
            img.save(os.path.join(input_dir_case3, f"exact_test_image_{i+1}.jpg"))
        print(f"Dummy images for exact-fit-montage test created in '{input_dir_case3}'.")
        
        create_image_montage(
            input_folder_path=input_dir_case3,
            output_folder_path=output_dir_case3,
            montage_filename="exact_montage.tiff", # Test different extension
            json_metadata_filename="exact_montage_data.json",
            target_resolution=(64, 64),
            montage_grid_size=grid_size_case3 
        )


    except ImportError:
        print("Pillow library is not installed. Cannot create dummy images for the example.")
    except Exception as e:
        print(f"An error occurred during the example setup or run: {e}")
    
    print("\nTo use this script, replace the example 'input_folder_path' and 'output_folder_path'")
    print("with your actual directories in the if __name__ == '__main__': block or call the function from another script.") 