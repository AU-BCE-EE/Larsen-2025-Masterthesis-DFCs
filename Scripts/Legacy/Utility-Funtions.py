### Script Description ###
# Generalized functions, therefore able to be reapplied

### Packages ###
import pandas as pd

### Functions ###
# Dataframe handeling:
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

# File and folder handeling:
def load_csv_file_as_df(file_path):
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    returns: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # ex the raw DAT file needs to be loaded as:
    # pd.read_csv(file_path, sep=r'\s+', engine='python') indicating collums in the file are seperated with several empty spaces

def save_df_as_csv(df, output_folder, output_file_name, overwrite = True):
    '''
    saves a df as a csv-file
    
    Input:
        df the dataframe to be saved
        output_folder (path-object) path of the outputfolder
        output_file_name wanted name of the csv-file
        overwrite (True/False) whether to overwrite existing files with the same name

    Output:
        a csv-file with a user-specified name in a user-specified folder
    '''
    output_file = output_folder / f"{output_file_name}.csv"

    if output_file.exists() and not overwrite:
        print(f"Skipping existing file: {output_file.name}")
        return

    df.to_csv(output_file, index=False)
    print(f" output_file saved as: {output_file}")
    

### Input and output folders ###

### Constants ###

### Script Excecution ###

### Print-calls ###

### Code references ###