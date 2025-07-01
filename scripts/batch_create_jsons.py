import subprocess
import os

input_list = "/user/dkavtara/MuonEG_Run2017B-F.txt"
output_json = "/user/dkavtara/btv/btvnanocommissioning/metadata/94X/MuonEG_Run2017B-F.json"
create_script = "create_data_jsons.py"

redirector = "root://xrootd-cms.infn.it/"

with open(input_list) as f:
    datasets = [line.strip() for line in f if line.strip()]

for dataset in datasets:
    print(f"Processing {dataset}")
    short_name = dataset.split("/")[1] + "_" + dataset.split("/")[2].split("-")[0]  # e.g. Run2017B

    # Query DAS to get file list
    file_list = subprocess.run(
        ["dasgoclient", "-query", f"file dataset={dataset}"],
        capture_output=True, text=True
    ).stdout.strip().splitlines()

    if not file_list:
        print(f"Warning: No files found for {dataset}")
        continue

    temp_txt = f"tmp_{short_name}.txt"
    with open(temp_txt, "w") as temp_file:
        temp_file.write("\n".join(file_list))

    # Run create_data_jsons.py
    subprocess.run([
        "python3", create_script,
        "-i", temp_txt,
        "-d", short_name,
        "-o", output_json
    ])

    # Clean up temp file
    os.remove(temp_txt)
