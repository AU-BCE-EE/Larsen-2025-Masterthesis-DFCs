### Script description ###
# Creates plots of inital triplicate test on slurry (2nd trial)
### Packages ###
import matplotlib.pyplot as plt
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

### defining constants ###
# folder and filename
input_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Lab-acidification-test-before-lab-field-trails") # copy the filepath
input_file_name_pig = '2025-10-14-titration-pig-2nd.csv' # copy the name as a string, don't forget .csv
input_file_name_cattle = '2025-11-11-Titration-cattle-3rd.csv'

### function-calls ###
df_pig = load_data(input_folder,input_file_name_pig)
df_cattle = load_data(input_folder, input_file_name_cattle)

# Extracting data from DF
# x-axis arrays
xs1_pig = df_pig['V(acid) / m(slurry) [L/ton]']
xs2_pig = df_pig['m(H2SO4) / m(slurry) [kg/ton]']

xs1_cattle = df_cattle['V(acid) / m(slurry) [L/Ton]']
xs2_cattle = df_cattle['V(H2SO4) / m(slurry) [kg/Ton]'] # actually the mass of H2SO4

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

### Plot the stuff ###
# catte 
plt.errorbar(xs1_cattle, pH_cattle_AA, yerr=pH_stdev_cattle_AA, fmt='o',
             color='#2b8cbe', label='Cattle AA', capsize=2)

plt.errorbar(xs1_cattle, pH_cattle_H2SO4, yerr=pH_stdev_cattle_H2SO4, fmt='o',
             color='#a6bddb', label='Cattle H2SO4', capsize=2)

# Pig
plt.errorbar(xs1_pig, pH_pig_AA, yerr = pH_stdev_pig_AA, fmt='o',
             color="#8e5107", label='Pig H2SO4', capsize=2)
plt.errorbar(xs1_pig, pH_pig_H2SO4, yerr = pH_stdev_pig_H2SO4, fmt='o',
             color='#d8b365', label='Pig AA', capsize=2)


# legend
plt.legend(fontsize=12, prop={'family': 'Times New Roman'},frameon=False) # legend font

# removing non-axis sides
ax = plt.gca() 
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Manual axis limits
#plt.xlim(0, 12)

# axis titles
plt.xlabel('V(acid) / m(slurry) [L / ton]', fontsize=14, fontname='Times New Roman')
plt.ylabel('pH', fontsize=14, fontname='Times New Roman')

# Manual axis ticks
#plt.tick_params(axis='both', labelsize=12)
#plt.xticks(range(0, 4400, 400), fontname='Times New Roman')
#plt.yticks(range(1500, 3500, 200), fontname='Times New Roman')

# show the graph
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