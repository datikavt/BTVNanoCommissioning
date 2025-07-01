from coffea.util import load
import uproot, sys, os, argparse, hist
from BTVNanoCommissioning.helpers.xs_scaler import collate, scaleSumW, scale_xs, getSumW
import numpy as np

parser = argparse.ArgumentParser(description="Make templates from coffea files")
parser.add_argument(
    "-i",
    "--input",
    type=str,
    required=True,
    help="Input coffea file(s)",
)
parser.add_argument(
    "-v",
    "--variable",
    type=str,
    required=True,
    help="Variables to store(histogram name)",
)
parser.add_argument(
    "-a",
    "--axis",
    type=str,
    required=True,
    help="dict, put the slicing of histogram, specify 'sum' option as string",
)
parser.add_argument(
    "--lumi",
    type=float,
    required=True,
    help="Luminosity in /pb",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    required=True,
    help="output root file name",
)
parser.add_argument(
    "--mergemap",
    type=str,
    default=None,
    help="Specify mergemap as dict, '{merge1:[dataset1,dataset2]...}' Also works with the json file with dict",
)


def create_template(inputs, variable, mergemap, axis, lumi, output):
    #NOTE: found that for old frameworks this was used scaleSumW with scale_xs
    # :https://github.com/cms-btv-pog/BTVNanoCommissioning/blob/9ec14fab297d1b77e491cd001b34fd68ca359325/notebooks/make_some_plots.ipynb#L58
    # events = inputs['/user/dkavtara/btv/btvnanocommissioning/hists_ctag_DY_sf_ctag_DY_mu_myfile/hists_ctag_DY_sf_ctag_DY_mu_myfile.coffea']['DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8']["sumw"]
    inputs = scaleSumW(inputs, lumi)
    collated = collate(inputs, mergemap)
    mergemap_all = {"all": [s for s in inputs]}
    merge_all = collate(inputs, {"all": [s for s in inputs]})
    hall = merge_all["all"][variable][axis]

    fout = uproot.recreate(f"{variable}_{output}")
    for data in collated.keys():
        if variable not in collated[data].keys():
            raise f"{variable} not in {data}"
        elif np.sum(collated[data][variable].values()) == 0:
            print(f"0 value in {variable} histogram of {data}, set empty histogram")
            fout[data.replace("-", "_")] = hall
        else:
            fout[data.replace("-", "_")] = collated[data][variable][axis]


if __name__ == "__main__":
    import glob

    arg = parser.parse_args()
    if len(arg.input.split(",")) > 1:
        inputs = {i: load(i) for i in arg.input.split(",")}
    elif "*" in arg.input:
        files = glob.glob(arg.input)
        inputs = {i: load(i) for i in files}
    else:
        inputs = {arg.input: load(arg.input)}
    import json

    if arg.mergemap != None:
        mergemap = (
            json.load(open(arg.mergemap))
            if arg.mergemap.endswith(".json")
            else json.loads(arg.mergemap)
        )
    # if not specify the mergemap, stored per dataset
    else:
        flists = []
        for f in inputs.keys():
            for d in inputs[f].keys():
                flists.append(d)
        mergemap = {d: d for d in flists}
    axis = json.loads(arg.axis)
    # modify axis to hist methods
    for a in axis:
        if axis[a] == "sum":
            axis[a] = sum
    create_template(inputs, arg.variable, mergemap, axis, arg.lumi, arg.output)
