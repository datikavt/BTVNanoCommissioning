import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser(description="Convert DAS file list to structured JSON.")
    parser.add_argument("-i", "--input", required=True, help="Input text file with ROOT file paths")
    parser.add_argument("-d", "--dataset", required=True, help="Dataset name to use as key in JSON")
    parser.add_argument("-o", "--output", required=True, help="Output JSON filename")

    args = parser.parse_args()

    # Read file paths and prepend redirector
    with open(args.input, "r") as f:
        root_files = [
            "root://xrootd-cms.infn.it/" + line.strip()
            for line in f if line.strip()
        ]

    # Load existing JSON if it exists
    if os.path.exists(args.output):
        with open(args.output, "r") as existing_file:
            try:
                output_data = json.load(existing_file)
            except json.JSONDecodeError:
                print(f"Warning: {args.output} exists but is not a valid JSON file. Starting fresh.")
                output_data = {}
    else:
        output_data = {}

    # Update or add the dataset entry
    output_data[args.dataset] = root_files

    # Write updated JSON
    with open(args.output, "w") as out_file:
        json.dump(output_data, out_file, indent=4)

    print(f"Saved {len(root_files)} entries for dataset '{args.dataset}' to {args.output}")

if __name__ == "__main__":
    main()
