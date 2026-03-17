### Script Description ###

### Packages ###
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

### Functions ###
def load_picarro_file_as_df(file_path: Path)-> pd.DataFrame:
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    returns: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path, sep=r'\s+', engine='python')
    # Collums in the file are seperated with several empty spaces

def time_normalization_global(df: pd.DataFrame, global_start: None | str = None) -> pd.DataFrame:
    '''
    Creates a collum with time normalized [h] from the experimental start

    Input:
        df with DATE and TIME collums (found in the raw picarro files), or DATE_TIME.
        global_start (str) ex 2025-11-11 11:02.22, if global_start is not provided first measurement will be used.

    output: 
        the df the collums DATE_TIME and TIME_NORM_GLOBAL[h] collums
    '''
    
    if 'DATE_TIME' not in df.columns: # check wheter the collum already exists
        df['DATE_TIME'] = df['DATE'] + ' ' + df['TIME'] # combines the time and date id's in a single new collum
        df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'], format="%Y-%m-%d %H:%M:%S.%f") # convert into a pd.datetime object
        df = df.drop(columns=['DATE', 'TIME']) # remmoving individual time and date collums

    df = df.sort_values('DATE_TIME').reset_index(drop=True) # sorting uisng time (earliest first)

    # Defining start-time with either method
    if global_start is None:
        start_time = df['DATE_TIME'].iloc[0] # .iloc takes the first value of the collum

    elif isinstance(global_start, str):
        start_time = pd.to_datetime(global_start)
        
    else:
        raise ValueError('global_start must be NONE or a string')


    # Normalization:
    df['TIME_NORM_GLOBAL[h]'] = (df['DATE_TIME'] - start_time).dt.total_seconds() / 3600 # [h]

    print('global time-normalization performed')
    return df

  
def visualize_raw_data_per_day(file_path: Path):
    
    df = load_picarro_file_as_df(file_path)
    '''
    Helper-function to visualize raw picarro data
    input: file_path, path-object of the specific picarro-file
    '''
    # normalizing the time and extracting concentration-measurements
    time_normalized_df = time_normalization_global(df)
    times = time_normalized_df['TIME_NORM_GLOBAL[h]'] 
    cs = time_normalized_df['NH3']

    # plot the stuff
    plt.plot(times , cs, '.k', markersize = 1)
    
    # x-axis
    plt.xlabel('time [h]', fontsize=12)
    #plt.xlim([0, max(times)*1.1]) # automatic definition of the x-axis
    plt.xlim([0, 24]) # manual definition of the x-axis
    
    # y-axis
    plt.ylabel('concentration [ppb]', fontsize=12)
    plt.ylim([0,max(cs)*1.1])

    # removing non-axis sides
    ax = plt.gca() 
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # axis titles
    plt.xlabel('Time [h]', fontsize=14, fontname='Times New Roman')
    plt.ylabel('concentration (ppb)', fontsize=14, fontname='Times New Roman')

    # show the graph
    plt.show()
    
def extract_data_from_picarro_file(file_path: Path, cycle_min = 7) -> pd.DataFrame:
    df = load_picarro_file_as_df(file_path)
    '''
    extracts data from raw-piccaro file. 

    inputs:
        file_path, path object, file path of the specific picarro file
        cycle_min (int), check to remove short valve cycles (due to manual change)

    Returns:
        df with the following collums
            DATE_TIME [y-m-d h:min:s.ms]
            VALVE_ID [float]
            C[PPB]
            C_STDEV[PPB]
    '''

    # Converting DATE_TIME collum into a panda datetime object, dropping individual collums
    df['DATE_TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format="%Y-%m-%d %H:%M:%S.%f")
    df = df.drop(columns=['DATE', 'TIME'])

    # Initialization of dict to extract data from piccaro-file
    extracted_data = {'C[PPB]': [], 'C_STDEV[PPB]': [], 'VALVE_ID': [], 'DATE_TIME': []}

    # initialzation of extraction-checks
    previous_valve_pos = None
    in_shift = False
    last_valve_shift_index = 0

    def record_cycle_data(df_segment:pd.DataFrame):
        '''
        Helper-function to extract collum from a valve-cycle (avoiding repeated code).
        
        Input: df-segment, last 30 min of a valve-cycle
        '''
        if len(df_segment) == 0:
            return
        middle_row = df_segment.iloc[len(df_segment) // 2]
        time_val = middle_row['DATE_TIME']
        valve_ID = middle_row['MPVPosition']
        NH3_concentration = df_segment['NH3_Raw'].mean()
        NH3_stdev = df_segment['NH3_Raw'].std()

        extracted_data['C[PPB]'].append(NH3_concentration)
        extracted_data['C_STDEV[PPB]'].append(NH3_stdev)
        extracted_data['VALVE_ID'].append(valve_ID)
        extracted_data['DATE_TIME'].append(time_val)

    for index, row in df.iterrows():  # looping over the rows
        valve_pos = row['MPVPosition']  # valve-ID

        if previous_valve_pos is not None:  # check avoids error at initial point
            valve_diff = valve_pos - previous_valve_pos  # checking if shift occurs via difference of previous and current valve ID

            if abs(valve_diff) > 0.5 and not in_shift:  # If a difference occurs a shift is happening
                in_shift = True  # only first row in a shift is gathered

                cycle_df = df.loc[last_valve_shift_index:index - 1]  # creating a smaller DF to determine time

                cycle_time = (cycle_df['DATE_TIME'].iloc[-1] - cycle_df['DATE_TIME'].iloc[0]).total_seconds()
                current_time = df.loc[index, 'DATE_TIME']

                if cycle_time > 60 * cycle_min:  # data is gathered if the cycle time is higher than 7 min
                    start_index = max(0, index - 30)
                    data_window = df.loc[start_index:index - 1]
                    record_cycle_data(data_window)

                # exception to keep stable data around in the range 00:00-00:10
                # Cyckles are stable, but the creation of a new file at midnight makes them too short 
                elif (current_time.time() >= pd.to_datetime("00:00:00").time() 
                      and current_time.time() <= pd.to_datetime("00:30:00").time()
                      and cycle_time >= 10):

                    # data-gathering
                    start_index = max(0, index - 30)
                    data_window = df.loc[start_index:index - 1]
                    record_cycle_data(data_window)
                    print(f"Accepted short cycle near midnight ({cycle_time:.0f}s) at {current_time}, valve position was {valve_pos}")

                # special case ONLY for this experiment - new dat-file was created in the middle of the first valve meassurement
                elif (current_time.time() >= pd.to_datetime('2026-02-19 09:29:0.00').time() 
                      and current_time.time() <= pd.to_datetime('2026-02-19 10:00:0.00').time()
                      and cycle_time >= 100):

                    # data-gathering
                    start_index = max(0, index - 30)
                    data_window = df.loc[start_index:index - 1]
                    record_cycle_data(data_window)
                    print(f"Accepted short cycle at start of the experiment ({cycle_time:.0f}s) at {current_time}, valve position was {valve_pos}")


                else:  # skipping over other short cycles
                    print(f"Skipped short valve cycle ({cycle_time / 60:.1f} min) at {current_time}, valve postion was {valve_pos}.")

                last_valve_shift_index = index

            elif valve_diff < 0.0001:
                in_shift = False

        previous_valve_pos = valve_pos

    # Convert to DataFrame
    result_df = pd.DataFrame(extracted_data)

    # Safety, remove duplicates based on both time and valve
    result_df = result_df.drop_duplicates(subset=["VALVE_ID", "DATE_TIME"], keep="first").reset_index(drop=True)

    return result_df


def combine_folder_txts_into_single_df(input_folder: Path, cycle_min = 7, visualization = False):
    '''
    Function handles overall logic of loading multiple data from a folder.
 
    input:
        input_folder, path object. A folder containing multiple raw picarro .dat-files
        cycle_min (int) [min], argumment to be passed to the imbeded extract_data_from_picarro_file() function
        visulazation (True/False), wheter to visualize the raw data during extraction, using the visualize_raw_data_per_day() function

    returns:
        sorted_df, a df sorted by valve_IDs and then time containing the following collums:
            DATE_TIME [y-m-d h:min:s.ms]
            VALVE_ID [float]
            C[PPB]
            C_STDEV[PPB]

    '''

    input_folder = Path(input_folder) # defining the folder as a path object, as an extra check
    data_files = list(input_folder.glob("*.dat")) # grapping dat-files in the folder

    # print if no files where found
    if len(data_files) == 0:
        print(f"No .txt files found in {input_folder}")
        return
    
    # initiazation of list used to combine the data
    all_data = []
    
    for file_path in data_files:
        print(f'Processing {file_path.name}') # .name provides the filename instead of the entire path
        extracted_df = extract_data_from_picarro_file(file_path, cycle_min)

        if not extracted_df.empty: # if not checks if the object is empty, extra precuation
            all_data.append(extracted_df)

        if visualization == True:
            visualize_raw_data_per_day(file_path)

    if not all_data:
        print(f'No data was extracted from {file_path.name}, something is wrong')
        return None
    
    print('all files have been processed')
    merged_df = pd.concat(all_data, ignore_index=True)# creating a single df from all_data 
    sorted_df = merged_df.sort_values(by=['VALVE_ID', 'DATE_TIME']).reset_index(drop=True) # and sorting it

    return sorted_df

def remove_data(df: pd.DataFrame, removal_dict: dict[tuple[str, str], list[int]], drop_rows = False) -> pd.DataFrame:
    '''
    Removes or replaces PPB-measurments and the related std-deviation with nan for unreliable data due to known field-errors.
    
    Input:
        A df with extracted data:
            C[ppb] collum (float)
            C_STDEV [PPB] collum (float)
            VALVE_ID collum (float)
            DATE_TIME collum (str)

        uisng remmoval_dict ((start, end), valve_ids), ex {("2023-04-12 12:12:57.520", "2023-04-12 18:12:46.058"): [1, 3]}
        If no valves are provided (the list is empty) all data in the respective time-interval is removed.

        drop_rows (True/False), if true the rows wil be removed from the df
        if False concentrations and stdev for the respective rows will be replaced by np.nan

    Returns: reduced df if some rows where remove, or otherwise having some rows containing nan
    '''
    cleaned_df = df.copy() # creating a copy of the df for added safety

    if not np.issubdtype(cleaned_df['DATE_TIME'].dtype, np.datetime64): # check and potentially converts of DATE_TIME collum
        cleaned_df['DATE_TIME'] = pd.to_datetime(cleaned_df['DATE_TIME'])

    for (start_str, end_str), valve_ids in removal_dict.items():  # extracting time-values from the remmoval dict
        start = pd.to_datetime(start_str) # converting string into pd.datetime object
        end = pd.to_datetime(end_str)

        if len(valve_ids) > 0: # creating sub-df with only the specified valves within the time-range
            removal_range = (cleaned_df['DATE_TIME'].between(start, end) & cleaned_df['VALVE_ID'].isin(valve_ids))

        else: # removes all date within the timerange
            removal_range = cleaned_df['DATE_TIME'].between(start, end)

        if drop_rows == False: # sets PPB data to nan, if the rows should not be dropped (still part of experiment, data simply missing)
            cleaned_df.loc[removal_range, ['C[PPB]', 'C_STDEV[PPB]']] = np.nan # replacing concentration and stdev using the sub.df 
            # print-confimation
            print(f"Set {removal_range.sum()} rows to NaN between {start}-{end} "
              f"{'for valves ' + str(valve_ids) if valve_ids else '(all valves)'}.")

        elif drop_rows == True: # dropping the rows if so specified
            cleaned_df = cleaned_df.loc[~removal_range].reset_index(drop=True)

            print(f"Dropped {removal_range.sum()} rows between {start}-{end} "
                  f"{'for valves ' + str(valve_ids) if valve_ids else '(all valves)'}.") # print-confimations

    return cleaned_df

def add_method(df: pd.DataFrame, method_dict: dict[int, str]):
    '''
    Add and addtional collum with slurry treatment id using .map().

    Input:
        df - dataframe with VALVE_ID collum present
        method: dict with ints (valve ids) as keys, and str as values (methods).
    
    Returns: 
        df with additional collum with treatment ids
    '''    
    if "VALVE_ID" not in df.columns:
        raise ValueError("VALVE_ID column not present")
    
    else:
        df = df.copy()
        df["TREATMENT"] = df["VALVE_ID"].astype(int).map(method_dict) # using .map() to add a new collum with method ID, using the valve id
        print('mehod collum added')
        return df


def save_df_as_csv(df: pd.DataFrame, output_folder: Path, output_file_name: Path, overwrite = True):
    '''
    saves a dataframe as a csv-file with added saftety around overwritting existing files

    Input
        df: the dataframe to be saved
        output_folder: the folder to save the file withing
        output_file_name: the name of the produced csv-file
        overwrite: whether to overwrite an existing file at the same location with the same name
    '''
    output_file = output_folder / f"{output_file_name}.csv"

    if output_file.exists() and not overwrite:
        print(f"Skipping existing file: {output_file.name}")
        return

    df.to_csv(output_file, index=False)
    print(f" output_file saved as: {output_file}")


    
### Constants ### 
before_exp_dict = {('2026-02-19 00:00:0.00' , '2026-02-19 09:30:0.00' ): []}
# in therms of the end, the DAT-file seems to have been refreshed - no need for added filtration

treatment_method_dict = {1: 'PH2SO4', 2: 'FH2SO4', 3: 'FU', 4: 'PU', 5: 'PAA', 11: 'BACKGROUND',
6: 'STD', 7: 'FAA', 8: 'FH2SO4', 9: 'FAA', 10: 'PU', 12: 'BACKGROUND',
17: 'FU', 18: 'PAA', 19: 'PH2SO4', 20: 'STD', 21: 'FAA', 27: 'BACKGROUND',
22: 'PH2SO4', 23: 'PU', 24: 'FH2SO4', 25: 'FU', 26: 'PAA', 28: 'BACKGROUND'} 
# F = Field
# P = packced
# U = untreated  
# AA = Acetic acid
# H2SO4 = sulphuric acid

exp_start = '2026-02-19 09:30:0.00'

### Folders and files ###
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\lab-trails\2026-02-19-lab-pig-slurry-raw-picarro-files")
output_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\1-inital-extraction")
output_file_name = Path('2026-03-17-pig-lab-extracted-v3')

##### Script excecution #####
combined_df = combine_folder_txts_into_single_df(input_folder, cycle_min=14, visualization = False)
print(combined_df)

combined_df_normtime = time_normalization_global(combined_df, exp_start)
print(combined_df_normtime)

combined_df_filtered = remove_data(combined_df_normtime, before_exp_dict, drop_rows= True) 
print(combined_df_filtered)

combined_df_method_added = add_method(combined_df_filtered, treatment_method_dict)
print(combined_df_method_added)

save_df_as_csv(combined_df_method_added, output_folder, output_file_name, overwrite = True)

###### Checks #####
### quick analysis of PPB values for each treatment ###
treatments = combined_df_method_added['TREATMENT'].unique()

for treatment in treatments:
    treatment_data = combined_df_method_added[combined_df_method_added['TREATMENT'] == treatment]
    PPB = treatment_data['C[PPB]']
    PPB_mean = round(PPB.mean(), 2)
    PPB_median = round(PPB.median(), 2)
    PPB_spread = round(PPB.std(), 2)
    PPB_min = round(PPB.min(), 2)
    PPB_max = round(PPB.max(), 2)
    PPB_CV = round(((PPB.std() / PPB.mean()) * 100), 2)  # coeficient of variation, as a percentage

    print(f'{treatment} PPB median is {PPB_median}, PPB mean is {PPB_mean}, coeficient of variation is {PPB_CV} %, (min, max) is ({PPB_min}, {PPB_max}) PPB')


### Coding references ###
# https://www.geeksforgeeks.org/python/python-os-mkdir-method/ 
# https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
# https://docs.python.org/3/library/glob.html
# https://www.geeksforgeeks.org/python/python-check-if-list-empty-not/ 