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

# Check if CUDA is available
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Constants
MODEL_URL = 'https://download.pytorch.org/models/inception_v3_google-1a9a5a14.pth'
MODEL_FILE = 'inception_v3_google-1a9a5a14.pth'
LABELS_URL = 'https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json'
LABELS_FILE = 'imagenet_classes.json'

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

class ImageClassifier:
    def __init__(self, model_file, labels_file):
        self.model = models.inception_v3(pretrained=False)
        self.model.load_state_dict(torch.load(model_file))
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
        image = Image.open(image_path)
        input_tensor = self.preprocess(image).unsqueeze(0)
        input_tensor = input_tensor.to(device)

        with torch.no_grad():
            output = self.model(input_tensor)

        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_catid = torch.topk(probabilities, 5)

        results = []
        for i in range(top_prob.size(0)):
            label = self.labels[top_catid[i].item()]
            score = top_prob[i].item()
            results.append({"labels": label, "score": str(score)})

        return results

    def get_feature_vector(self, image_path):
        image = Image.open(image_path)
        input_tensor = self.preprocess(image).unsqueeze(0)
        input_tensor = input_tensor.to(device)

        with torch.no_grad():
            # Get the output of the second last layer (pool3 equivalent in Inception v3)
            features = self.model.avgpool(self.model.extract_features(input_tensor))

        return features.cpu().numpy().squeeze()

def run_inference_on_images(image_list, output_dir):
    image_to_labels = defaultdict(list)
    classifier = ImageClassifier(MODEL_FILE, LABELS_FILE)

    for image_index, image in enumerate(image_list):
        try:
            print(f"Parsing {image_index + 1}/{len(image_list)}: {image}")
            if not os.path.exists(image):
                print(f'File does not exist: {image}')
                continue

            results = classifier.classify_image(image)
            image_to_labels[image] = results

            print("Top 5 predictions:")
            for result in results:
                print(f"  {result['labels']} (score = {result['score']})")

            # Get and save feature vector
            feature_vector = classifier.get_feature_vector(image)
            outfile_name = os.path.basename(image) + ".npz"
            out_path = os.path.join(output_dir, outfile_name)
            np.savetxt(out_path, feature_vector, delimiter=',')
            print(f"Feature vector saved to {out_path}")

            print()  # Empty line for readability

        except Exception as e:
            print(f'Could not process image {image_index + 1}/{len(image_list)}: {image}')
            print(f'Error: {str(e)}')

        # Close open file handlers
        proc = psutil.Process()
        for open_file in proc.open_files():
            os.close(open_file.fd)

    return image_to_labels

def main():
    if len(sys.argv) < 2:
        print("Please provide a glob path to one or more images, e.g.")
        print("python classify_image_pytorch.py '../cats/*.jpg'")
        sys.exit(1)

    ensure_model_and_labels()

    output_dir = "image_vectors"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    images = glob.glob(sys.argv[1])
    if not images:
        print(f"No images found matching the pattern: {sys.argv[1]}")
        sys.exit(1)

    print(f"Found {len(images)} images. Starting classification...")
    image_to_labels = run_inference_on_images(images, output_dir)

    with open("image_to_labels.json", "w") as img_to_labels_out:
        json.dump(image_to_labels, img_to_labels_out, indent=2)

    print(f"Classification complete. Results saved to image_to_labels.json")
    print(f"Feature vectors saved in the '{output_dir}' directory")

if __name__ == '__main__':
    main()