##### Packagages #####
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


##### Script Excecutions #####
# Import paths
input_path_interp = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\3-intergration\2026-03-12-field-cattle-integrated-v323.csv")
input_path_extrap = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\3-intergration\2026-05-22-field-cattle-extrap-treatment-lvl.csv")

# Import the dfs
interp_df = load_csv_file_as_df(input_path_interp)
#print(interp_df)
extrap_df = load_csv_file_as_df(input_path_extrap)
#print(extrap_df)

#### Visuals #####
# predefine figure-size and resolution, ensure consistency #
FIGSIZE = (6, 4)
DPI = 300

# fonts-types and size and tick control, needs to be defined before all plots for common style
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 18,
    'axes.labelsize': 18,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'ytick.direction': 'in',
    'xtick.direction': 'in',
    'axes.linewidth': 1})

### Plot of relative flux for all merged treatments ###
plt.figure(figsize=(FIGSIZE)) # predefine the figure size
treatment_colors = {'AA': 'blue','RAW': 'darkorange','H2SO4': 'darkgreen'} # treatment colors
treatment_names = {'AA': 'AA','RAW': 'None','H2SO4': 'SA'} # treatment names
    
# determine unique treatments in merged df
for treatment in sorted(interp_df['TREATMENT'].unique()):
    ### Interpolation ### 
    treatment_df = interp_df[interp_df['TREATMENT'] == treatment]

    # determine the time range of the interpolation
    interp_x_min = treatment_df['time_since_start_of_experiment'].min()
    interp_x_max = treatment_df['time_since_start_of_experiment'].max()

    # extract relevant data
    t_treatment = treatment_df['time_since_start_of_experiment']
    Rel_F = treatment_df['relative_flux']
    Rel_F_stdev = treatment_df['relative_flux_std_dev']

    label = treatment_names.get(treatment, treatment)  # Fallback to original if not found
    color = treatment_colors.get(treatment, 'gray')  # Default to gray if treatment not in mapping
    plt.plot(t_treatment, Rel_F, '-', color = color, label = label, linewidth = 1.5)
    plt.fill_between(t_treatment, Rel_F - Rel_F_stdev, Rel_F + Rel_F_stdev, alpha = 0.3, color = color)

    ### Extrapolation ###
    ext_df = extrap_df[extrap_df['TREATMENT'] == treatment]

    # Filter the df
    ext_filtered = ext_df[(ext_df['time_since_start_of_experiment'] < interp_x_min) | (ext_df['time_since_start_of_experiment'] > interp_x_max)]

    if not ext_filtered.empty:
        plt.plot(ext_filtered['time_since_start_of_experiment'], ext_filtered['relative_flux'],'--', color=color, linewidth=1.5)
        plt.fill_between(ext_filtered['time_since_start_of_experiment'], ext_filtered['relative_flux'] - ext_filtered['relative_flux_std_dev'], ext_filtered['relative_flux'] + ext_filtered['relative_flux_std_dev'], alpha = 0.3, color = color)

### Prepare the figure ###
# x- and y-axis
plt.xlabel('Time Since Application [h]')
plt.xlim(0, 160)
plt.ylabel('Relative flux (% of TAN) [h⁻¹]')
plt.ylim(auto = True)

# legend
plt.legend(frameon=False)

# save/show
plt.tight_layout()
#plt.savefig(output_path_figures, dpi=300, bbox_inches='tight')
plt.show()
plt.close()
