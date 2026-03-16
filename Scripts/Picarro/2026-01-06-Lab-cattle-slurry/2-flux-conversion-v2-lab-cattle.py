### Script Description ###

### Packages ###
from math import pi
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


### Functions ###
def load_csv_file_as_df(file_path: Path):
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    returns: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces


def SL_to_L(SL_value: float, T_act: float, P_act:float) -> float:
    '''
    conversion volume from standard-liters (1 bar, 0 deg c) to actual condions
    
    Input: 
        SL_flow, the flow in standard-liters
        T: Temperature at experimental conditions [deg c]
        P: Temperature at experimental condtions  [bar]

    output:
        volume at actual experimental condtions

    '''
    T_act = T_act + 273.15 # celsius to Kelvin
    L_act = SL_value * (T_act / 273.15) * (1 / P_act) # Vact = V_SL * (P_SL / P_act) * (T_act / P_SL)
    
    return L_act


def add_flow(df: pd.DataFrame, flow_dict: dict[int, float]):
    '''
     Add and addtional collum with experimental flow from each valve

    Input:
        df - dataframe with VALVE_ID collum present
        method: dict with ints (valve ids) as keys, and flow as values.
    
    Returns: 
        df with additional flow collum
    '''
    df = df.copy()
    df['Q[L/min]'] = df[f"VALVE_ID"].astype('Int64').map(flow_dict) # using .map() to add a new collum with method ID, using the valve id
       
    return df


def flux_conversion_const_weather(df: pd.DataFrame, P:float, T: float):
    '''
    Converting concentration-measurements [PPB] and related std-deviation into fluxes [mg/m2 h], adding them as new collums in the df assuming constant weather conditons
    
    input:
        DF with C[PPB] and C_STDEV[PPB] collum P[hpa] and T_GROUND_10cm[DEGC] as collums

    returns:
        DF previusly mentioned, with flux-collums added
    '''
    # conversion of global constants
    T = T + 273.15 # celsius to Kelvin
    P = P / 1.01325 # [bar] to [atm]

    # Local constants
    R = 8.205736 * 10**(-5) # Ideal gas constant [m3 atm / K mol]
    MW_N = 14 * 10**3 # molecular weight of elementary nitrogen [mg/mol]
    A = 28.27 * 10**(-4) # [cm2] to [m2] total soil surface 
    
    # Gathering needed collums from df:
    C_PPB = df['C[PPB]']
    C_PPB_stdev = df['C_STDEV[PPB]']
    Q = df['Q[L/min]']

    # Intermediary mass/volume [mg/m3] calcualtion using ideal gas equaton
    C_mass = C_PPB * (P / (R * T)) * MW_N * 10**(-9) # [mg/m3]
    C_mass_stdev = C_PPB_stdev * (P / (R * T)) * MW_N * 10**(-9) # [mg/m3]

    # flux_calculation
    Q = Q * 60 # [L/ min] to [L/h]
    Q = Q / 1000 # [L/h] to [m3 / h]
    df['F[mg/h m2]'] = (C_mass * Q) / A # ([mg/m3] [m3/h]) / [m2] = [mg / h m2]
    df['F_STDEV[mg/h m2]'] = (C_mass_stdev * Q) / A # ([mg/m3] [m3/h]) / [m2] = [mg / h m2]

    return df


def save_df_as_csv(df, output_folder, output_file_name, overwrite = True):
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

    df.to_csv(output_file, index=False)
    print(f" output_file saved as: {output_file}")


##### Files and folders #####
### Input folders and files ###
# picarro data:
input_path_picarro = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\1-inital-extraction\2026-03-10-cattle-lab-extracted-v3.csv")

### Output folders and files ###
output_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\2-flux-conversion")
output_file_name = Path('2026-03-12-lab-cattle-flux-v32')

##### Constants #####
#treatment_method_dict = {1: 'PU', 2: 'FH2SO4', 3: 'STD', 4: 'PH2SO4', 5: 'PAA', 11: 'BACKGROUND',
#6: 'FAA', 7: 'FU', 8: 'FH2SO4', 9: 'PU', 10: 'FAA', 12: 'BACKGROUND',
#17: 'FH2SO4', 18: 'FU', 19: 'PAA', 20: 'STD', 21: 'PH2SO4', 27: 'BACKGROUND',
#22: 'FAA', 23: 'FU', 24: 'PU', 25: 'PH2SO4', 26: 'PAA', 28: 'BACKGROUND'} not used simply here to provide an overview

flow_dict = {1: 1.179, 2: 1.180, 3: 1.180, 4: 1.182, 5: 1.188, 11: 1.186,
6: 1.180, 7: 1.182, 8: 1.180, 9: 1.181, 10: 1.182, 12: 1.187,
17: 1.177, 18: 1.181, 19: 1.182, 20: 1.181, 21: 1.179, 27: 1.187,
22: 1.181, 23: 1.182, 24: 1.182, 25: 1.182, 26: 1.181, 28: 1.188} # SL/ min

Pres = 1.01325 # [bar]
Temp = 22 # [deg c]

##### Script Excecution #####
# importing file
picarro_df = load_csv_file_as_df(input_path_picarro)
#print(picarro_df)

# conversion from SL to liters at actual conditons
converted_flow_dict = {}
for Valve_id, SL_flow in flow_dict.items():
    L_flow = SL_to_L(SL_flow, Temp, Pres)
    converted_flow_dict[Valve_id] = L_flow
#print(converted_flow_dict)

df_flow_added = add_flow(picarro_df, converted_flow_dict)
#print(df_flow_added)

flux_df = flux_conversion_const_weather(df_flow_added, Pres, Temp)
print(flux_df)

#save_df_as_csv(flux_df, output_folder, output_file_name, overwrite = False)

##### Checks #####
#... 
##### Visuals ##### 
def preliminary_visualization(df, valve_lvl = True):
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

#preliminary_visualization2(flux_df,'F[mg/h m2]','F_STDEV[mg/h m2]', valve_lvl = False)

### Code references ###
