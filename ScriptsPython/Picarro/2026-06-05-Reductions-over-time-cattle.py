### Packages ###
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# uniform axis aestetics
# uniform axis aestetics
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'ytick.direction': 'in',
    'xtick.direction': 'in',
    'axes.linewidth': 1})

### functions ###
def load_csv_file_as_df(file_path:Path)-> pd.DataFrame:
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    output: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces

### constants ###
# input-folders
Path_field = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\3-intergration\2026-06-05-field-cattle-extrap-valve-lvl.csv")
Path_lab = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\3-intergration\2026-06-05-lab-cattleRetrail-integrated-replicate_lvl.csv")

# output-folder
output_folder_figures = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Report Graphs")
output_name_figure = Path("graph-2026-06-05-relative-reductions-over-time")
output_path_figures = output_folder_figures / output_name_figure


### Function-calls & script excecution ###
field_df = load_csv_file_as_df(Path_field)
#print(field_df)
lab_df = load_csv_file_as_df(Path_lab)
lab_df = lab_df[lab_df["TREATMENT"] != "STD"] # AC stds don't make sense for this plot
#print(lab_df)

all_results = []
### field results ### 
# determine relative reductions across experimental time

raw_mean = (field_df[field_df["TREATMENT"] == "RAW"].groupby("time_since_slurry_aplication[h]")["%_relative_accumulated_emissions"] .mean()) # determine reference mean of each time-stamp
#print(raw_mean)

# insert the reference mean collum back into the df
raw_mean.index = raw_mean.index.round(4)
field_df["time_rounded"] = field_df["time_since_slurry_aplication[h]"].round(4)
field_df["accum_ref_mean"] = field_df["time_rounded"].map(raw_mean)

# calculate relative reductions for each treatment time-stamp
field_df["R_i"] = (1 - (field_df["%_relative_accumulated_emissions"] / field_df["accum_ref_mean"])) * 100

# determine mean and stdev relative reductions for each treatment
field_result = (field_df[field_df["TREATMENT"] != "RAW"].groupby(["TREATMENT", "time_since_slurry_aplication[h]"])["R_i"].agg(mean_R=("mean"), sd_R=("std")).reset_index())
#print(result)

field_result = field_result.dropna(subset=["mean_R"])  # clean field result consistently
field_result["sample_type"] = "Field"
all_results.append(field_result)

#print(all_results)
### Laboratory results ###

lab_df["sample_type"] = lab_df["TREATMENT"].str[0] # grap first character denoting sample type (F and P)

# for both sample types
for sample, group in lab_df.groupby("sample_type"):
    ref_label = sample + "RAW"  # becomes "FRAW" or "PRAW"
    
    # determine reference mean for each time-stamp
    raw_mean = (group[group["TREATMENT"] == ref_label].groupby("time_since_slurry_aplication[h]")["%_relative_accumulated_emissions"].mean())
    
    # determine relative reductions
    raw_mean.index = raw_mean.index.round(4)
    group = group.copy()  # avoids pandas SettingWithCopyWarning
    group["time_rounded"] = group["time_since_slurry_aplication[h]"].round(4)
    group["accum_ref_mean"] = group["time_rounded"].map(raw_mean)
    group["R_i"] = (1 - (group["%_relative_accumulated_emissions"] / group["accum_ref_mean"])) * 100
    
    # determine mean and stdev of each sample-type
    result = (group[group["TREATMENT"] != ref_label].groupby(["TREATMENT", "time_since_slurry_aplication[h]"])["R_i"].agg(mean_R=("mean"), sd_R=("std")).reset_index())
    
    # combine results from each
    result["sample_type"] = sample  # keep track of which group this came from
    all_results.append(result)

all_results = pd.concat(all_results).dropna(subset=["mean_R"])
all_results = all_results[all_results["sample_type"] != "F"] # remove F samples
#print(all_results)


# plot the stuff
style_map = {"Field": "-", "F": "--", "P": "--"}

color_map = {
    ("Field", "AA"):    "darkblue",
    ("Field", "H2SO4"): "darkgreen",
    ("P", "PAA"):       "blue",
    ("P", "PH2SO4"):    "green", 
}

label_map = {
    ("Field", "AA"):    "Field AA",
    ("Field", "H2SO4"): "Field  SA",
    ("P", "PAA"):       "P AA",
    ("P", "PH2SO4"):    "P  SA",
}

fig, ax = plt.subplots(figsize=(10, 5))

for (sample_type, treatment), group in all_results.groupby(["sample_type", "TREATMENT"]):
    color = color_map.get((sample_type, treatment), "black")
    label = label_map.get((sample_type, treatment), f"{sample_type} - {treatment}")
    
    line, = ax.plot(
        group["time_since_slurry_aplication[h]"],
        group["mean_R"],
        linewidth = 2,
        linestyle=style_map.get(sample_type, "-"),
        label = label,
        color = color 
    )
    ax.fill_between(
        group["time_since_slurry_aplication[h]"],
        group["mean_R"] - group["sd_R"],
        group["mean_R"] + group["sd_R"],
        color=line.get_color(),
        alpha=0.1
    )


ax.set_xlabel("Time since slurry application [h]")
ax.set_ylabel("Relative reduction (%)")
plt.xlim(0, 160)
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig(output_path_figures, dpi=300, bbox_inches='tight')
plt.show()
plt.close

