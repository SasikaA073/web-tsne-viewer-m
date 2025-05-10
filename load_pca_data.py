import json
import numpy as np
import os
import pickle 

def load_2d_data_as_numpy_array(json_file_path):
    """Loads a JSON file and converts its 2D coordinate data to a NumPy array."""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        coordinates = []
        for item in data:
            if 'x' in item and 'y' in item:
                coordinates.append([item['x'], item['y']])
            elif 'pca1' in item and 'pca2' in item: # Fallback to pca1/pca2
                coordinates.append([item['pca1'], item['pca2']])
            else:
                print(f"Warning: Skipping item {item.get('image', 'Unknown')} as it lacks 'x'/'y' or 'pca1'/'pca2' keys.")
                continue
        
        if not coordinates:
            print(f"No valid coordinate data with 'x'/'y' or 'pca1'/'pca2' keys found in {json_file_path}.")
            return None

        numpy_array = np.array(coordinates)
        
        print(f"Successfully loaded {json_file_path}")
        print(f"Shape of the NumPy array: {numpy_array.shape}")
        # print("First 5 rows of the array:")
        # print(numpy_array[:5])
        return numpy_array
        
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file_path}'.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_file_path}'.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == '__main__':
    # Replace with the actual path to your file if it's not in the same directory.
    file_path_to_load = "output/images_color_rgb_2D.json" 

    if not os.path.exists(file_path_to_load):
        print(f"Error: The file '{file_path_to_load}' was not found.")
        print("Please ensure the file exists in the correct location or update the 'file_path_to_load' variable.")
    else:
        loaded_array = load_2d_data_as_numpy_array(file_path_to_load)

        # Save array to pickle file
        pickle_path = "output/coordinates_2d.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump(loaded_array, f)
        print(f"Saved array to {pickle_path}")
        print(f"Array shape: {loaded_array.shape}")

        if loaded_array is not None:
            print("NumPy array created successfully.")
            # You can now use 'loaded_array' for your computations.
            # For example, print the whole array (be cautious if it's very large):
            # print(loaded_array)
        else:
            print(f"Failed to create NumPy array from {file_path_to_load}.") 