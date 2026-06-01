# Repository Overview
Data and files concerning NH3 emission mitigation via acidification during slurry applicaton, meassured using dynamic flux chambers (DFCs) connected with cavity ring-down spectroscopy (CRDS).
And modelling of the related to the same experiment.
SOP's and general calculations related to the project has also been uploaded.
Related to the maintainers master thesis under Johanna Pedersen. Project time is/was 2025-08-25 to 2026-06-03.

# Maintainer
Mikael Loevig Larsen
202107228@post.au.dk

# References
Thesis paper will be presented here when made avalable through the university library.

# Description of directories and files
## `Field-trails`
Overviews, data from tests analytical test and calculations for the field-experiments.

* `cats.csv` age and weight of the experimental subjects
* `breath.csv` breath scores from the experiment

### `2025-10-14-intial-lab-titration`
Files specifically relavant to the inital lab titration

### `2025-10-28-field-cattle-slurry`
Files specifically relavant to the field experiment applying cattle slurry

### `2025-11-05-field-pig-slurry`
Files specifically relavant to the field experiment applying pig slurry

## `Lab-Trails`
Overviews, data from analytical tests and calculations for the lab-experiments

### `soil-sample-Ids`
each soil sample has a distint number, denoted in these files

## `Output`
csv-output of CRDS data treatment and modelling.

### `1-inital-extraction`
Stable PPB-data extracted from raw-CRDS dat-files.

### `2-Flux-conversion`
Stable PPB-data converted into flux, outputted here before major data treatment decisions.

### `3-integration`
Background-corrected (inverse ditance weighting) & linearly interpolated flux data, and accumulated emissions.

### `ALFAM2-data-for-template`
Data from field experiments in this work, prepared in the same style as used in the ALFAM2 database.

### `ALFAM2-model-resuts`
Results from the project modelling applying the alfam2 function.

## `ScriptsPython`
Python scripts used in this project, used for CRDS data treatment and for creating report plots.

### `2025-10-14-field-inital-lab-titration-plots`
files used for creating plots for the initial titration.

### `AlFAM2-model-exerimental-comparision`
Files for comparing modelled and experimental data in a plot.

### `ALFAM2-prepping-the-template`
Files for converting treated data in this work into the same structure as used in the ALFRAM2 database (for later uploading).

### `Picarro`
Files for data treatment of the CRDS(Picarro)-data, same script-structure is setup to handle each respective experiment, using the 1-extraction, 2-flux-conversion, 3-integration output-format.

#### `2025-10-28-Field-trail-cattle-slurry`
Files for treating the field experiment applying cattle slurry.

#### `2025-10-28-Field-trail-pig-slurry`
Files for treating the field experiment applying pig slurry.

#### `2026-01-06-Lab-cattle-slurry`
Files for 1st lab acidification experiment applying cattle slurry - not presented in thesis, one of the slurries were potentially switched due to human error.

#### `2026-04-19-Lab-density-test`
Files experiment testing soil homogeneity and density of packing.

#### `2026-01-06-Lab-pig-slurry`
Files for lab acidification experiment applying pig slurry.

#### `2026-01-29-Lab-cattle-retrail`
Files for 1st lab acidification experiment applying cattle slurry - presented in thesis.

#### `picarro legacy`
Former versions of these scripts, for example when the temperature was switched.

##### `Picarro-non-thesis-data`
Inital scripts setup using former experimental data from the same setup provided by J. Pedersen.

## `ScriptsR`
R scripts and related files used in this project for alfam2 modelling.

## `SOPS's`
Collection of used standard operating procedures.

# Variables
(Variables should be described here or in a separate file.
It may be necessary to have separate lists for the different data files.

* `cat_key` unique integer key for each experimental subject
* `breath_score` "breath foulness" index as median of three panelists)
