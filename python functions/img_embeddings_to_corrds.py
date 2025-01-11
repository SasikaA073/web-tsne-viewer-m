# Import necessary libraries
import os
import json
import numpy as np
from sklearn.manifold import TSNE
from sklearn.preprocessing import MinMaxScaler

# Configuration
n_dims = 3  # Start with 3D to generate coordinates for 3D embeddings first
output_dir = 'image_vectors'  # Ensure this is the directory containing .npz files
multiplication_factor = 25  # Define the multiplication factor

# Load the image embeddings
img_embeddings = {}
for file in os.listdir(output_dir):
    if file.endswith('.npz'):
        img_id = file.split('.')[0]  # Remove both .jpg and .npz extensions
        img_embeddings[img_id] = np.loadtxt(os.path.join(output_dir, file), delimiter=',')

if len(img_embeddings) == 0:
    raise ValueError("No .npz files found in 'image_vectors' directory")

# Convert embeddings to numpy array
embeddings_array = np.array(list(img_embeddings.values()))

# Print shape information for debugging
print(f"Number of images: {len(img_embeddings)}")
print(f"Embedding dimensions: {embeddings_array.shape}")

# Perform t-SNE dimensionality reduction
try:
    # 3D t-SNE coordinates generation
    tsne_3d = TSNE(
        n_components=3,
        random_state=0,
        perplexity=min(30, len(img_embeddings) - 1)  # Adjust perplexity based on dataset size
    )
    img_coords_3d = tsne_3d.fit_transform(embeddings_array)

    # Standardize the coordinates to [0, 1]
    scaler = MinMaxScaler(feature_range=(0, 1))
    img_coords_3d_scaled = scaler.fit_transform(img_coords_3d)

    # Apply the multiplication factor
    img_coords_3d_scaled *= multiplication_factor

    # Save 3D coordinates to JSON
    coordinates_3d = [
        {
            "image": f"{img_id}.jpg",
            "x": float(x),
            "y": float(y),
            "z": float(z)
        }
        for img_id, (x, y, z) in zip(img_embeddings.keys(), img_coords_3d_scaled)
    ]

    output_file_3d = 'tsne_img_3D_coords.json'
    with open(output_file_3d, 'w') as f:
        json.dump(coordinates_3d, f, indent=2)

    print(f"\nt-SNE 3D coordinates saved to {output_file_3d}")
    print(f"Processed {len(img_embeddings)} images for 3D embeddings successfully")

    # 2D t-SNE coordinates generation
    tsne_2d = TSNE(
        n_components=2,
        random_state=0,
        perplexity=min(30, len(img_embeddings) - 1)  # Adjust perplexity based on dataset size
    )
    img_coords_2d = tsne_2d.fit_transform(embeddings_array)

    # Standardize the coordinates to [0, 1]
    img_coords_2d_scaled = scaler.fit_transform(img_coords_2d)

    # Apply the multiplication factor
    img_coords_2d_scaled *= multiplication_factor

    # Save 2D coordinates to JSON
    coordinates_2d = [
        {
            "image": f"{img_id}.jpg",
            "x": float(x),
            "y": float(y)
        }
        for img_id, (x, y) in zip(img_embeddings.keys(), img_coords_2d_scaled)
    ]

    output_file_2d = 'tsne_img_2D_coords.json'
    with open(output_file_2d, 'w') as f:
        json.dump(coordinates_2d, f, indent=2)

    print(f"t-SNE 2D coordinates saved to {output_file_2d}")
    print(f"Processed {len(img_embeddings)} images for 2D embeddings successfully")

except Exception as e:
    print(f"Error during t-SNE processing: {str(e)}")
    if "perplexity" in str(e):
        print("\nNote: If you're getting a perplexity error, you might have too few images.")
        print("Try reducing the perplexity value or using more images.")
    raise
