import json
import subprocess
import os
import argparse
from urllib.parse import urlparse

def main():
    parser = argparse.ArgumentParser(description="Copy ROOT files listed in a JSON file with xrdcp.")
    parser.add_argument("-j", "--json", required=True, help="Input JSON file with dataset -> file URLs")
    parser.add_argument("-b", "--base-dir", required=True, help="Base directory to copy files into")
    args = parser.parse_args()

    with open(args.json, "r") as f:
        data = json.load(f)

    for dataset, files in data.items():
        # Create dataset directory inside base-dir
        dataset_dir = os.path.join(args.base_dir, dataset)
        os.makedirs(dataset_dir, exist_ok=True)

        for url in files:
            # Extract filename from URL
            path = urlparse(url).path
            filename = os.path.basename(path)

            dest_path = os.path.join(dataset_dir, filename)

            print(f"Copying {url} -> {dest_path}")
            result = subprocess.run(["xrdcp", url, dest_path])
            if result.returncode != 0:
                print(f"Error copying {url}")

if __name__ == "__main__":
    main()
