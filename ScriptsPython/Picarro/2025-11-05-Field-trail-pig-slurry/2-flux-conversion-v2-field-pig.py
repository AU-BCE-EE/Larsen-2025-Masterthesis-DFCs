### Script Description ###

### Packages ###
from math import pi
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


##### Functions #####
def load_csv_file_as_df(file_path: Path) -> pd.DataFrame:
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    returns: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces

def make_datetime_weather(df: pd.DataFrame) -> pd.DataFrame:
    '''
    combines data and time collums found in weather_data, and convert these into a time object
    
    input: df containing 'date' and 'time' collums

    Returns: df contaning 'DATE_TIME' collum as a time object
    '''
    copy_df = df.copy()

    if 'DATE_TIME' in copy_df.columns:
        print('DATE_TIME collum already created')
        return copy_df

    else:
        copy_df['DATE_TIME'] = copy_df['date'].astype(str) + ' ' + copy_df['time'].astype(str) # combines the time and date id's in a single new collum
        copy_df['DATE_TIME'] = pd.to_datetime(copy_df['DATE_TIME'], format="%d/%m/%Y %H")
        copy_df = copy_df.drop(columns=['date', 'time']) # remmoving individual time and date collums
        return copy_df


def add_weather_conditions(picarro_input_df: pd.DataFrame, weather_input_df: pd.DataFrame) -> pd.DataFrame:
    '''
    adds additional collums with weather-data to a dataframe with measurements extraced from the picarro-file, 
    matching via the DATA_TIME collums present in both dataframes

    input: data_df dataframe with picarro_data. weather_df dataframe with weather data

    Returns: df with picarro data and collums with weather-paramers for further calculations 
    '''
      # Ensure datetime columns are proper datetime objects
    picarro_df = picarro_input_df.copy()
    weather_df = weather_input_df.copy()

    picarro_df['DATE_TIME'] = pd.to_datetime(picarro_df['DATE_TIME'])
    weather_df['DATE_TIME'] = pd.to_datetime(weather_df['DATE_TIME'])

    # Sort both dataframes by DATE_TIME (required for merge_asof)
    picarro_df = picarro_df.sort_values('DATE_TIME')
    weather_df = weather_df.sort_values('DATE_TIME')

    # Select relevant weather columns
    weather_selected = weather_df[['DATE_TIME', 'megrtp', 'pres']]

    # merging the weather_data into the data_df
    merged_df = pd.merge_asof(picarro_df, weather_selected, on='DATE_TIME', direction='nearest')  # use last known weather before measurement
    merged_df = merged_df.rename(columns={"megrtp": "T[degc]","pres": "P_ATMOS[hpa]"})
    return merged_df


def add_presure_drop(input_df: pd.DataFrame, preasure_drop_dict: dict) -> pd.DataFrame:
    '''
     Add and addtional collum with slurry preasure drop for each dfc using .map().

    Input:
        df - dataframe with VALVE_ID collum present
        method: dict with ints (valve ids) as keys, and str as values (methods).
    
    Returns: 
        df with additional collum with presure drop
    '''
    if "VALVE_ID" not in input_df.columns:
        raise ValueError("VALVE_ID column not present")
    
    else:
        df = input_df.copy()
        df['P_DROP[pa]'] = df[f"VALVE_ID"].astype('Int64').map(preasure_drop_dict) # using .map() to add a new collum with method ID, using the valve id
       
    return df


def flux_conversion_nonconst_weather(input_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Converting concentration-measurements [PPB] and related std-deviation into fluxes [mg/m2 h], adding them as new collums in the df assuming constant weather conditons
    
    input:
        DF with C[PPB] and C_STDEV[PPB] collum P[hpa] and T_GROUND_10cm[DEGC] as collums

    returns:
        DF previusly mentioned, with flux-collums added
    '''
    df = input_df.copy()

    # Initalization of constants
    R = 8.205736 * 10**(-5) # Ideal gas constant [m3 atm / K mol]
    MW_N = 14 * 10**3 # molecular weight of elementary nitrogen [mg/mol]
    D = 0.7 # chamber diameter [m]
    A = (D/2)**2 * pi # area enclosed by single chamber
    K = 3 # emperical chamber dependent constant, presuredrop and flow relation at restriction 
    
    # Gathering needed collums from df:
    C_PPB = df['C[PPB]']
    C_PPB_stdev = df['C_STDEV[PPB]']
    T = df['T[degc]'] + 273.15 # degrees celsius to kelvin
    P = df['P_ATMOS[hpa]'] * 0.000987 # hpa to atm
    dP = df['P_DROP[pa]']

    # Intermediary mass/volume [mg/m3] calcualtion using ideal gas equaton
    C_mass = C_PPB * (P / (R * T)) * MW_N * 10**(-9) # [mg/m3]
    C_mass_stdev = C_PPB_stdev * (P / (R * T)) * MW_N * 10**(-9) # [mg/m3]

    # flux_calculation
    Q =  K * (dP**0.5) # Q [L/s]
    Q = Q * 3600 # [L/h]
    Q = Q / 1000 # [m3 / h]
    df['F[mg/h m2]'] = (C_mass * Q) / A # ([mg/m3] [m3/h]) / [m2] = [mg / h m2]
    df['F_STDEV[mg/h m2]'] = (C_mass_stdev * Q) / A # ([mg/m3] [m3/h]) / [m2] = [mg / h m2]

    return df


def save_df_as_csv(df: pd.DataFrame, output_folder: Path, output_file_name: Path, overwrite = True):
    '''
    saves a df as a csv-file in a designated outputfolder

    Input:
        df: the dataframe to be saved
        outputfolder(path object): the file-path of the output folder
        output_file_name(path object): wanted name of the created file
        overwrite(BOOl): designate whether the function should overwrite an existing file
    '''
    output_file = output_folder / f"{output_file_name}.csv"

    if output_file.exists() and not overwrite:
        print(f"The file with the following name already exist: {output_file.name}")
        return

    elif output_file.exists():
        print('previous file overwritten')

    df.to_csv(output_file, index=False)
    print(f" output_file saved as: {output_file}")


##### Input folders and files #####
input_path_weather = Path(r"C:\Users\mikae\Desktop\Github - speciale\AgrosceNa-NEXT\data\weather\FoulumVejr_0110_1711.csv") #Weather data
input_path_picarro = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\1-inital-extraction\2026-03-12-field-pig-extracted-v3.csv") # picarro data

### Output folders and files ###
output_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\2-flux-conversion")
output_file_name = Path('2026-03-12-field-pig-flux-v32')

# Figures #
output_folder_figures = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Report Graphs")
output_name_figure = Path("graph-2026-05-25-field-pig-temperature.pdf")
output_path_figures = output_folder_figures / output_name_figure

##### Constants #####
preasure_drop_dict = {1: 132.8, 2: 123.1, 3: 122.6, 4: 122.7, 5: 122.7, 6: 125.5, 7: 128.8, 8: 126.9, 9: 126.9,
10: 129.4, 11: 121.4, 12: 124.3, 13: 125.0, 14: 126.5, 15: 143.1, 15: 143.1, 16: 141.1, 17: 135.3, 18: 125.4, 19: 129.3} # delta pa

##### Script Excecution #####
weather_df = load_csv_file_as_df(input_path_weather)
#print(weather_df)

weather_df = make_datetime_weather(weather_df)
#print(weather_df)

picarro_df = load_csv_file_as_df(input_path_picarro)
#print(picarro_df)

combined_df = add_weather_conditions(picarro_df, weather_df)
#print(combined_df)

combined_df = add_presure_drop(combined_df, preasure_drop_dict)

flux_df = flux_conversion_nonconst_weather(combined_df)
#print(flux_df)

#save_df_as_csv(flux_df, output_folder, output_file_name, overwrite = True)

##### Weather stats ######
# Need:
# - temperature data of soil and grass-level (also 2 m?), base statistics and a graph
# - precipitation, total precipitation and a graph
# wind, required for modelling

# Filter weather based on experimental start and end
start_dateTime = picarro_df["DATE_TIME"].iloc[0]
end_dateTime = picarro_df["DATE_TIME"].iloc[-1]
filtered_weather_df  = weather_df[(weather_df['DATE_TIME'] >= start_dateTime) & (weather_df['DATE_TIME'] <= end_dateTime)].copy()
#print(filtered_weather_df)

# Create delta-time column
filtered_weather_df['delta-t'] = (
    filtered_weather_df['DATE_TIME'] -
    filtered_weather_df['DATE_TIME'].iloc[0]
).dt.total_seconds() / 3600
#
# print(filtered_weather_df.head(50))

# Basic temperature stistics
T = filtered_weather_df['megrtp']
T_min = round(T.min(), 1)
T_mean = round(T.mean(), 1)
T_max = round(T.max() , 1) 
T_median = round(T.median() , 1) 
print(f'Temperature during the experiment was (min, median, mean, max): ({T_min}, {T_median}, {T_mean}, {T_max}) degrees celsius \n')

# more info on when the highest temperature occured
#max_temp_rows = flux_df[flux_df['T[degc]'] == T_max] # creating a bool
#print('additional info on the max temperature: \n', max_temp_rows[['TIME_NORM_GLOBAL[h]', 'F[mg/h m2]', 'T[degc]']])

### Determine total rainfall ###
cum_railfall = filtered_weather_df['prec'].sum()
print(f'total rainfall was {cum_railfall} mm \n')

##### Visuals ##### 
# global figure size and DPI
FIGSIZE = (6, 4)
DPI = 300

# fonts-types and size and tick control, needs to be defined before all plots
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'ytick.direction': 'in',
    'xtick.direction': 'in',
    'axes.linewidth': 1
})

### Weather data ###
# Temperatures #
plt.figure(figsize=(FIGSIZE)) # predefine the figure size

# plotted data
t = filtered_weather_df['delta-t']
T_grass = filtered_weather_df['megrtp'] # y, T [degc] 20 cm above ground
plt.plot(t, T_grass, '.-', color='black', linewidth=1.5)

# axis
plt.xlabel('Time Since first Application [h]')
plt.ylabel('Temperature [°C]')
plt.xlim(0, 165)
plt.ylim(0, 17)

# legend

# save/show
plt.tight_layout()
plt.savefig(output_path_figures, dpi=DPI, bbox_inches='tight')
plt.show()
plt.close() 

### Flux data ###
def preliminary_visualization2(df: pd.DataFrame, y_col: str, yerr_col: str, valve_lvl=False):
    xcol = 'TIME_NORM_GLOBAL[h]'

    if not valve_lvl:
        for treatment, t_data in df.groupby('TREATMENT'):
            t_data = t_data.sort_values(xcol)
            x = t_data[xcol]
            y = t_data[y_col]
            s = t_data[yerr_col]

            plt.errorbar(x, y, yerr=s, fmt='.', capsize=1, label=treatment)

        plt.xlabel('Global time [h]')
        plt.ylabel(y_col)
        plt.legend(frameon=False, loc='center left', bbox_to_anchor=(1, 0.5))

        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.show()
        return

    # valve-level version
    treatments = df['TREATMENT'].unique()
    fig, axes = plt.subplots(len(treatments), 1, sharex=True,
                             figsize=(10, 3*len(treatments)))

    if len(treatments) == 1:
        axes = [axes]

    for ax, (trt, t_data) in zip(axes, df.groupby('TREATMENT')):

        for valve, v_data in t_data.groupby('VALVE_ID'):
            v_data = v_data.sort_values(xcol)
            ax.errorbar(v_data[xcol],
                        v_data[y_col],
                        yerr=v_data[yerr_col],
                        fmt='.',
                        capsize=1,
                        label=str(valve))

        ax.set_title(str(trt))
        ax.legend(frameon=False, loc='center left', bbox_to_anchor=(1, 0.5))

    plt.xlabel('Global time [h]')
    fig.supylabel(y_col)
    plt.show()

#preliminary_visualization2(combined_df,'F[mg/h m2]','F_STDEV[mg/h m2]', valve_lvl = True)
#preliminary_visualization2(combined_df,'TAN_RATE[1/h]','TAN_RATE_STDEV[1/h]', valve_lvl = False )


### Code references ###
