""" Cleaning output files """
######### Package Imports ###################################################################

import os, shutil

######### Function Definitions ##############################################################

def clean_up_output(filename_start,path):
    """Delete output files from the simulation

    Parameters
    ----------
    filename_start : string
        string containing the beginning of the filename to delete
    path : string
        path to the directory where we clean the output
    """ 
    for fname in os.listdir(path):
        if fname.startswith(filename_start) and not os.path.isdir(os.path.join(path,fname)):
            os.remove(os.path.join(path,fname))

def store_output_in_folder(filenames,folder_name,path):
    """Move output files from the simulation into new folder

    Parameters
    ----------
    filenames : list of string
        list of string containing the name of the files to move
    folder_name : string
        name of the folder where we store the output files       
    path : string
        directory of the folder_name (creates one if it does not already exist)
    """    

    # Create directory if it does not exist
    if not os.path.exists(os.path.join(path,folder_name)):
        os.makedirs(os.path.join(path,folder_name))
    # move file into the new folder
    for i in filenames:
        if os.path.exists(os.path.join(path,i)):
            os.replace(os.path.join(path,i),os.path.join(path,folder_name,i))
        else:
            print('File {} does not exist'.format(os.path.join(path,i)))

def clean_file_type(ext,path):
    """Delete files of a given type in the current directory

    Parameters
    ----------
    ext : string
        extension of the files to delete 
    path : string
        path to the directory where we clean the output

    """ 
    for fname in os.listdir(path):
        if fname.endswith(ext):
            os.remove(os.path.join(path,fname))

def clean_all_output(path,filename_starts = ['JV','Var','tj','tVG','scPars','Str4Parallel','log'],exts = ['.png']):
    """Delete all files in the current directory

    Parameters
    ----------
    path : string
        path to the directory where we clean the output
    filename_starts : list of string
        list of string containing the beginning of the filename to delete, default is ['JV','Var','tj','tVG','scPars','Str4Parallel','log']
    exts : list of string
        list of string containing the extension of the files to delete, default is ['.png']
    
    """ 
    

    for filename_start in filename_starts:
        clean_up_output(filename_start,path)

    for ext in exts:
        clean_file_type(ext,path)

def delete_folders(folder_name_start,path):
    """Delete all folders starting with a given name in the current directory, even if they are not empty

    Parameters
    ----------
    folder_name : string
        name of the folder to delete
    path : string
        path to the directory where we delete the folder

    """ 
    for fname in os.listdir(path):
        folder_path = os.path.join(path, fname)
        if fname.startswith(folder_name_start) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            
