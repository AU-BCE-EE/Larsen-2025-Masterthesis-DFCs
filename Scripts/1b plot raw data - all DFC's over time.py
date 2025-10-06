### Script description ###
# reads raw data, txt-files from a designated inputfolder, should combine data from all files
# plot concentration [ppb] as a function of time independant of valves
# select data related to a single valve, and plot this as a function of time

### Currrent version ###

### Packages ### 
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

### Scrip initialization ####
# Folders
# copy the filepath.Put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\Actual data - only 1 file")

# Starting time
# starting time of the first meassurement in this experiment, not simply this file wherefore it has to be input here, remember '' to create a string
date = '2023-04-12' # [y-m-d] ex 2023-04-12 
time = '12:05:11.196' # [h-min-s.ms] ex 12:05:11.195
start_time = pd.to_datetime(date + ' ' +  time, format="%Y-%m-%d %H:%M:%S.%f")  # ading the time and date string together using equivalent formatting as the meassurents

# creating empty series-object to save the data for plotting, pandas need to have the type specified
times = pd.Series(dtype=float)
Cs = pd.Series(dtype=float)

### Actual Code-section ###

for txt_file in input_folder.glob("*.txt"): # loops over txt-files in the inputfolder (txt-file specific as an extra precuation to avoid errors)
    current_df = pd.read_csv(txt_file, sep=r'\s+') # loads the current file in the loop as a table(pd-dataframe), indicating that the collum seperator is several empty spaces
    # precation, creating a copy to maintain the original file as is
    #print(current_table)
    #print(current_table_copy["TIME"])

    ## Normalizing time ##

    # Creating a new collum with time and date 
    current_df['DATE_TIME'] = current_df['DATE'] + ' ' + current_df['TIME'] # combines the time and date id's in a single new collum
    #print(current_table_copy["DATETIME"].iloc[0])

    # remmoving individual time and date collums
    current_df = current_df.drop(columns=['DATE', 'TIME'])
    #print(current_table_copy.head(10)) # prints the first 10 datapoints of a collum as a manual check of the code

    # using a built-in panda-function to intepret the DATE_TIME as time-values, not simply strings
    current_df['DATE_TIME'] = pd.to_datetime(current_df['DATE_TIME'], format="%Y-%m-%d %H:%M:%S.%f") 
    #print(type(current_table_copy["DATE_TIME"].iloc[0]))
    
    # Creating a new collum with normalized time
    current_df['TIME_NORMALIZED'] = (current_df['DATE_TIME'] - start_time).dt.total_seconds() / 60 # [min]
    #print(current_table_copy["TIME_NORMALIZED"].iloc[0])

    ## Extracting relevant data into the series-object ##
    
    # add relevant data from this file into the series'
    times = pd.concat([times, current_df['TIME_NORMALIZED']], ignore_index=True)
    Cs = pd.concat([Cs, current_df['NH3']], ignore_index=True)
    
## Plot the stuff ## 
# note to self, create a std-plot function
plt.plot(times , Cs, '.-k')
# make the graph pretty
plt.xlabel('time [min]', fontsize=12)
#plt.xlim([0, max(times)*1.1]) # automatic definition of the x-axis
plt.xlim([0, 150]) # manual definition of the x-axis
plt.ylabel('concentration [ppb]', fontsize=12)
plt.ylim([0,max(Cs)*1.1])

# show the graph
plt.show()
    

### Code references ### 
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.drop.html 
# https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html 