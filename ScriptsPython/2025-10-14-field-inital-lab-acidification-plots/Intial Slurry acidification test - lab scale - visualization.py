### Script description ###
# Creates plots of inital triplicate test on slurry (2nd trial)
### Packages ###
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from pathlib import Path

### Functions ###
def load_data(input_folder,input_file_name):
    '''
    Load a csv-file as a df using it's folderpath and filename
    Requires the path and pandas package
    '''
    df = pd.read_csv(input_folder / input_file_name, comment='#', sep=';')
    df.columns = df.columns.str.strip() # remove empty spaces 
    # notice the / to attach the strings, non-std Python formatting
    # defining which signs are comments and therefore ignored
    # defining the seperator-symbol used in the csv
    return df  

##### defining constants #####
# folder and filename
input_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Field-trails\2025-10-14-inital-lab-acidification") # copy the filepath
input_file_name_pig = '2025-10-14-titration-pig-2nd.csv' # copy the name as a string, don't forget .csv
input_file_name_cattle = '2025-11-11-Titration-cattle-3rd.csv'

##### function-calls #####
df_pig = load_data(input_folder,input_file_name_pig)
print(df_pig)
df_cattle = load_data(input_folder, input_file_name_cattle)
print(df_cattle)

##### Extracting data from DF #####
# x-axis arrays
xs1_pig = df_pig['V(acid) / m(slurry) [L/ton]']
xs2_pig = df_pig['m(H2SO4) / m(slurry) [kg/ton]']
xs3_pig = (xs1_pig / 1.05) # volume to mass of acetic acid [L] / [kg/L]= kg

xs1_cattle = df_cattle['V(acid) / m(slurry) [L/Ton]']
xs2_cattle = df_cattle['V(H2SO4) / m(slurry) [kg/Ton]'] # error in the table header - mass and NOT volume of H2SO4
xs3_catte = (xs1_cattle / 1.05)  # volume to mass of acetic acid [L] / [kg/L] = kg

# y-axis arrays
pH_pig_AA = df_pig['pH pig AA (mean)']
pH_pig_H2SO4 = df_pig['pH pig H2SO4 (mean)']

pH_cattle_AA = df_cattle['pH(AA) avg']
pH_cattle_H2SO4 = df_cattle['pH(H2SO4) avg']

# std-deviation
pH_stdev_pig_AA = df_pig['pH stdev pig AA']
pH_stdev_pig_H2SO4 = df_pig['pH stdev pig H2SO4']

pH_stdev_cattle_AA = df_cattle['pH(AA) stdev']
pH_stdev_cattle_H2SO4 = df_cattle['pH(H2SO4) stdev']
print('PH stedev', pH_stdev_cattle_H2SO4)

##### Plot the stuff ######

### catte 
plt.errorbar(xs3_catte, pH_cattle_AA, yerr=pH_stdev_cattle_AA, fmt='o', color='#2b8cbe', label='Cattle AA', capsize=2)
plt.errorbar(xs1_cattle, pH_cattle_H2SO4, yerr=pH_stdev_cattle_H2SO4, fmt='o', color="#6e9fdf", label='Cattle H₂SO₄', capsize=2)
# Pig
plt.errorbar(xs3_pig, pH_pig_AA, yerr = pH_stdev_pig_AA, fmt='o',color="#EB0D0D", label='Pig AA', capsize=2)
plt.errorbar(xs1_pig, pH_pig_H2SO4, yerr = pH_stdev_pig_H2SO4, fmt='o',color="#fa7305", label='Pig H₂SO₄', capsize=2)
plt.xlabel('m(acid) / m(slurry) [kg / ton]', fontsize=14, fontname='Times New Roman')
plt.ylabel('pH', fontsize=14, fontname='Times New Roman')


### Cattle slurry as mass of sulpuric acid ###
#plt.errorbar(xs1_pig, pH_pig_H2SO4, yerr = pH_stdev_pig_H2SO4, fmt='o',color="#fa7305", label='Pig H₂SO₄', capsize=2)
#plt.errorbar(xs2_cattle, pH_cattle_H2SO4, yerr=pH_stdev_cattle_H2SO4, fmt='o',color="#6e9fdf", label='Cattle H₂SO₄', capsize=2)
#plt.legend(fontsize=12, prop={'family': 'Times New Roman'},frameon=False) # legend font
#plt.xlabel('m(H₂SO₄) / m(slurry) [kg / ton]', fontsize=14, fontname='Times New Roman')
#plt.ylabel('pH', fontsize=14, fontname='Times New Roman')

### Show the graphs and general stuff relevant for all axis
plt.legend(fontsize=12, prop={'family': 'Times New Roman'},frameon=False) # legend font
plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(10)) # Increase the number of ticks
plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(10))
plt.gca().tick_params(axis='both', direction='in', which='both') # moved the ticks on the inside of the figure
plt.show()



### print-test ###
#print(df_pig)
#print(df_cattle)
#print(data)
#print(x_data)
#print(type(x_data))
#print(x_linear)

### code-references ###
# https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.scatter.html
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html 