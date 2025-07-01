from BTVNanoCommissioning.helpers.func import update
from BTVNanoCommissioning.utils.correction import add_jec_variables
import numpy as np
import re
import awkward as ak


def missing_branch(events):
    """
    Add missing branches or rename branches in the `events` object.

    This function adds missing branches or renames existing branches in the `events` object using the `missing_branch` parameter.

    Usage:
    Use the `hasattr` function to check for missing branches.

    Deprecated:
    The `add_jec` function is deprecated. Please use the `JME_shifts` function in the `correction` module instead.

    Example:
    ```python
    events.fixedGridRhoFastjetAll = (
        events.fixedGridRhoFastjetAll
        if hasattr(events, "fixedGridRhoFastjetAll")
        else events.Rho.fixedGridRhoFastjetAll
    )
    ```

    Parameters:
    events (coffea.nanoaodevents): The events object to update.
    missing_branch (str): The name of the missing branch to add or rename.

    Returns:
    events (coffea.nanoaodevents): Events with updated branches.

    """
    # Function implementation here
    # Try NanoAOD-style first
    if hasattr(events, "fixedGridRhoFastjetAll"):
        events["fixedGridRhoFastjetAll"] = events.fixedGridRhoFastjetAll
    # Then try if it's in a sub-collection like Rho (NanoAODv10+ sometimes does this)    
    elif hasattr(events, "Rho") and hasattr(events.Rho, "fixedGridRhoFastjetAll"):
        events["fixedGridRhoFastjetAll"] = events.Rho.fixedGridRhoFastjetAll
    # Then try RECO-style naming with full key name    
    elif "double" in events.fields:
        print("Checking 'double' collection for fixedGridRhoFastjetAll...")

        # Check inside the 'double' collection
        for key in events["double"].fields:
            if key.endswith("double_fixedGridRhoFastjetAll__RECO.obj"):
                print("Matched RECO rho key:", key)
                events["fixedGridRhoFastjetAll"] = events["double"][key]
                break
        else:
            raise RuntimeError("Could not find fixedGridRhoFastjetAll in 'double' collection.")

    else:
        raise RuntimeError("Could not find fixedGridRhoFastjetAll in any known form.")



    # Try assigning 'Jet' if not present but alternatives exist
    if not hasattr(events, "Jet"):
        possible_jet_keys = ["patJets", "recoCaloJets", "recoPFJets", "slimmedJets"]  # Add others as needed
        for key in possible_jet_keys:
            if hasattr(events, key):
                events.Jet = events[key]
                break
        else:
            print("Warning: No Jet collection found, skipping Jet-related updates.")
            return events  # Early return; Jet logic can't proceed    
            
    ## calculate missing nodes

    if not hasattr(events.Jet, "btagDeepFlavB"):
        jets = events.Jet
        if not hasattr(events.Jet, "btagDeepFlavB_b"):
            # If btagDeepFlavB_b is not present, we need to extract it from userFloat labels
            # These are the label strings we want to find in the userFloat labels
            target_labels = {
                "btagDeepFlavB_b": "btagDeepFlavB:b",
                "btagDeepFlavB_bb": "btagDeepFlavB:bb",
                "btagDeepFlavB_lepb": "btagDeepFlavB:lepb"
            }

            labels = jets["slimmedJets__PAT./patJets_slimmedJets__PAT.obj/patJets_slimmedJets__PAT.obj.userFloatLabels_"]
            values = jets["slimmedJets__PAT./patJets_slimmedJets__PAT.obj/patJets_slimmedJets__PAT.obj.userFloats_"]

            for outname, label in target_labels.items():
                found_mask = ak.any(labels == label, axis=1)

                # Use ak.where to build index only where label exists
                indices = ak.where(labels == label, ak.local_index(labels, axis=1), -1)
                index_per_jet = ak.max(indices, axis=1)

                # Extract values only where found
                extracted = ak.fill_none(
                    ak.where(
                        found_mask,
                        values[ak.local_index(values, axis=1), index_per_jet],
                        -1.0  # or np.nan
                    ),
                    -1.0
                )

                jets[outname] = extracted

        # Combine components
        jets["btagDeepFlavB"] = (
            jets["btagDeepFlavB_b"]
            + jets["btagDeepFlavB_bb"]
            + jets["btagDeepFlavB_lepb"]
        )

        # Update back to events
        events.Jet = update(jets, {"btagDeepFlavB": jets.btagDeepFlavB})
    if (
        hasattr(events.Jet, "btagDeepFlavCvL")
        and hasattr(events.Jet, "btagDeepFlavUDS")
        and not hasattr(events.Jet, "btagDeepFlavC")
    ):
        jets = events.Jet
        jets["btagDeepFlavC"] = (
            events.Jet.btagDeepFlavCvL / (1.0 - events.Jet.btagDeepFlavCvL)
        ) * (events.Jet.btagDeepFlavG + events.Jet.btagDeepFlavUDS)
        events.Jet = update(
            events.Jet,
            {"btagDeepFlavC": jets.btagDeepFlavC},
        )
    if hasattr(events.Jet, "btagDeepFlavCvB") and not hasattr(
        events.Jet, "btagDeepFlavC"
    ):
        jets = events.Jet
        jets["btagDeepFlavC"] = (
            events.Jet.btagDeepFlavCvB / (1.0 - events.Jet.btagDeepFlavCvB)
        ) * (events.Jet.btagDeepFlavB)
        events.Jet = update(
            events.Jet,
            {"btagDeepFlavC": jets.btagDeepFlavC},
        )
    if hasattr(events.Jet, "btagDeepFlavC") and not hasattr(
        events.Jet, "btagDeepFlavCvL"
    ):
        jets = events.Jet
        jets["btagDeepFlavCvL"] = np.maximum(
            np.minimum(
                np.where(
                    ((events.Jet.btagDeepFlavC / (1.0 - events.Jet.btagDeepFlavB)) > 0)
                    & (events.Jet.pt > 15),
                    (events.Jet.btagDeepFlavC / (1.0 - events.Jet.btagDeepFlavB)),
                    -1,
                ),
                0.999999,
            ),
            -1,
        )
        jets["btagDeepFlavCvB"] = np.maximum(
            np.minimum(
                np.where(
                    (
                        (
                            events.Jet.btagDeepFlavC
                            / (events.Jet.btagDeepFlavC + events.Jet.btagDeepFlavB)
                        )
                        > 0
                    )
                    & (events.Jet.pt > 15),
                    (
                        events.Jet.btagDeepFlavC
                        / (events.Jet.btagDeepFlavC + events.Jet.btagDeepFlavB)
                    ),
                    -1,
                ),
                0.999999,
            ),
            -1,
        )
        events.Jet = update(
            events.Jet,
            {
                "btagDeepFlavCvL": jets.btagDeepFlavCvL,
                "btagDeepFlavCvB": jets.btagDeepFlavCvB,
            },
        )
    if not hasattr(events.Jet, "btagPNetCvNotB") and hasattr(events.Jet, "btagPNetB"):
        jets = events.Jet
        jets["btagPNetCvNotB"] = (
            jets.btagPNetCvB * jets.btagPNetB / (1.0 - jets.btagPNetB) ** 2
        )
        events.Jet = update(
            events.Jet,
            {"btagPNetCvNotB": jets.btagPNetCvNotB},
        )
    if not hasattr(events.Jet, "btagRobustParTAK4CvNotB") and hasattr(
        events.Jet, "btagRobustParTAK4B"
    ):
        jets = events.Jet
        jets["btagRobustParTAK4CvNotB"] = (
            jets.btagRobustParTAK4CvB
            * jets.btagRobustParTAK4B
            / (1.0 - jets.btagRobustParTAK4B) ** 2
        )
        events.Jet = update(
            events.Jet,
            {"btagRobustParTAK4CvNotB": jets.btagRobustParTAK4CvNotB},
        )
    if hasattr(events, "METFixEE2017"):
        events.MET = events.METFixEE2017
    if hasattr(events.PuppiMET, "ptUnclusteredUp") and not hasattr(
        events.PuppiMET, "MetUnclustEnUpDeltaX"
    ):
        met = events.PuppiMET
        met["MetUnclustEnUpDeltaX"] = (met.ptUnclusteredUp - met.pt) * np.cos(
            met.phiUnclusteredUp
        )
        met["MetUnclustEnUpDeltaY"] = (met.ptUnclusteredUp - met.pt) * np.sin(
            met.phiUnclusteredUp
        )
        events.PuppiMET = update(
            events.PuppiMET,
            {
                "MetUnclustEnUpDeltaX": met.MetUnclustEnUpDeltaX,
                "MetUnclustEnUpDeltaY": met.MetUnclustEnUpDeltaY,
            },
        )
    return events
