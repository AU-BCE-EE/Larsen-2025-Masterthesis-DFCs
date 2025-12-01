### Script Description ###

### Packages ###
from math import pi
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


### Functions ###
def date_time_object_conversion(df):
    '''
    combines data and time collums found in weather_data, and convert these into a time object
    
    input: df containing 'date' and 'time' collums

    Returns: df contaning 'DATE_TIME' collum as a time object
    '''

    df['DATE_TIME'] = df['date'].astype(str) + ' ' + df['time'].astype(str) # combines the time and date id's in a single new collum
    #df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'], format="%Y-%m-%d %H:%M:%S.%f")
    df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'], format="%d/%m/%Y %H")
    df = df.drop(columns=['date', 'time']) # remmoving individual time and date collums

    return df


def add_weather_conditions(picarro_df, weather_df):
    '''
    adds additional collums with weather-data to a dataframe with measurements extraced from the picarro-file, 
    matching via the DATA_TIME collums present in both dataframes

    input: data_df dataframe with picarro_data. weather_df dataframe with weather data

    Returns: df with picarro data and collums with weather-paramers for further calculations 
    '''
      # Ensure datetime columns are proper datetime objects
    picarro_df['DATE_TIME'] = pd.to_datetime(picarro_df['DATE_TIME'])
    weather_df['DATE_TIME'] = pd.to_datetime(weather_df['DATE_TIME'])

    # Sort both dataframes by DATE_TIME (required for merge_asof)
    picarro_df = picarro_df.sort_values('DATE_TIME')
    weather_df = weather_df.sort_values('DATE_TIME')

    # Select relevant weather columns
    weather_selected = weather_df[['DATE_TIME', 'mesotp10', 'pres']]

    # merging the weather_data into the data_df
    merged_df = pd.merge_asof(picarro_df, weather_selected, on='DATE_TIME', direction='nearest')  # use last known weather before measurement
    merged_df = merged_df.rename(columns={"mesotp10": "T_GROUND_10cm[DEGC]","pres": "P_ATMOSPHERE[hpa]"})
    return merged_df

def load_csv_file_as_df(file_path):
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    returns: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces

def add_presure_drop(df, preasure_drop_dict):
    '''
     Add and addtional collum with slurry preasure drop for each dfc using .map().

    Input:
        df - dataframe with VALVE_ID collum present
        method: dict with ints (valve ids) as keys, and str as values (methods).
    
    Returns: 
        df with additional collum with presure drop
    '''
    if "VALVE_ID" not in df.columns:
        raise ValueError("VALVE_ID column not present")
    
    else:
        df = df.copy()
        df['P_DROP[pa]'] = df[f"VALVE_ID"].astype(int).map(preasure_drop_dict) # using .map() to add a new collum with method ID, using the valve id
       
    return df


def flux_conversion_nonconst_weather(df):
    '''
    Converting concentration-measurements [PPB] and related std-deviation into fluxes [mg/m2 h], adding them as new collums in the df assuming constant weather conditons
    
    input:
        DF with C[PPB] and C_STDEV[PPB] collum P[hpa] and T_GROUND_10cm[DEGC] as collum

    returns:
        DF previusly mentioned, with flux-collums added
    '''
    # Initalization of constants
    R = 8.205736 * 10**(-5) # Ideal gas constant [m3 atm / K mol]
    MW_N = 14 * 10**3 # molecular weight of elementary nitrogen [mg/mol]
    D = 0.7 # chamber diameter [m]
    A = (D/2)**2 * pi # area enclosed by single chamber
    K = 3 # emperical constant, dp and q relation at physical restriction 
    
    # Gathering needed collums from df:
    C_PPB = df['C[PPB]']
    C_PPB_stdev = df['C_STDEV[PPB]']
    T = df['T_GROUND_10cm[DEGC]'] + 273.15 # degrees celsius to kelvin
    P = df['P_ATMOSPHERE[hpa]'] * 0.000987 # hpa to atm
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


def preliminary_visualization(df, valve_lvl = False):
    '''
    combines fluxes and related std-deviation from treatment-triplicates
    and plots these as a function of TIME_NORMALIZED GLOBAL

    input:
        df with the following collums:
            TIME_NORM_GLOBAL[h]
            TREATMENT
            F[mg/h m2]
            F_STDEV[mg/h m2]

    '''
    for treatment, treatment_data in df.groupby('TREATMENT'):
        if valve_lvl == False:
            treatment_data = treatment_data.sort_values('TIME_NORM_GLOBAL[h]')
            times = treatment_data['TIME_NORM_GLOBAL[h]']
            f = treatment_data['F[mg/h m2]']
            f_stdev = treatment_data['F_STDEV[mg/h m2]']

            plt.errorbar(times, f, yerr = f_stdev, fmt = '.', label=f'{treatment}', capsize=1)

             # axis titles
            plt.xlabel('Global time [h]', fontsize=14, fontname='Times New Roman')
            plt.ylabel('flux [mg / m2 h]', fontsize=14, fontname='Times New Roman')
    
            # legend
            plt.legend(fontsize=12, prop={'family': 'Times New Roman'},frameon=False) # legend font

            # removing non-axis sides
            ax = plt.gca() 
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
    
            # show the graph
            plt.show()
            return

        elif valve_lvl == True:
            treatments = df['TREATMENT'].unique()
            fig, axes = plt.subplots(len(treatments), 1, sharex=True, figsize=(10, 3 * len(treatments)))

            # if only one treatment, axes won't be a list
            if len(treatments) == 1:
                axes = [axes]

            # 2) loop through your normal groupby
            for ax, (treatment, t_data) in zip(axes, df.groupby('TREATMENT')):

            # valve level inside each subplot
                for valve, v_data in t_data.groupby('VALVE_ID'):
                    v_data = v_data.sort_values('TIME_NORM_GLOBAL[h]')
                    x = v_data['TIME_NORM_GLOBAL[h]']
                    y = v_data['F[mg/h m2]']
                    s = v_data['F_STDEV[mg/h m2]']

                    ax.errorbar(x, y, yerr=s, fmt='.', label=str(valve), capsize=1)

                    ax.set_title(str(treatment))
                    ax.legend(frameon=False)
                    ax.legend(frameon=False, loc="center left", bbox_to_anchor=(1.0, 0.5))

            plt.xlabel('Global time [h]')
            fig.supylabel("flux [mg / m2 h]")
            plt.show()
            return
   

def add_mapped_column(df, mapping_dict, from_col, new_col):
    """
    Adding a new collum to a df using a dictionary and .map
    
    Input:
        df contaning from_col(str) (the collum header)
        mapping dict, keys are already present a df-collum, values will be inserted
        new_col(str), header for the collum added

    Return:
        df with new_col added
    """
    if from_col not in df.columns:
        raise ValueError(f"Column '{from_col}' not present in DataFrame")
    
    df = df.copy()
    df[new_col] = df[from_col].map(mapping_dict)
    
    return df


def TAN_normalization(df, TAN_M2_dict,Tan_M2_stdev_dict):
    '''
    normalizing fluxes and related std_dev (plus error propagation) agianst slurry TAN-values
    
    input:
        df with the following collums included
            F[mg/h m2]
            F_STDEV[mg/h m2]

        TAN_M2_dict{'treatment': TAN[mg/m2]}
        TAN_M2_stdev_dict {'treatment' : TAN_stdev [mg/m2]}

    output:
        df with the folloing collums added
            TAN_RATE[h-1]
            TAN_RATE_STDEV
    '''
    # adding new collums from dictionary
    df['TAN[mg/m2]'] = df['TREATMENT'].map(TAN_M2_dict)
    df['TAN_STDEV[mg/m2]'] = df['TREATMENT'].map(Tan_M2_stdev_dict)

    # as background is not present .map() insterts nan - replace those with 0's
    df['TAN[mg/m2]'] =  df['TAN[mg/m2]'].fillna(0.0)
    df['TAN_STDEV[mg/m2]'] =  df['TAN_STDEV[mg/m2]'].fillna(0.0)
    
    # TAN normalization
    mask = df['TAN[mg/m2]'] > 0

    df['TAN_RATE[1/h]'] = 0.0
    df.loc[mask, 'TAN_RATE[1/h]'] = df.loc[mask, 'F[mg/h m2]'] / df.loc[mask, 'TAN[mg/m2]']
    
    # Error propagation
    df['TAN_RATE_STDEV[1/h]'] = 0.0

    rel_f = df['F_STDEV[mg/h m2]'] / df['F[mg/h m2]']
    rel_tan = df['TAN_STDEV[mg/m2]'] / df['TAN[mg/m2]']

    df.loc[mask, 'TAN_RATE_STDEV'] = (df.loc[mask, 'TAN_RATE[1/h]'] *((rel_f[mask]**2 + rel_tan[mask]**2)**0.5))
    return df


def preliminary_visualization2(df, y_col, yerr_col, valve_lvl=False):
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


### Input folders and files ###
# Weather data:
input_path_weather = Path(r"C:\Users\mikae\Desktop\Github - speciale\AgrosceNa-NEXT\data\weather\FoulumVejr_0110_1711.csv")
weather_df = load_csv_file_as_df(input_path_weather)
weather_df = date_time_object_conversion(weather_df)

# picarro data:
input_path_picarro = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Field-trails\Cattle-Slurry 2025-10-28\Piccaro-data\1-extracted-data\cattle-field-extracted-valve18.csv")

### Constants ###
preasure_drop_dict = {4: 131.2 , 5: 131.2, 8: 131.2, 9: 131.2, 11: 127.3, 12: 129.5, 13: 127.3, 14: 131.6, 15: 131.3, 16: 131.3, 17: 129.5, 18: 125.6} # pa
TAN_M2_dict = {'AA' : 5371.0, 'RAW': 5218.4, 'H2SO4': 5466.2} # [mg/m2]
TaN_M2_stdev_dict = {'AA' : 143.2, 'RAW': 165.7, 'H2SO4': 95.3} # [mg/m2]

### Script Excecution ###

picarro_df = load_csv_file_as_df(input_path_picarro)

combined_df = add_weather_conditions(picarro_df, weather_df)

combined_df = add_presure_drop(combined_df, preasure_drop_dict)

flux_conversion_nonconst_weather(combined_df)

combined_df = TAN_normalization(combined_df, TAN_M2_dict, TaN_M2_stdev_dict)

#preliminary_visualization(combined_df, valve_lvl = True)
#preliminary_visualization2(combined_df,'F[mg/h m2]','F_STDEV[mg/h m2]', valve_lvl = True)
preliminary_visualization2(combined_df,'TAN_RATE[1/h]','TAN_RATE_STDEV[1/h]', valve_lvl = False )

### Print-tests ###
#print(weather_df)
#print(combined_df)
### Code references ###
