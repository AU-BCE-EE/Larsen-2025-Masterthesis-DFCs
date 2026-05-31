# Repository Overview
Data and files concerning NH3 emission mitigation from manure meassured using dynamic flux chambers (DFCs)
And modelling of the related to the same experiment
SOP's and general calculations related to the project has also been uploaded
Related to the maintainers master thesis under Johanna Pedersen
Project time is 2025-08-25 to 2026-06-03

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

## `Lab-Trails/`
Overviews, data from analytical tests and calculations for the lab-experiments

-` Lab-Trails/soil-sample-Ids`
each soil sample has a distint number, denoted here

## `Output`
csv-output of CRDS data treatment and modelling.

## `ScriptsPython`
Python scripts used in this project, used for CRDS data treatment and for creating repport plots

## `ScriptsR`
R scripts used in this project, used for ALFAM2 modelling

## `SOPS's`
Collection of used standard operating procedures

# Variables
(Variables should be described here or in a separate file.
It may be necessary to have separate lists for the different data files.

* `cat_key` unique integer key for each experimental subject
* `breath_score` "breath foulness" index as median of three panelists)
