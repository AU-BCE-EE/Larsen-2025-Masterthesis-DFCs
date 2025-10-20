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
    # notice the / to attach the strings, non-std Python formatting
    # defining which signs are comments and therefore ignored
    # defining the seperator-symbol used in the csv
    return df  

### defining constants ###
# folder and filename
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Fall Experiments\Inital Lab slurry acidification") # copy the filepath
input_file_name = 'Titrations - 2nd trail.csv' # copy the name as a string, don't forget .csv

### function-calls ###
df = load_data(input_folder,input_file_name)

# removing nonlinear data (first 3 points) for performing linear regression
x_data = df['V (acid) [mL]'] 
y_data1 = df['pH Cattle H2SO4 (mean)']

y_data2 = df['pH cattle AA (mean)']

y_data3

### Plot the stuff ###
# measured current and voltage
plt.scatter(data['Current(mA)'], data['Voltage(mV)'], color='black', label='measured data')
# linear fit
plt.plot(x_linear_vis, intercept + slope * x_linear_vis, color='black', linestyle='--', label='linear fit')

# legend
plt.legend(fontsize=12, prop={'family': 'Times New Roman'},frameon=False)

# removing non-axis sides
ax = plt.gca() 
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# axis limits
plt.xlim(0, 4500)

# axis titles
plt.xlabel('Current (mA)', fontsize=14, fontname='Times New Roman')
plt.ylabel('Voltage (mV)', fontsize=14, fontname='Times New Roman')

# axis ticks
plt.tick_params(axis='both', labelsize=12)
plt.xticks(range(0, 4400, 400), fontname='Times New Roman')
plt.yticks(range(1500, 3500, 200), fontname='Times New Roman')

# show the graph
plt.show()

### print-test ###
#print(df)
#print(data)
#print(x_data)
#print(type(x_data))
#print(x_linear)
print(lingress_res)

### code-references ###
# https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.scatter.html
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html 