### Script Description ###
# read raw piccarro-files which are txt-files
# for each file load it as a data-frame
# manual remmoval bad of data due to noted equipment errors
# 
# identify each time a "good" valve shift occurs, ie each time and iteration of 8 min has actually occrued, not simply manual shifts to test the apparatus
# when a good shift has occured extract:
# - concentrations as ppb
# - the valve ID
# - date-time
# 
# addtionally plot ppb as a function starting time - either data from all files, a specific file, or a random simply as a test during usual procedure

### Packages ###
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

### Functions ###
def time_normalization_global(df, global_start = None):
    '''
    Takes a df with the DATE and TIME collum (present in the raw piccarro files).
    Creates a new collum DATE_TIME [y-m-d-h-m.ms], by combining these while dropping the individual collums if it hasn't already been created.
    Creates a new collum with time normalized based upon the start of the entire experiment.
    Either using a manually specified startting time as a str.
    Or using the first measurment.
    Returns the df with the prevously described collums.
    '''
    if 'DATE_TIME' not in df.columns:
        # Combining time and date into a single collum
        df['DATE_TIME'] = df['DATE'] + ' ' + df['TIME'] # combines the time and date id's in a single new collum
        df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'], format="%Y-%m-%d %H:%M:%S.%f") 
        # remmoving individual time and date collums
        df = df.drop(columns=['DATE', 'TIME'])


    if global_start is None:
        start_time = df['DATE_TIME'].iloc[0] # .iloc takes the first value of the collum
        df['TIME_NORM_GLOBAL[h]'] = (df['DATE_TIME'] - start_time).dt.total_seconds() / 3600 # [h]

    if isinstance(global_start, str):
        df['TIME_NORM_GLOBAL[h]'] = (df['DATE_TIME'] - start_time).dt.total_seconds() / 3600 # [h]

    return df


def time_normalization_local(df, local_starts=None):
    '''
    Takes a df with the DATE and TIME columns (present in the raw Picarro files).
    Creates a new column DATE_TIME [y-m-d-h-m.ms], by combining these while dropping the individual columns.
    Creates a new column with time normalized based upon individual starts for each valve.
    local_starts is a dict with valves (ints) as keys and the starts (str) as values.
    If local_starts are not provided, the starting measurement of each valve will be used.
    '''
    if 'DATE_TIME' not in df.columns:
        df['DATE_TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format="%Y-%m-%d %H:%M:%S.%f")
        df = df.drop(columns=['DATE', 'TIME'])

    # Normalize MPVPosition rounding and type
    df['MPVPosition'] = df['MPVPosition'].round(5)
    valve_ids = df['MPVPosition'].unique()

    if local_starts is not None:
        # Ensure keys are numeric (handle accidental string keys)
        local_starts = {float(k): v for k, v in local_starts.items()}

    df['TIME_NORMALIZED_LOCAL'] = np.nan

    for valve_id in valve_ids:
        mask = df['MPVPosition'] == valve_id
        valve_times = df.loc[mask, 'DATE_TIME']

        if local_starts is not None and valve_id in local_starts:
            start_time = pd.to_datetime(local_starts[valve_id])
        else:
            start_time = valve_times.min()

        df.loc[mask, 'TIME_NORMALIZED_LOCAL'] = (valve_times - start_time).dt.total_seconds()

    return df
   
def visualize_raw_data(txt_file):
    df = pd.read_csv(txt_file, sep=r'\s+')
    # loads the current file in the loop as a table(pd-dataframe)
    #  indicating that the collum seperator is several empty spaces

    time_normalized_df = time_normalization_global(df)
    times = time_normalized_df['TIME_NORM_GLOBAL[h]'] 
    cs = time_normalized_df['NH3']

    plt.plot(times , cs, '.-k')
    # make the graph pretty
    plt.xlabel('time [min]', fontsize=12)
    #plt.xlim([0, max(times)*1.1]) # automatic definition of the x-axis
    plt.xlim([0, 150]) # manual definition of the x-axis
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
    
def extract_data_from_picarro_file(txt_file):
    '''
    Extracts needed data from the raw Picarro files and returns them as a dataframe.
    Input: a txt_file with several empty spaces as column dividers (as in raw Picarro files).

    Gathers data from the last 30 s before a valve-shift (when the measurement is stable).
    As an additional check, only extracts from valve-cycles with >7 min of data
    (avoiding quick manual shifts to test the equipment).

    Returns a df with the following columns:
    - C[PPB]
    - C_STDEV[PPB]
    - VALVE_ID
    - DATE_TIME [y-m-d-h-min-s.ms]
    '''
    # Load the file as a table (pd.DataFrame)
    df = pd.read_csv(txt_file, sep=r'\s+')
    # \s+ means "split on one or more spaces" (true for raw Picarro files)

    # Combine DATE and TIME into datetime objects
    df['DATE_TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format="%Y-%m-%d %H:%M:%S.%f")
    df = df.drop(columns=['DATE', 'TIME'])
    
    # Initialize storage dictionary
    extracted_data = {'C[PPB]': [], 'C_STDEV[PPB]': [], 'VALVE_ID': [], 'DATE_TIME': []}

    # Initialize loop logic
    previous_valve_pos = None
    in_shift = False
    last_valve_shift_index = 0

    for index, row in df.iterrows():
        valve_pos = row['MPVPosition']

        if previous_valve_pos is not None:  # avoid error at first row
            valve_diff = valve_pos - previous_valve_pos

            # Detect valve-position shift
            if valve_diff > 0.0001 and not in_shift:
                in_shift = True  # avoid picking up additional shift-points

                # Define the current valve cycle
                cycle_df = df.loc[last_valve_shift_index:index - 1]
                cycle_time = (cycle_df['DATE_TIME'].iloc[-1] - cycle_df['DATE_TIME'].iloc[0]).total_seconds()

                if cycle_time > 60 * 7:  # only accept cycles longer than 7 minutes
                    # Gather data 30 s before the shift
                    start_index = max(0, index - 30)
                    data_window = df.loc[start_index:index - 1]

                    if len(data_window) > 0:
                        middle_row = data_window.iloc[len(data_window) // 2]
                        time_val = middle_row['DATE_TIME']
                        valve_ID = middle_row['MPVPosition']

                        NH3_concentration = data_window['NH3'].mean()
                        NH3_stdev = data_window['NH3'].std()

                        # Save extracted values
                        extracted_data['C[PPB]'].append(NH3_concentration)
                        extracted_data['C_STDEV[PPB]'].append(NH3_stdev)
                        extracted_data['VALVE_ID'].append(valve_ID)
                        extracted_data['DATE_TIME'].append(time_val)
                
                else:
                     current_time = df.loc[index, 'DATE_TIME']
                     print(f"Skipped short valve cycle ({cycle_time/60:.1f} min) at {current_time}.")

                # Update cycle start index *after* processing
                last_valve_shift_index = index

            elif valve_diff < 0.0001:
                in_shift = False 
        
        previous_valve_pos = valve_pos

    extracted_df = pd.DataFrame(extracted_data)
    return extracted_df


def combine_folder_txts_into_single_df(input_folder, Visualization = False):
    '''
    Function handles overall logic of loading multiple data from a folder.
    extract_data_from_piccarro_file() function is used for each file in the folder.
    Extracted data from multiple files are merged and saved as a single csv-file. 
    '''

    txt_files = list(input_folder.glob("*.txt"))
    if len(txt_files) == 0:
        print(f"No .txt files found in {input_folder}")
        return
    
    all_data = []
    
    for txt_file in txt_files:
        print(f'Processing {txt_file.name}') # .name provides simply the filename not the entire path
        extracted_df = extract_data_from_picarro_file(txt_file)

        if not extracted_df.empty: # if not checks if the object is empty, extra precuation
            all_data.append(extracted_df)

    if not all_data:
        print('No data was extracted, something is wrong')
        return
    
    # creating a single df from all_data and sorting it
    merged_df = pd.concat(all_data, ignore_index=True)

    sorted_df = extracted_df.sort_values(by=['VALVE_POS[-]', 'DATE_Time']) # sorting the dataframe

    return sorted_df

def remove_data(df, dict):
    '''
    Removes unreliable data due to known field-errors.
    using a df with picarro data.


    uisng tuble (str, [ints]) to determine which data to remove.
    str simillar to the DATE_TIME-collum in the piccaro data, start and end of the remmoval seperated by (something!) 
    ex 2023-04-12 12:12:57.520 --- 2023-04-12 18:12:46.058.
    The ints coresponding to valve id's.
    If no values are provided (the dict is empty) all data in the respective time-interval is removed.

    Returns a df with the specified data removed.
    '''

def save_df_as_csv(df, output_folder, overwrite = True):
    '''
    
    '''
    output_file = output_folder / "test_extracted.csv"

    if output_file.exists() and not overwrite:
        print(f"Skipping existing file: {output_file.name}")
        return

    df.to_csv(output_file, index=False)
    print(f" output_file saved as: {output_file}")

    
### Constants ### 

### Function calls ###
if __name__ == "__main__":
    # copy the folderpath
    input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\Actual data - only 1 file")
    # copy the folderpath, add at least.csw
    output_file = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\1 Dummy_extracted")

    combine_folder_txts_into_single_df(input_folder , output_file, overwrite = False)

### Print tests ### 

### Coding references ###
# https://www.geeksforgeeks.org/python/python-os-mkdir-method/ 
# https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
# https://docs.python.org/3/library/glob.html
# https://www.geeksforgeeks.org/python/python-check-if-list-empty-not/ 