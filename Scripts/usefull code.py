### Script description ###
# Usefull codes/functions with explantion - potentially not used in final version of actual scrits, therefore saved here

### Packages ###
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline

### Actual code-section ###
# table["COLLUMNAME"].iloc[0])) # graps a single value from a specified collum in a pandas dataframe

# print(table['COLLUMNAME'].head(10)) # prints the first 10 datapoints of a table or a specified collum

a= [3,2,1]
print(np.empty_like(a))

def interpolate_valve(valve_data, interp_method = 'linear'):
    '''
    Performs interpolations(linear & cubic spline), within the range which data is present for each valve.
    Using x-values (global normalized time) and y-values (flux) on data coresponding to each valve id stored in a dict to perform the interpolation.
    Also extracs additional data used as argumments in later for later functions such as method_id.
    
    Returns a dict with valve_id as key and interpolated data (x_expanded, y_interpolated, method_id) as values.
    
    Notice this function is simplified compared to v2 script, as this function should be able to handle all valves within reasonable time-frames.
    Therefore, ability to interpolate using either method at the same time was removed. 
    Also make the data-structures later functions needs to handle simpler.
    '''
    interp_results = {} # initalizing the return-dict

    for id,data in valve_data.items(): # looping over the valve data dict
        x = data['x'] # normalized time
        y = data['y'] # flux
        method_id = data['metod_id']

        x_expanded = np.linspace(x[0], x[-1], num=int((x[-1] - x[0]) * 120) + 1) # creates evenly spaced timestamps (½ min)

        if interp_method == 'linear':
            y_interp = np.interp(x_expanded, x, y)

        elif interp_method == 'cubic':
            y_interp = CubicSpline(x, y)(x_expanded)

        interp_results[id] = {'x_expanded' : x_expanded, 'y_interp': y_interp, 'method_id' : method_id} # adding to the dict
        # id as key, results from interpolation as values 

    return interp_results


def process_input_folder(input_folder , output_folder, overwrite = False):
    '''
    Function handles overall logic of loading and saving multiple data from a folder.
    extract_data_from_piccarro_file is used for each file in the folder    
    '''

    output_folder.mkdir(parents=True, exist_ok=True) 
    # creates the outputfolder if it doesnt already exist
    # exist_ok = True ensures script simply moves on if output_folder exist instead of raising a value_error

    txt_files = list(input_folder.glob("*.txt"))
    if len(txt_files) == 0:
        print(f"No .txt files found in {input_folder}")
        return
    
    for txt_file in txt_files:
        print(f'Processing {txt_file.name}') # .name provides simply the filename not the entire path
        extracted_df = extract_data_from_piccaro_file(txt_file)

        output_file = output_folder / f"{txt_file.stem}_extracted.csv"
    
        if output_file.exists() and not overwrite:
            print(f"Skipping existing file: {output_file.name}")
            continue

        extracted_df.to_csv(output_file, index=False)
        print(f"Saved: {output_file.name}")

### Changing another script, saving this here for now ### 

def extract_data_from_picarro_file(file_path, cycle_min = 7):
    '''
    Extracts needed data from the raw Picarro files and returns them as a dataframe.
   
    Input: a DAT_file with several empty spaces as column dividers (as in raw Picarro files).

    Gathers data from the last 30 s before a valve-shift (when the measurement is stable).
    As an additional check, only extracts from valve-cycles with >7 min of data(avoiding quick manual shifts to test the equipment).
    Short cycles if they are within the range 00:00-00:10 are however kept (the picarro creates a new file around midnight "cutting"
    stable valve-cycle) 

    Returns a df with the following columns:
    - C[PPB]
    - C_STDEV[PPB]
    - VALVE_ID
    - DATE_TIME [y-m-d-h-min-s.ms]
    '''
    df = load_picarro_file_as_df(file_path)

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

                if cycle_time > 60 * cycle_min:
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
                    if:
                        ...
                    
                    else:
                        print(f"Skipped short valve cycle ({cycle_time/60:.1f} min) at {current_time}.")

                # Update cycle start index *after* processing
                last_valve_shift_index = index

            elif valve_diff < 0.0001:
                in_shift = False 
        
        previous_valve_pos = valve_pos

    extracted_df = pd.DataFrame(extracted_data)
    return extracted_df



def combine_csw_files_into_single_df(input_folder):
    '''
    Function handles overall logic of loading multiple data from a folder
    
    input: input_folder (path-object)

    Return: a single df from multiple csv-files sorted with respect a created DATE_TIME collum
    '''

    input_folder = Path(input_folder) # defining the folder as a path object, as an extra check
    data_files = list(input_folder.glob("*.csv")) # grapping dat-files in the folder

    all_data = []

    # print if no files where found
    if len(data_files) == 0:
        print(f"No .csv files found in {input_folder}")
        return
   
    for file in data_files:
        df = pd.read_csv(input_folder / file)
        df = date_time_object_conversion(df)
        
        all_data.append(df)
        

    print('all files have been processed')
    merged_df = pd.concat(all_data, ignore_index=True)# creating a single df from all_data 
    sorted_df = merged_df.sort_values(by=['DATE_TIME']).reset_index(drop=True) # and sorting it

    return sorted_df

