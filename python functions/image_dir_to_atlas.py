import os
import cv2
import zipfile
import matplotlib.pyplot as plt
import argparse

# Function to ensure the correct number of images
def limit_images_to_n(image_dir, n_images):
    image_file_paths = os.listdir(image_dir)
    if len(image_file_paths) > n_images:
        for image_file_path in image_file_paths[n_images:]:
            os.remove(os.path.join(image_dir, image_file_path))
        image_file_paths = image_file_paths[:n_images]
    return image_file_paths

# Function to center-crop images to a specific size and save them with 1-indexed filenames
def center_crop_images(image_file_paths, image_dir, output_dir, img_size):
    os.makedirs(output_dir, exist_ok=True)
    for i, image_file_path in enumerate(image_file_paths):
        image = plt.imread(os.path.join(image_dir, image_file_path))
        center_cropped_image = cv2.resize(image, img_size)
        plt.imsave(os.path.join(output_dir, f"{i+1}.jpg"), center_cropped_image)

# Function to create a zip file for the cropped images
def create_zip_file(output_dir, zip_file):
    with zipfile.ZipFile(zip_file, "w") as zipf:
        for image_file_path in os.listdir(output_dir):
            zipf.write(os.path.join(output_dir, image_file_path), arcname=image_file_path)

# Function to save the list of cropped image paths to a text file
def save_image_paths_to_text(output_dir, text_file):
    center_cropped_file_paths = os.listdir(output_dir)
    center_cropped_file_paths.sort(key=lambda x: int(x.split(".")[0]))  # Sort by filename
    with open(text_file, "w") as f:
        for image_file_path in center_cropped_file_paths:
            f.write(f"{output_dir}/{image_file_path}\n")

# Function to create an image montage using ImageMagick's `montage` command
def create_montage(text_file, montage_file, n_cols, n_rows):
    os.system(f"montage `cat {text_file}` -geometry +0+0 -background none -tile {n_cols}x{n_rows} {montage_file}")

# Function to parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Create an image atlas from a folder of images.")
    
    # Add arguments for input and output
    parser.add_argument('--input', required=True, type=str, help='Directory containing the images')
    parser.add_argument('--output', required=True, type=str, help='Output text file for image paths')
    
    # Parse arguments
    args = parser.parse_args()
    
    return args.input, args.output

# MAIN PIPELINE
def main():

    # Define constants
    N_IMAGES = 300
    IMG_SIZE = (128, 128)  # Size to center-crop images to
    N_ROWS = 15
    N_COLS = 20

    # Get IMAGE_DIR and TEXT_FILE from command line
    IMAGE_DIR, TEXT_FILE = parse_arguments()
   
    main_output_dir = f"Output_{IMAGE_DIR}"
    os.makedirs(main_output_dir, exist_ok=True)
    # Output directory, zip file, and montage file can be derived or hardcoded
    OUTPUT_DIR = f"{main_output_dir}/{TEXT_FILE}_center_cropped"
    ZIP_FILE = f"{main_output_dir}/{TEXT_FILE}_center_cropped.zip"
    MONTAGE_FILE = f"{main_output_dir}/{TEXT_FILE}-img-atlas.jpg"

    TEXT_FILE = TEXT_FILE + ".txt"

    # Step 1: Ensure we have exactly N_IMAGES and list the image paths
    image_file_paths = limit_images_to_n(IMAGE_DIR, N_IMAGES)

    # Step 2: Center crop the images to 128x128 and save them
    print("Center cropping images...")
    center_crop_images(image_file_paths, IMAGE_DIR, OUTPUT_DIR, IMG_SIZE)

    # Step 3: Create a zip file of the center-cropped images
    print("Creating zip file...")
    create_zip_file(OUTPUT_DIR, ZIP_FILE)

    # Step 4: Save a text file with the paths of the cropped images
    print("Saving image paths to text file...")
    save_image_paths_to_text(OUTPUT_DIR, TEXT_FILE)

    # Step 5: Create a montage using ImageMagick
    print("Creating image montage...")
    create_montage(TEXT_FILE, MONTAGE_FILE, N_COLS, N_ROWS)

if __name__ == "__main__":
    main()
