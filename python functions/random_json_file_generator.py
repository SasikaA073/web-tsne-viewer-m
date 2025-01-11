import json
import random

# Generate 300 random coordinates
coordinates = [{'x': round(random.uniform(0, 1), 3), 'y': round(random.uniform(-1, 1), 3)} for _ in range(300)]

# Define the JSON file name
json_file = 'coordinates.json'

# Write to the JSON file
with open(json_file, 'w') as f:
    json.dump(coordinates, f, indent=2)

print(f"Generated {len(coordinates)} coordinates and saved to '{json_file}'.")
