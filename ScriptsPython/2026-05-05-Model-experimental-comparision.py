##### TO-Do / script description #####
# Import experimental plot-level data - TAN df
# Import Model plot-level data
# ensure units of flux are consitent between the 2 datasets 
# Visualize model-data on plot-level, determine whether it makes sense to make the distinction, if not simplify and plot at treatment level for later plots
# Visualize model-data agianst plot-level experimental data

##### Packagages #####
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

##### Functions #####
def load_csv_file_as_df(file_path:Path)-> pd.DataFrame:
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    output: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces

def remove_nan_rows(raw_df:pd.DataFrame) -> pd.DataFrame:
    # might delete this function and simply use dropna directly
    '''
    remove rows containing nan from a df

    Input:
        raw_df: dataframe containing raw datapoints from all valves

    output:
        filtered df: df with nan-containing rows removed
    '''
    copy_df = raw_df.copy() # creating a copy to avid changing raw df
    rows_before = len(copy_df)

    filtered_df = copy_df.dropna(axis = 0, how = 'any') # dropping any rows contaning nan
    rows_after = len(filtered_df)
    removed_rows = rows_before - rows_after
    print(f'number of rows removed is {removed_rows}')
    return filtered_df


##### Input folders #####
# Model-data #
model_path= Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\ALFAM2\Alfam2-model-results\2026-05-21-alfam2_Cattle-th.csv")

# experimental data, plotlvl # 
expt_path= Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\3-intergration\2026-03-16-field-cattle-integrated-valve-lvl-v323.csv")

##### Output folders ####
output_folder_figures = Path(r"C:\Users\mikae\Desktop")
output_name_figure = Path("model-versus-ekpt.pdf")
output_path_figures = output_folder_figures / output_name_figure


##### Script excecution #####
### Model Df ### 

# import the stuff  #
model_df = load_csv_file_as_df(model_path)

# clean collum titles #
model_df.columns = model_df.columns.str.strip().str.replace('"', '')
#print(model_df)

# prepare j collum #
# collum class types
#print(model_df['j'].iloc[0], type(model_df['j'].iloc[0]))
#print(model_df['j'].iloc[1], type(model_df['j'].iloc[1]))
#print(model_df['er'].iloc[0], type(model_df['er'].iloc[0]))

model_df['j'] = pd.to_numeric(model_df['j'], errors='coerce') # ensure number-class
model_df['j'] = model_df['j'].replace(-np.inf, 0) # replace -infs
#print(model_df['j'].iloc[0], type(model_df['j'].iloc[0]))
#print(model_df['j'].iloc[1], type(model_df['j'].iloc[1]))

# remove nan rows #
model_df = remove_nan_rows(model_df)
print(model_df)

# clean every collum #
for col in model_df.select_dtypes(include='object').columns:
    model_df[col] = model_df[col].str.strip().str.replace('"', '')

print(model_df)

# create a mean of the model #
model_mean = (model_df.groupby(['treatment', 'ctime'], as_index=False)['j'].mean())

#### Experimental df ###
expt_df = load_csv_file_as_df(expt_path)
#print(expt_df)

expt_df['flux [kgN/ha h]'] = expt_df['flux [mg/m2 h]'] / 100
print(expt_df)


##### Visualizations #####
# predefine figure-size and resolution, ensure consistency #
FIGSIZE = (6, 4)
DPI = 300

# fonts-types and size and tick control, needs to be defined before all plots
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 18,
    'axes.labelsize': 18,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'ytick.direction': 'in',
    'xtick.direction': 'in',
    'axes.linewidth': 1})

### Plot model-data on a plot-level ####
# ensure color consistency between equvalent treatments
linestyles = ['-', '--', ':']  # 3 scenarios

# define treatment colors
treatment_colors = {
    'AA': 'blue',
    'H2SO4':'orange',
    'RAW': 'black'
}

treatments = model_df['treatment'].unique()

for t_idx, treatment in enumerate(treatments):
    treatment_df = model_df[model_df['treatment'] == treatment]
    scenarios = treatment_df['scenario'].unique()

    for s_idx, scenario in enumerate(scenarios):
        scenario_df = treatment_df[treatment_df['scenario'] == scenario]
        

        plt.plot(scenario_df['ctime'], scenario_df['j'], linestyle=linestyles[s_idx % 3], linewidth = 1,  color = treatment_colors[treatment] , label = treatment if s_idx == 0 else None) 
        # setup to only label once per treatment
        # graps color from the treatment dict, and linestyle from the list

plt.xlim(0, 160)
plt.ylim(0, 0.45)

plt.xlabel("time since application [h]")
plt.ylabel("Flux [kgTAN ha⁻¹ h⁻¹]")

plt.legend()
plt.tight_layout()
#plt.savefig(output_path_figures, dpi=300, bbox_inches='tight')
plt.show()
plt.close()

### expermemtal data, valve-level together with mean from model ###
markers = ['o', 'v', 's'] 

# define treatment colors
treatment_colors = {
    'AA': 'blue',
    'H2SO4':'darkgreen',
    'RAW': 'orangered'
}

treatments = expt_df['TREATMENT'].unique()

for t_idx, treatment in enumerate(treatments):
    treatment_df = expt_df[expt_df['TREATMENT'] == treatment]
    scenarios = treatment_df['VALVE_ID'].unique()

    for s_idx, scenario in enumerate(scenarios):
        scenario_df = treatment_df[treatment_df['VALVE_ID'] == scenario]
        plt.plot(scenario_df['time_since_slurry_aplication[h]'], scenario_df['flux [kgN/ha h]'], linestyle='None' , marker = markers[s_idx % 3], markersize = 1,   color = treatment_colors[treatment] , label =  None) 
        # setup to only label once per treatment
        # graps color from the treatment dict, and linestyle from the list

for t_idx, treatment in enumerate(treatments):
    treatment_df = model_mean[model_mean['treatment'] == treatment]
    plt.plot(treatment_df['ctime'], treatment_df['j'], linewidth = 1, marker = 'D', markersize = 1,  color = treatment_colors[treatment] , label = treatment) 



plt.xlim(0, 160)
plt.ylim(0, 0.45)

plt.xlabel("time since application [h]")
plt.ylabel("Flux [kgTAN ha⁻¹ h⁻¹]")

plt.legend(frameon=False)
plt.tight_layout()
#plt.savefig(output_path_figures, dpi=300, bbox_inches='tight')
plt.show()
plt.close()



