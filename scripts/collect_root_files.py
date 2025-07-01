import os
import json
import argparse

def collect_root_files(base_dir):
    result = {}
    base_dir = os.path.abspath(base_dir)

    for subdir in os.listdir(base_dir):
        full_subdir_path = os.path.join(base_dir, subdir)
        if os.path.isdir(full_subdir_path):
            root_files = []
            for root, _, files in os.walk(full_subdir_path):
                for f in files:
                    if f.endswith(".root"):
                        root_files.append(os.path.abspath(os.path.join(root, f)))
            if root_files:
                result[subdir] = root_files

    return result

def main():
    parser = argparse.ArgumentParser(description="Dump ROOT file paths from subdirs into JSON")
    parser.add_argument("-i", "--input", required=True, help="Base directory to search")
    parser.add_argument("-o", "--output", required=True, help="Output JSON file")

    args = parser.parse_args()
    output_data = collect_root_files(args.input)

    with open(args.output, "w") as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Wrote {len(output_data)} dataset(s) to {args.output}")

if __name__ == "__main__":
    main()
