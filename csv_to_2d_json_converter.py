import csv
import json
import os
import argparse

def convert_csv_to_2d_json(csv_file_path: str, output_json_path: str):
    """
    Reads a CSV file with x, y, and image_path columns and converts it to a JSON
    file with the structure: [{'image': filename, 'x': x_coord, 'y': y_coord}, ...].

    Args:
        csv_file_path: Path to the input CSV file.
        output_json_path: Path to save the output JSON file.
    """
    if not os.path.isfile(csv_file_path):
        print(f"Error: Input CSV file not found at '{csv_file_path}'")
        return

    output_data_list = []
    line_count = 0
    processed_count = 0
    error_count = 0

    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if not all(col in reader.fieldnames for col in ['x', 'y', 'image_path']):
                print(f"Error: CSV file must contain columns 'x', 'y', and 'image_path'. Found: {reader.fieldnames}")
                return
                
            for row_num, row in enumerate(reader):
                line_count += 1
                try:
                    x_coord = float(row['x'])
                    y_coord = float(row['y'])
                    image_full_path = row['image_path']
                    image_filename = os.path.basename(image_full_path)

                    if not image_filename:
                        print(f"Warning: Empty filename derived from path '{image_full_path}' at row {row_num + 2}. Skipping.")
                        error_count += 1
                        continue

                    output_data_list.append({
                        "image": image_filename,
                        "x": x_coord,
                        "y": y_coord
                    })
                    processed_count += 1
                except ValueError as ve:
                    print(f"Warning: Could not convert x/y to float for row {row_num + 2}: {row}. Error: {ve}. Skipping.")
                    error_count += 1
                except Exception as e:
                    print(f"Warning: Error processing row {row_num + 2}: {row}. Error: {e}. Skipping.")
                    error_count += 1
        
        print(f"Read {line_count} data rows from CSV.")
        print(f"Successfully processed {processed_count} rows.")
        if error_count > 0:
            print(f"Skipped {error_count} rows due to errors.")

    except FileNotFoundError:
        print(f"Error: Input CSV file '{csv_file_path}' not found during open.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading CSV '{csv_file_path}': {e}")
        return

    if not output_data_list:
        print("No data was successfully processed. Output JSON will not be created.")
        return

    try:
        with open(output_json_path, 'w', encoding='utf-8') as outfile:
            json.dump(output_data_list, outfile, indent=4)
        print(f"Successfully converted CSV to JSON at '{output_json_path}'")
    except Exception as e:
        print(f"Error writing JSON to '{output_json_path}': {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Converts a CSV file with t-SNE coordinates (x, y) and image paths "
                    "to a JSON file suitable for 2D visualization."
    )
    parser.add_argument(
        "--input_csv", 
        type=str, 
        required=True,
        help="Path to the input CSV file (e.g., micoo/micoo80_tsne.csv). "
             "Must contain 'x', 'y', and 'image_path' columns."
    )
    parser.add_argument(
        "--output_json", 
        type=str, 
        default=None,
        help="Path for the output JSON file (default: images_color_rgb_2D.json in the same directory as input_csv)."
    )

    args = parser.parse_args()

    output_json_path = args.output_json
    if output_json_path is None:
        base_dir = os.path.dirname(args.input_csv) if os.path.dirname(args.input_csv) else '.'
        output_json_path = os.path.join(base_dir, "images_color_rgb_2D.json")
        
    print(f"Starting CSV to 2D JSON conversion...")
    print(f"Input CSV: {args.input_csv}")
    print(f"Output JSON: {output_json_path}")

    convert_csv_to_2d_json(args.input_csv, output_json_path)

    print("Conversion script finished.") 