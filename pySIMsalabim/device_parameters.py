#############################################################################################
############################### Read and get parameters from ################################
############################### device_parameters.txt or cmd ################################
#############################################################################################

# Description:
# ------------
# This file contains the functions to read the device_parameters.txt file and store the parameters in a List object.

######### Package Imports ###################################################################
import os, random, shutil, sys, re

######### Function Definitions ##############################################################

def ReadParameterFile(path2file):
    """Get all the parameters from the 'device_parameters.txt' file
    for SIMsalabim and ZimT

    Parameters
    ----------
    path2file : str
        Path to the 'device_parameters.txt'

    Returns
    -------
    dict
        Contains the parameters and values from the 'device_parameters.txt'
    """    
    
    lines = []
    ParFileDic = {}
    # check if the file exists
    if not os.path.isfile(path2file):
        raise FileNotFoundError('The file '+path2file+' does not exist')

    # read the file
    with open(path2file) as f:
        lines = f.readlines()

    count = 0
    for line in lines:
        line = line.replace(' ', '')
        if line[0] != '*' and (not line.isspace()):
            equal_idx = line.find('=')
            star_idx = line.find('*')
            ParFileDic[line[0:equal_idx] ] = line[equal_idx+1:star_idx]
            count += 1
   
    return ParFileDic


def GetParFromStr(str2run):
    """Get parameters from command string for SIMsalabim or ZimT

    Parameters
    ----------
    str2run : str
        Command string for SIMsalabim or ZimT

    Returns
    -------
    dict
        Contains the parameters and values from the command string
    """    

    str2run = ' '.join(str2run.split()) #remove extra white space
    # find first '-' and remove everything before
    str2run = str2run[str2run.find('-'):]
    str2run = str2run.split()

    Names= str2run[::2]
    Values = str2run[1::2]
    ParStrDic = {}
    for i,j in enumerate(Names):
        Names[i] = Names[i].replace('-', '')
        # Values[i] = float(Values[i])
        try: # if the value is a float
            ParStrDic[Names[i]] = float(Values[i])
        except: # if the value is a string
            ParStrDic[Names[i]] = Values[i]
    return ParStrDic


def ChosePar(parname,ParStrDic,ParFileDic):
    """Chose if we use parameter from 'device_parameters.txt'
    or from the command string for SIMsalabim and ZimT

    Parameters
    ----------
    parname : str
        Parameter name as defined in 'device_parameters.txt' file
    ParStrDic : dict
        Contains the parameters and values from the command string
    ParFileDic : dict
        Contains the parameters and values from the 'device_parameters.txt'

    Returns
    -------
    str
        String of the parameter value (need to be converted to float if needed)
    """    
    if parname in ParStrDic.keys():
        parval = ParStrDic[parname]
    else :
        parval = ParFileDic[parname]
    
    return parval

def DevParFromStr(str2run):
    """Get the device parameters from the command string if any are given
    otherwise use the default values from the 'device_parameters.txt' file

    Parameters
    ----------
    str2run : str
        Command string for SimSS or ZimT

    Returns
    -------
    str
        Path to the 'device_parameters.txt' file
    """    
    # remove double spaces
    str2run = ' '.join(str2run.split())
    # find first '-' in str2run
    idx = str2run.find('-')
    # remove everything after
    str2run = str2run[:idx]
    # find the first space in str2run
    idx = str2run.find(' ')
    # remove everything before
    str2run = str2run[idx+1:]
    # remove all spaces
    str2run = str2run.replace(' ', '')

    return str2run

def CheckProgVersion(path2file):
    """Check for the program version number in device_parameters.txt

    Parameters
    ----------
    path2file : str
        path to the device_parameters.txt file
    """    
    
    lines = []
    ParFileDic = {}
    with open(path2file) as f:
        lines = f.readlines()
    
    for i in lines:
        try:
            if 'version:' in i:
                str_line = re.sub(r"\s+", "", i, flags=re.UNICODE)
                idx = str_line.find(':')
                version = float(str_line[idx+1:])
        except ValueError:
            sys.exit("Version number is not in the file or is not a float, execution is stopped.\nPlease review the device_parameters.txt file in folder:\n"+path2file)
    if version < 4.33:
        sys.exit('You are running an older version of SIMsalabim which has not been tested with this version of the code. This may lead to issues.\nPlease update your SIMsalabim version to 4.33 or higher.\nExecution is stopped.')
    return(version)

def MakeDevParFileCopy(path2file,path2file_copy):
    """Make a copy of the file 'path2file in 'path2file_copy

    Parameters
    ----------
    path2file : str
        absolute path to the simulation folder that contains the device_parameters.txt file.
    path2file_copy : _type_
        absolute path to the simulation folder that will contain the device_parameters_old.txt file.
    """    
    shutil.copyfile(path2file,path2file_copy)

def UpdateDevParFile(ParFileDic,path2file,fullpath=True,MakeCopy=True):
    """Update the device_parameters.txt with the values contained in ParFileDic
    Has to be used with SIMsalabim v4.33 or higher

    Parameters
    ----------
    ParFileDic : dic
        Dictioanry containing the values to be written in the file.
    path2file : str
        absolute path to the simulation folder that contains the device_parameters.txt file. 
    MakeCopy : bool, optional
        Make a copy of the previous device_parameters.txt file in device_parameters_old.txt, by default True
    """    

    # Saves a copy of the original device_parameters.txt file
    

    if MakeCopy:
        path2file_old = os.path.join(path2file,'device_parameters_old.txt')
        if not fullpath:
            path2file = os.path.join(path2file,'device_parameters.txt')
        MakeDevParFileCopy(path2file,path2file_old)
    else:
        if not fullpath:
            path2file = os.path.join(path2file,'device_parameters.txt')
    
    # Check for version number
    CheckProgVersion(path2file)

    with open(path2file) as f: # read lines in device_parameters.txt
        lines = f.readlines()
    newlines = []
    

    for i in lines:
        str_line = re.sub(r"\s+", "", i, flags=re.UNICODE)

        if str_line.startswith('*') or len(str_line) == 0: # line is a comment
            newlines.append(i)
        else:
            idx1 = str_line.find('=') # index of '='
            idx2 = str_line.find('*') # index of '*'

            i_start = i.find('=')
            i_end = i.find('*')
            # if len(idx):
            str1 = i[:i_start+1]
            str2 = i[i_end:] 
            if str_line[:idx1] in ParFileDic.keys():
                newlines.append(str1 + ' ' + str(ParFileDic[str_line[:idx1]]) + ' '*10 + str2)
            else:
                newlines.append(i)
    with open(path2file, 'w') as f: # write new lines in device_parameters.txt
        for line in newlines:
            f.write(line)