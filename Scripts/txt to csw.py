
### Script description ###
# Read txt-files from a designated input-folder
# Create copies of these
# Bulk-save the copies as Csw-files in a designated outputfolder if a file with the same name doesnt already exist 

### Packages ###
from pathlib import Path
import pandas as pd

### Variables ###
# copy the filepath
# put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\Data\testdata\NH3 data") 
output_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\data")

### File conversion ###
for txt_file in input_folder.glob("*.txt"): # loops over txt-files in the inputfolder
    csv_file = output_folder / (txt_file.stem + ".csv") # the path for the csv-copy

    if csv_file.exists(): # skips filenames already existing in the outputfolder
        print(f"Skipping {csv_file.name}, already exists")
        continue

    # Load the .txt file (adjust separator if needed)
    current_file = pd.read_csv(txt_file, sep="\t")  
    
    # Save as .csv
    current_file.to_csv(csv_file, index=False)
    print(f"Saved {csv_file.name}")

print('Conversion Performed')

### Code references ###
# https://www.digitalocean.com/community/tutorials/python-raw-string
# https://www.geeksforgeeks.org/python/convert-text-file-to-csv-using-python-pandas/

