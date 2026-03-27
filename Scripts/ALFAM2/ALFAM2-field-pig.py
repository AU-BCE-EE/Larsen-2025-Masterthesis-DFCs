##### Script Description #####
# Prepare flux-data and other parameters to fit ALFAM2 submission template

##### Packages #####
from pathlib import Path
import numpy as np
import pandas as pd

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
    weather_selected = weather_df[['DATE_TIME', 'mesotp10', 'prec']]

    # merging the weather_data into the data_df
    merged_df = pd.merge_asof(picarro_df, weather_selected, on='DATE_TIME', direction='nearest')  # use last known weather before measurement
    merged_df = merged_df.rename(columns={"mesotp10": "T_10cm[degc]"})
    return merged_df

def background_correction(filtered_df:pd.DataFrame, power:int = 2) -> pd.DataFrame:
    '''
    Finds bacground-corrected flux (F_BC) via inverse distance weiging of the 3 closest background-measurements, global time-scale

    Input: 
        filtered_df: dataframe contaning data from all valves
        power: int chosen power for the time-weighted average, 2 is typically used. Higer power-values ensures closer points are given higher weigths

    output: 
        datframe with a new collum FC for all actual treatments - background data removed 
    '''
    # extract background data from filtered df - remove background data from 
    df_copy = filtered_df.copy()

    # isolate treatment and background data
    background_df = df_copy[df_copy['TREATMENT'] == 'BACKGROUND'].copy()
    treatment_df = df_copy[df_copy['TREATMENT'] != 'BACKGROUND'].copy()

    background_df = background_df.sort_values(by='TIME_NORM_GLOBAL[h]') # Ensure background data is sorted by time (safety-line, this should already be the case)
    background_df = background_df.dropna(subset=['F[mg/h m2]']) # remove empty rows from background df (avoding spill-over of nan on actual data)

    F_BC = [] # prepare object to store corrected flux-values within

    for idx, row in treatment_df.iterrows(): # looping over the dataframe-rows (vertically)
        current_time = row['TIME_NORM_GLOBAL[h]'] # extracting time-values of the current row

        # find the 3 closest backgrounds
        background_df['time_diff'] = np.abs(background_df['TIME_NORM_GLOBAL[h]'] - current_time) # determine background data time-distance for current row
        closest_background = background_df.nsmallest(3, 'time_diff') #nsmallest returns a df with the 3 closest background-times

        # determine weights (inverse distance weigting)
        distances = closest_background['time_diff'].to_numpy(dtype=float)
        weights = 1 / (distances ** power) 
        weights = weights / np.sum(weights)  # Normalize weights

        # Calculate the weighted average
        flux_values = closest_background['F[mg/h m2]'].to_numpy(dtype=float)
        weighted_avg = np.sum(weights * flux_values)

        # correct the treatment flux and add it to the results-list
        corrected_flux_value = row['F[mg/h m2]'] - weighted_avg
        F_BC.append(corrected_flux_value)


    # add the result-list as a new row
    treatment_df['F_BC'] = F_BC

    return treatment_df


def add_collum(input_df: pd.DataFrame, mapping_dict: dict, present_col: str, new_col: str) -> pd.DataFrame:
    '''
     Adds new collum using .map().

    Input:
        df - dataframe with VALVE_ID collum present
        method: dict with ints (valve ids) as keys, and str as values (methods).
    
    Returns: 
        df with additional collum with presure drop
    '''
    if "VALVE_ID" not in input_df.columns:
        raise ValueError("VALVE_ID column not present")
    
    else:
        df_copy = input_df.copy()
        df_copy[new_col] = df_copy[present_col].astype('Int64').map(mapping_dict) # using .map() to add a new collum with method ID, using the valve id
       
    return df_copy

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
input_path_flux = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\2-flux-conversion\2026-03-12-field-pig-flux-v32.csv")

##### Output folders and files ######
output_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\ALFAM2")

### Constants ###
Proj_tag = 'N-Grass'
expt_tag = 'PigAcid' 
K = 3 # emperical constant used to correlate presure drop in DFC to flow 

triplicate_dict = {
1:1, 2:2, 3:3,
4:1, 6:2, 7:3,
11:1, 12:2, 17:3,
8:1, 13:2, 18:3,
10:1, 14:2, 15:3} # vavles are keys, triplicate number are values

##### Script Excecution #####

# Load and preprocess
df_picarro = load_csv_file_as_df(input_path_flux)
df_weather = load_csv_file_as_df(input_path_weather)
#print('raw weather df: \n', df_weather)
#print('untreated df: \n', df_picarro.head(50))
df_picarro = df_picarro.drop(columns=['C[PPB]', 'C_STDEV[PPB]', 'F_STDEV[mg/h m2]']) # drop unneded collums
#print("After dropping columns: \n", df.head(10))

### Background correction of flux ###
df_picarro = background_correction(df_picarro)
#print("After background correction: \n", df.head(50))

### Convert flux-unit ###
df_picarro = df_picarro.drop(columns=['F[mg/h m2]'])  # Step 3
df_picarro['F_BC'] = df_picarro['F_BC'] * 10**(-6) * 10**(4)
#print('flux conversion \n', df.head(10))

### DFC-flow ###
dP = df_picarro['P_DROP[pa]']
Q =  K * (dP**0.5) # Q [L/s]
Q = Q / 1000 # [m3 / s]
df_picarro['Q[m3/s]'] = Q
df_picarro = df_picarro.drop(columns=['P_DROP[pa]']) 
#print('flow check: \n', df_picarro.head(10))

### add an interval counter ###
df_picarro['INTERVAL'] = 0 # initalizie the collum
for valve_id in df_picarro['VALVE_ID'].unique():
    valve_data = df_picarro[df_picarro['VALVE_ID'] == valve_id]
    valve_data = valve_data.sort_values(by='DATE_TIME')
    df_picarro['INTERVAL'] = df_picarro.groupby('VALVE_ID').cumcount() + 1
#print('check of interval counter \n' , df.head(30))

### Add weather data ###
df_weather = make_datetime_weather(df_weather)
#print('DATE_TIME collum created? : \n', df_weather)
df_picarro = add_weather_conditions(df_picarro, df_weather)
#print('weather conditions added: \n', df_picarro)

### add tags ###
df_picarro['Project'] = Proj_tag
df_picarro['Experiment'] = expt_tag
df_picarro = add_collum(df_picarro, triplicate_dict, 'VALVE_ID', 'REPLICATE')
# combine valve id and treatment
df_picarro['Plot'] = df_picarro['VALVE_ID'].astype(int).astype(str) + '' + df_picarro['TREATMENT']
#print("Final DataFrame: \n", df_picarro.head())

### Determine Shift-length ###
df_picarro = df_picarro.sort_values(by=['VALVE_ID', 'DATE_TIME'])
df_picarro['DATE_TIME'] = pd.to_datetime(df_picarro['DATE_TIME'])

# Define START as the current timestamp
df_picarro['START_TIME'] = df_picarro['DATE_TIME']

# Define END as the next timestamp within each VALVE_ID
df_picarro['END_TIME'] = df_picarro.groupby('VALVE_ID')['DATE_TIME'].shift(-1)

# Remove rows where END_TIME is NaT (last row per group)
df_picarro = df_picarro.dropna(subset=['END_TIME'])

# Calculate shift length
df_picarro['SHIFT_LENGTH_HOURS'] = ((df_picarro['END_TIME'] - df_picarro['START_TIME']).dt.total_seconds() / 3600) # [h]

print('Final df \n', df_picarro)

### Save the data ###
#save_df_as_csv(df_picarro, output_path, Path('2026-03-26-ALFAM2-Cattle-v1'))
df_picarro.to_excel(Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\ALFAM2\2026-03-27-ALFAM2-Pigv1.xlsx"), index=False)

##### Code References #####
 