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
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Fall Experiments\slurry acidification - initial lab scale\2nd trial") # copy the filepath
input_file_name = 'Titrations - 2nd trail.csv' # copy the name as a string, don't forget .csv

### function-calls ###
df = load_data(input_folder,input_file_name)

# Extracting data from DF
x_data1 = df['V (acid) [mL]'] 
x_data2 = df['m(H2SO4) / m(slurry) [kg/ton]']
x_data3 = df['V(acid) / m(slurry) [L/ton]']

y_data1 = df['pH Cattle H2SO4 (mean)']
y_data2 = df['pH cattle AA (mean)']
y_data3 = df['pH pig H2SO4 (mean)']
y_data4 = df['pH pig AA (mean)']

y_stdev1 = df['stdev pH H2SO4 cattle']
y_stdev2 = df['pH stdev Cattle AA']
y_stdev3 = df['pH stdev pig H2SO4']
y_stdev4 = df['pH stdev pig AA']

### Plot the stuff ###
# measured current and voltage
plt.errorbar(x_data2, y_data1, yerr=y_stdev1, fmt='o',
             color='#2b8cbe', label='Cattle H2SO4', capsize=2)
#plt.errorbar(x_data2, y_data2, yerr=y_stdev2, fmt='o',
 #            color='#a6bddb', label='Cattle AA', capsize=2)

# Pig
plt.errorbar(x_data2, y_data3, yerr=y_stdev3, fmt='o',
             color="#8e5107", label='Pig H2SO4', capsize=2)
#plt.errorbar(x_data1, y_data4, yerr=y_stdev4, fmt='o',
#             color='#d8b365', label='Pig AA', capsize=2)


# legend
plt.legend(fontsize=12, prop={'family': 'Times New Roman'},frameon=False) # legend font

# removing non-axis sides
ax = plt.gca() 
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# axis limits
#plt.xlim(0, 4500)

# axis titles
plt.xlabel('m(H2SO4) / m(slurry) [kg / ton]', fontsize=14, fontname='Times New Roman')
plt.ylabel('pH', fontsize=14, fontname='Times New Roman')

# axis ticks
#plt.tick_params(axis='both', labelsize=12)
#plt.xticks(range(0, 4400, 400), fontname='Times New Roman')
#plt.yticks(range(1500, 3500, 200), fontname='Times New Roman')

# show the graph
plt.show()

### print-test ###
#print(df)
#print(data)
#print(x_data)
#print(type(x_data))
#print(x_linear)

### code-references ###
# https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.scatter.html
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html 