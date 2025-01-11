import os
import sys
import glob
import json
import psutil
from collections import defaultdict
import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import urllib.request
import traceback

# Check if CUDA is available
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Constants
MODEL_URL = 'https://download.pytorch.org/models/inception_v3_google-1a9a5a14.pth'
MODEL_FILE = 'inception_v3_google-1a9a5a14.pth'
LABELS_URL = 'https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json'
LABELS_FILE = 'imagenet_classes.json'
VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']

def download_file(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)
        print(f"{filename} downloaded successfully.")
    else:
        print(f"{filename} already exists.")

def ensure_model_and_labels():
    download_file(MODEL_URL, MODEL_FILE)
    download_file(LABELS_URL, LABELS_FILE)

def get_all_images(folder_path):
    """Get all images with valid extensions from the given folder."""
    images = []
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist!")
        return images

    # Walk through the directory
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in VALID_EXTENSIONS):
                full_path = os.path.join(root, file)
                images.append(full_path)

    return sorted(images)

class ImageClassifier:
    def __init__(self, model_file, labels_file):
        self.model = models.inception_v3(weights=None, init_weights=True)
        state_dict = torch.load(model_file, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.to(device)
        self.model.eval()

        with open(labels_file, 'r') as f:
            self.labels = json.load(f)

        self.preprocess = transforms.Compose([
            transforms.Resize(299),
            transforms.CenterCrop(299),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def classify_image(self, image_path):
        try:
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.preprocess(image).unsqueeze(0)
            input_tensor = input_tensor.to(device)

            with torch.no_grad():
                output = self.model(input_tensor)

            if isinstance(output, tuple):
                output = output[0]

            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            top_prob, top_catid = torch.topk(probabilities, 5)

            results = []
            for i in range(top_prob.size(0)):
                catid_str = str(top_catid[i].item())
                label = self.labels[catid_str][1]
                score = float(top_prob[i].item())
                results.append({"label": label, "score": f"{score:.4f}"})

            return results

        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}\n{traceback.format_exc()}")

    def get_feature_vector(self, image_path):
        try:
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.preprocess(image).unsqueeze(0)
            input_tensor = input_tensor.to(device)

            with torch.no_grad():
                # Get features before the final classification layer
                x = self.model.Conv2d_1a_3x3(input_tensor)
                # ... (remaining feature extraction layers)
                x = self.model.avgpool(x)
                features = torch.flatten(x, 1)

            return features.cpu().numpy().squeeze()

        except Exception as e:
            raise Exception(f"Error extracting features: {str(e)}\n{traceback.format_exc()}")

def run_inference_on_images(image_list, output_dir):
    image_to_labels = defaultdict(list)
    classifier = ImageClassifier(MODEL_FILE, LABELS_FILE)

    total_images = len(image_list)
    print(f"\nProcessing {total_images} images...")

    for image_index, image in enumerate(image_list, 1):
        try:
            print(f"\nProcessing {image_index}/{total_images}: {os.path.basename(image)}")
            
            results = classifier.classify_image(image)
            image_to_labels[image] = results

            # print("Top 5 predictions:")
            # for result in results:
            #     print(f"  {result['label']} (score = {result['score']})")

            # Get and save feature vector
            feature_vector = classifier.get_feature_vector(image)
            outfile_name = os.path.basename(image) + ".npz"
            out_path = os.path.join(output_dir, outfile_name)
            np.savetxt(out_path, feature_vector, delimiter=',')
            print(f"Feature vector saved to {out_path}")

        except Exception as e:
            print(f'Error processing image {image_index}/{total_images}: {image}')
            print(f'Error details: {str(e)}')

        # Close open file handlers
        try:
            proc = psutil.Process()
            for open_file in proc.open_files():
                os.close(open_file.fd)
        except Exception as e:
            print(f"Warning: Could not close file handlers: {str(e)}")

    return image_to_labels

def main():
    if len(sys.argv) != 2:
        print("Please provide the path to the folder containing images, e.g.")
        print("python classify_image_pytorch.py path/to/image/folder")
        sys.exit(1)

    folder_path = sys.argv[1]
    
    # Remove any trailing slashes for consistency
    folder_path = folder_path.rstrip('/')
    
    ensure_model_and_labels()

    output_dir = "image_vectors"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get all images from the folder
    images = get_all_images(folder_path)
    
    if not images:
        print(f"No images found in folder: {folder_path}")
        print(f"Supported formats: {', '.join(VALID_EXTENSIONS)}")
        sys.exit(1)

    print(f"Found {len(images)} images. Starting classification...")
    image_to_labels = run_inference_on_images(images, output_dir)

    # Save results
    output_json = "image_to_labels.json"
    with open(output_json, "w") as img_to_labels_out:
        json.dump(image_to_labels, img_to_labels_out, indent=2)

    print(f"\nClassification complete!")
    print(f"Results saved to {output_json}")
    print(f"Feature vectors saved in '{output_dir}' directory")
    print(f"Processed {len(images)} images with formats: {', '.join(VALID_EXTENSIONS)}")

if __name__ == '__main__':
    main()