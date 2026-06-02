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

# Description of directories
* `General Calculations` Word-file includes quick "by-hand"-calculations, - check of coding results, derrivations of theoretical equations, and the scaling factor calculation
* `Reductions` Excel-file caclulations for relative and absolute reductions for all experiments - also includes and overview of results although this doesn't contain the later experiments (felt less relevant to update when report writing was started)

## `Field-trails`
Overviews, data from analytical test and calculations for the field-experiments. Includes overview of treatments for each plot, weather, soil(pH, BD, water content), slurry(pH, TAN, DM, acid dosage) and flow-data
* `2025-12-05-field-picarro-callibration` Excel-file, results and data from the Picarro(CRDS) callibration - created by F. Pierre and shared
* `FoulumVejr` 2 CSV-files containing weather data for the respective field experiments
* `Slurry ` Excelfile containing "raw" data for the acidifications (masses of slurry and acids, pH before and after)
* `SlurryData ` Csv-file, contains analytical results for slurry at application for the field experiments (TAN, VFA, pH) - not all were used for this project
* `soil-data ` Excel-file, contains analytical results (water content, BD) and raw data (masses before/after drying) for the soils at application for the field experiments
* `TAN-concentration-and-application-rate ` Excelfile - calculation of the applied TAN [kg ha⁻¹]
* `weather-data-guide ` PNG - description of the different collumns in the wather-files

### `2025-10-14-intial-lab-titration`
Files specifically relavant to the inital lab titration. Contains related pictures, and pH meassured per applied volume - and the conversion of this volume into mass.

### `2025-10-28-field-cattle-slurry`
Files specifically relavant to the field experiment applying cattle slurry. Includes and overview of the DFC and thier respective flows, and the applied treatments.

### `2025-11-05-field-pig-slurry`
Files specifically relavant to the field experiment applying cattle slurry. Includes and overview of the DFC and thier respective flows, and the applied treatments.

## `Lab-Trails`
Overviews, data from analytical tests and calculations for the lab-experiments. Includes overview of treatment for each sample, slurry(pH, TAN, DM, acid dosage) soil(BD, water content), flow-data, calculations of the application rates and the calculations for preparing the packed soils.

### `soil-sample-Ids`
each soil sample has a distint number, denoted in these files in the case they had been switched.

## `Output`
csv-output of CRDS data treatment and modelling. There is also a txt-file which explains changes between script versions

### `1-inital-extraction`
Stable PPB-data extracted from raw-CRDS dat-files.

### `2-Flux-conversion`
Stable PPB-data converted into flux, outputted here before major data treatment forks.

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

### `ALFAM2-prepping-the-template`
Scripts for converting treated data in this work into the same structure as used in the ALFRAM2 database (for later uploading).

### `Picarro`
Files for data treatment of the CRDS(Picarro)-data, same script-structure is setup to handle each respective experiment, using the 1-extraction, 2-flux-conversion, 3-integration output-format.

#### `2025-10-28-Field-trail-cattle-slurry`
Files for treating the field experiment applying cattle slurry. This one also contains an addtional script compared to the other where constant extrapolation of an inital data-loss was applied

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
Former versions of these scripts, for example when the temperature was switched, as a sensor bellow gorund was mistakenly used initally. A txt-file in the output denotes changes in the applied versions

##### `Picarro-non-thesis-data`
Inital scripts setup using former experimental data from the same setup provided by J. Pedersen.

## `ScriptsR`
R scripts and related files used in this project for alfam2 modelling.
* `ALFAM2-Field-cattle-slurry` R-file actual simulation file
* `ALFAM2-Field-cattle-slurry-inital-test` R-file Inital tests only with final results
* `par_comb_AUDFC` Csv-file, Generic and specific function-paramters, to compare
* `pars_AUDFC` Csv-file Au-specific function paramters
* `weather-data-field-cattle` csv-file weather data with the 160 hours relevant for this simulation extracted

## `SOPS's`
Collection of used standard operating procedures.
