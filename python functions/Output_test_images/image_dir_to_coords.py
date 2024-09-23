import os
import cv2
import subprocess
import re
import numpy as np
from sklearn.decomposition import PCA
import json
import argparse

# Function to get the most prominent color using ImageMagick
def get_most_prominent_color(image_path):
    """
    Runs an ImageMagick command to find the most prominent color in an image.
    
    Parameters:
    - image_path: Path to the image file.
    
    Returns:
    - most_prominent_color: Tuple (R, G, B) of the most prominent color.
    """
    try:
        # ImageMagick command to get the histogram and sort colors by frequency
        command = (
            f"convert {image_path} -scale 50x50! -depth 8 +dither "
            "-colors 8 -format \"%c\" histogram:info: | sort -r -n -k 1 -t \",\""
        )
        
        # Execute the command using subprocess and capture the output
        result = subprocess.check_output(command, shell=True, universal_newlines=True)
        
        # The first line of the result contains the most prominent color information
        first_line = result.splitlines()[0]
        
        # Use a regular expression to extract the RGB values from the line
        rgb_match = re.search(r'\((\d+),(\d+),(\d+)\)', first_line)
        
        if rgb_match:
            # Convert the RGB values to integers
            r = int(rgb_match.group(1))
            g = int(rgb_match.group(2))
            b = int(rgb_match.group(3))
            most_prominent_color = (r, g, b)
            return most_prominent_color
        else:
            raise ValueError("Could not parse RGB values.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error running ImageMagick command: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to process images in the folder and perform dimensionality reduction
def process_images(folder_path):
    # Get all file paths in the directory
    file_paths = os.listdir(folder_path)

    # Sort files according to numeric order
    file_paths.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

    # Extract the most prominent color for each image
    prominent_colors = []
    for file_path in file_paths:
        image_path = os.path.join(folder_path, file_path)
        color = get_most_prominent_color(image_path)
        prominent_colors.append(color)

    # Convert the prominent colors to a numpy array
    prominent_colors = np.array(prominent_colors)

    # Apply PCA to reduce the dimensionality to 2
    pca = PCA(n_components=2)
    reduced_colors = pca.fit_transform(prominent_colors)

    # Store the X and Y values
    X = reduced_colors[:, 0]
    Y = reduced_colors[:, 1]

    # Store the results in a JSON file
    data = []
    for i in range(len(file_paths)):
        data.append({
            "image": file_paths[i],
            "x": X[i],
            "y": Y[i]
        })

    # Write the data to a JSON file
    with open("color_data.json", "w") as f:
        json.dump(data, f)

    print(f"JSON file 'color_data.json' created with {len(file_paths)} entries.")

# Main function to handle argument parsing
def main():
    parser = argparse.ArgumentParser(description="Process images to find prominent colors and reduce dimensionality using PCA.")
    parser.add_argument("folder_path", type=str, help="Path to the folder containing the images")
    args = parser.parse_args()

    # Process the images in the folder
    process_images(args.folder_path)

if __name__ == "__main__":
    main()
