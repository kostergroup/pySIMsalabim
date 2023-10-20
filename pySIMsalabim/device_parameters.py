#############################################################################################
############################### Read and get parameters from ################################
############################### device_parameters.txt or cmd ################################
#############################################################################################

# Description:
# ------------
# This file contains the functions to read the device_parameters.txt file and store the parameters in a List object.

######### Package Imports ###################################################################
import os, random, shutil

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