"""Functions for processing the device parameters"""
######### Package Imports #########################################################################

import os, sys, shutil, random, re
import numpy as np
import pandas as pd

######### Function Definitions ####################################################################

def load_device_parameters(session_path, dev_par_file_name, default_path=os.path.join('SIMsalabim', 'ZimT'), reset = False, availLayers = [], run_mode = False):
    """Load the device_parameters file and create a List object. Check if a session specific file already exists. 
    If True, use this one, else return to the default device_parameters

    Parameters
    ----------
    session_path : string
        Folder path of the current simulation session
    dev_par_file_name : string
        Name of the device parameters file
    default_path : string
        Path name where the default/standard device parameters file is located
    reset : boolean
        If True, the default device parameters are copied to the session folder
    availLayers : List
        List with all the available layer files
    run_mode : bool, optional
        indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default True


    Returns
    -------
    List
        List with nested lists for all parameters in all sections.
    List
        List with all the layers
    """
    dev_par = {}
    if run_mode == True:
        # Check if the session specific device parameter file exists. If not, copy the default file to the session folder.
        if not os.path.isfile(os.path.join(session_path, dev_par_file_name)) or (reset == True):
            shutil.copy(os.path.join(default_path, dev_par_file_name), session_path) # The simulation_setup_file
            file_list = os.listdir(default_path)
            for file in file_list:
                if (file.endswith('_parameters.txt')):
                    shutil.copy(os.path.join(default_path, file), session_path) # The layer files

    # Read the simulation_setup file and store all lines in a list
    with open(os.path.join(session_path, dev_par_file_name), encoding='utf-8') as fp:
        # First check how many layers are defined.
        layersSection = False
        layers = [['par', 'setup',dev_par_file_name,dev_par_file_name]] # Initialize the simulation setup file. This is identified by key 'setup'

        for line in fp:
            # Read all lines from the file
            if line.startswith('**'):
            # Left adjusted comment
                comm_line = line.replace('*', '').strip()
                if ('Layers' in comm_line):  # Found section with the layer files
                    layersSection = True
                else:
                    layersSection = False
            else:
                    # Line is either a parameter or leftover comment.
                par_line = line.split('*')
                if '=' in par_line[0]:  # Line contains a parameter
                    par_split = par_line[0].split('=')
                    par = ['par', par_split[0].strip(), par_split[1].strip(),par_line[1].strip()] # The element with index 2 contains the actual file name!
                    if layersSection: # If the line is in the layer section, it contains the name of a layer file, thus add it to the Layers list
                        layers.append(par) # Add sublist to the layers list 
        fp.close()

    # Read each layer file and append it as a sublist in the main dev_par list
    for layer in layers:
        with open(os.path.join(session_path, layer[2]), encoding='utf-8') as fp:
            dev_par[f'{layer[2]}'] = devpar_read_from_txt(fp)
            fp.close()
    
    if run_mode == True:
        # Now load the layer files that are not in the simulation_setup but have been defined or created before
        devLayerList = []
        for layer in layers:
            devLayerList.append(layer[2])

        extraLayers = []
        for layer in availLayers:
            if layer not in devLayerList:
                extraLayers.append(layer)

        # Read each extra layer file and append it as a sublist in the main dev_par list
        for layer in extraLayers:
            with open(os.path.join(session_path, layer), encoding='utf-8') as fp:
                dev_par[f'{layer}'] = devpar_read_from_txt(fp)
                fp.close()
    return dev_par, layers

def devpar_read_from_txt(fp):
    """Read the opened .txt file line by line and store all in a List.

    Parameters
    ----------
    fp : TextIOWrapper
        filepointer to the opened .txt file.

    Returns
    -------
    List
        List with nested lists for all parameters in all sections.
    """
    index = 0
    # Reserve the first element of the list for the top/header description
    dev_par_object = [['Description']]

    # All possible section headers
    section_list = ['General', 'Layers', 'Contacts', 'Optics', 'Numerical Parameters', 'Voltage range of simulation', 'User interface','Mobilities', 'Interface-layer-to-right', 'Ions', 'Generation and recombination', 'Bulk trapping']
    for line in fp:
        # Read all lines from the file
        if line.startswith('**'):
        # Left adjusted comment
            comm_line = line.replace('*', '').strip()
            if (comm_line in section_list):  # Does the line match a section name
                # New section, add element to the main list
                dev_par_object.append([comm_line])
                index += 1
            else:
                # A left-adjusted comment, add with 'comm' flag to current element
                dev_par_object[index].append(['comm', comm_line])
        elif line.strip() == '':
        # Empty line, ignore and do not add to dev_par_object
            continue
        else:
        # Line is either a parameter or leftover comment.
            par_line = line.split('*')
            if '=' in par_line[0]:  # Line contains a parameter
                par_split = par_line[0].split('=')
                par = ['par', par_split[0].strip(), par_split[1].strip(),par_line[1].strip()]
                dev_par_object[index].append(par)
            else:
                # leftover (*) comment. Add to the description of the last added parameter
                dev_par_object[index][-1][3] = dev_par_object[index][-1][3] + \
                    "*" + par_line[1].strip()
    return dev_par_object

def store_file_names(dev_par, sim_type, dev_par_name, layers, run_mode = False): #
    """Read the relevant file names from the device parameters and store the file name in a session state. 
        This way the correct and relevant files can be retrieved and used in the results. Make a distinction between simss and zimt.

    Parameters
    ----------
    dev_par : List
        Nested List object containing all device parameters
    sim_type : string
        Which type of simulation to run: simss or zimt
    dev_par_name : string
        Name of the device parameter file
    layers : List
        List with all the layers in the device
    run_mode : bool, optional
        indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default True
    """
    
    # make sure sim_type is simss or zimt
    sim = sim_type.lower()
    if sim not in ['simss', 'zimt']:
        raise ValueError('sim_type must be either simss or zimt')

    # st.session_state['LayersFiles'] = []
    LayersFiles = []
    genProfile = 'none'
    expjv_id = False
    varFile = 'none'
    logFile = 'none'
    expJV = 'none'
    JVFile = 'none'
    scParsFile = 'none'
    tVGFile = 'none'
    tJFile = 'none'
    opticsFiles = []

    # Get the relevant file names from the device parameters
    for section in dev_par[dev_par_name][1:]:
        # Generation profile
        if section[0] == 'Optics':
            for param in section:
                if param[1] == 'genProfile':
                    if param[2] != 'none' and param[2] != 'calc':
                        genProfile = param[2]
                        # st.session_state['genProfile'] = param[2]
                    elif param[2] == 'calc':
                        genProfile = 'calc'
                        # st.session_state['genProfile'] = 'calc'
                    else:
                        genProfile = 'none'
                        # st.session_state['genProfile'] = 'none'
        
        # Files in USer Interface section
        if section[0] == 'User interface':
            for param in section:
                if param[1] == 'varFile':
                    varFile = param[2]
                    # st.session_state['varFile'] = param[2]
                if param[1] == 'logFile':
                    logFile = param[2]
                    # st.session_state['logFile'] = param[2]
                if sim == 'simss':
                    if param[1] == 'useExpData':
                        if param[2] != '1':
                            expjv_id = False
                            expJV = 'none'
                            # st.session_state['expJV'] = 'none'
                        else:
                            expjv_id = True
                    if param[1] == 'expJV' and expjv_id is True:
                        expJV = param[2]
                        # st.session_state['expJV'] = param[2]
                    if param[1] == 'JVFile':
                        JVFile = param[2]
                        # st.session_state['JVFile'] = param[2]
                    if param[1] == 'scParsFile':
                        scParsFile = param[2]
                        # st.session_state['scParsFile'] = param[2]
                if sim == 'zimt':
                    if param[1] == 'tVGFile':
                        tVGFile = param[2]
                        # st.session_state['tVGFile'] = param[2]
                    if param[1] == 'tJFile':
                        tJFile = param[2]
                        # st.session_state['tJFile'] = param[2]
                        
        if section[0] == 'Layers':
            for param in section[1:]:
                LayersFiles.append(param[2])
                # st.session_state['LayersFiles'].append(param[2])

    # When the generation profile has been calculated, store the names of the nk and spectrum files. QQQ process for each layer!
    # if st.session_state['genProfile'] == 'calc':
    if genProfile == 'calc':
        opticsFiles = []
        # st.session_state['opticsFiles'] = []
        specfile = ''
        # Get the spectrum and nk files from the simulation setup
        for section in dev_par[dev_par_name][1:]:
            if section[0] == 'Optics':
                for param in section:
                    if param[1].startswith('nk'):
                        opticsFiles.append(param[2])
                        # st.session_state['opticsFiles'].append(param[2])
                    elif param[1]=='spectrum':
                        specfile = param[2]


    # Go over the layer files for trap files and nk files
    # st.session_state['traps_int'] = []
    # st.session_state['traps_bulk'] = []
    traps_int = []
    traps_bulk = []

    usedFiles= [] 
    for layer in layers:
        if not layer[2] in usedFiles: # We only want to check the layer parameter files that have been used in the simulation
            usedFiles.append(layer[2])

    # Get the nk file for each layer
    for usedFile in usedFiles:
        for section in dev_par[usedFile][1:]:
            # if st.session_state['genProfile'] == 'calc':
            if genProfile == 'calc':
                if section[0] == 'Generation and recombination':
                    for param in section:
                        if param[1].startswith('nk'):
                            opticsFiles.append(param[2])
                            # st.session_state['opticsFiles'].append(param[2])
                
            
    # We need to check every layer files whether files for the trap distribution have been used for interface and/or bulk traps.
    # If present, add file name to list, if not add 'none' to the list. We will process this when preparing the download of the files.
            if section[0] == 'Interface-layer-to-right':
                for param in section:
                    if param[1] == 'intTrapFile':
                        if param[2] != 'none':
                            traps_int.append(param[2])
                            # st.session_state['traps_int'].append(param[2])
                        else:
                            traps_int.append('none')
                            # st.session_state['traps_int'].append('none')

            if section[0] == 'Bulk trapping':
                for param in section:
                    if param[1] == 'bulkTrapFile':
                        if param[2] != 'none':
                            traps_bulk.append(param[2])
                            # st.session_state['traps_bulk'].append(param[2])
                        else:
                            traps_bulk.append('none')
                            # st.session_state['traps_bulk'].append('none')

    # Add the name of the spectrum file to the end of the array
    # if st.session_state['genProfile'] == 'calc':
    if genProfile == 'calc':
        opticsFiles.append(specfile)
        # st.session_state['opticsFiles'].append(specfile)

    if run_mode == True:
        return LayersFiles, opticsFiles, genProfile, traps_int, traps_bulk, expJV, varFile, logFile, JVFile, scParsFile, tVGFile, tJFile      
    else:
        if sim == 'simss':
            return LayersFiles, opticsFiles, traps_int, traps_bulk, expJV, varFile, logFile, JVFile, scParsFile
        else:
            return LayersFiles, opticsFiles, traps_int, traps_bulk, tVGFile, varFile, logFile, tJFile


def devpar_read_from_txt(fp):
    """Read the opened .txt file line by line and store all in a List.

    Parameters
    ----------
    fp : TextIOWrapper
        filepointer to the opened .txt file.

    Returns
    -------
    List
        List with nested lists for all parameters in all sections.
    """
    index = 0
    # Reserve the first element of the list for the top/header description
    dev_par_object = [['Description']]

    # All possible section headers
    section_list = ['General', 'Layers', 'Contacts', 'Optics', 'Numerical Parameters', 'Voltage range of simulation', 'User interface','Mobilities', 'Interface-layer-to-right', 'Ions', 'Generation and recombination', 'Bulk trapping']
    for line in fp:
        # Read all lines from the file
        if line.startswith('**'):
        # Left adjusted comment
            comm_line = line.replace('*', '').strip()
            if (comm_line in section_list):  # Does the line match a section name
                # New section, add element to the main list
                dev_par_object.append([comm_line])
                index += 1
            else:
                # A left-adjusted comment, add with 'comm' flag to current element
                dev_par_object[index].append(['comm', comm_line])
        elif line.strip() == '':
        # Empty line, ignore and do not add to dev_par_object
            continue
        else:
        # Line is either a parameter or leftover comment.
            par_line = line.split('*')
            if '=' in par_line[0]:  # Line contains a parameter
                par_split = par_line[0].split('=')
                par = ['par', par_split[0].strip(), par_split[1].strip(),par_line[1].strip()]
                dev_par_object[index].append(par)
            else:
                # leftover (*) comment. Add to the description of the last added parameter
                dev_par_object[index][-1][3] = dev_par_object[index][-1][3] + \
                    "*" + par_line[1].strip()
    return dev_par_object

def devpar_write_to_txt(dev_par_object):
    """Convert the List object into a single string. Formatted to the device_parameter definition

    Parameters
    ----------
    dev_par_object : List
        List object with all parameters and comments.

    Returns
    -------
    string
        Formatted string for the txt file
    """
    par_file = []  # Initialize List to hold all lines
    lmax = 0  # Max width of 'parameter = value' section, initialise with 0
    section_length_max = 84 # Number of characters in the section title

    # Description and Version
    for item in dev_par_object[0][1:]:
        # First element of the main object contains the top description lines. Skip very first element (Title).
        desc_line = "** " + item[1] + '\n'
        par_file.append(desc_line)

    # Determine max width of the 'parameter = value' section of the txt file to align properly.
    for sect_item in dev_par_object[1:]:
        # Loop over all sections
        for par_item in sect_item[1:]:
            # Loop over all parameters
            if par_item[0] == 'par':
                # Only real parameter entries need to be considered, characterised by the first list element being 'par'
                temp_string = par_item[1] + ' = ' + par_item[2]
                if len(temp_string) > lmax:
                    # Update maxlength if length of 'par = val' combination exceeds it.
                    lmax = len(temp_string)
    # Add 1 to max length to allow for a empty space between 'par=val' and description.
    lmax = lmax + 1

    # Read every entry of the Parameter List object and create a formatted line (string) for it. Append to string List par_file.
    for sect_element in dev_par_object[1:]:
        # Loop over all sections. Exclude the first (Description Title) element.

        ## Section
        # Start with a new line before each section name. Section title must be of format **title************...
        par_file.append('\n')
        sec_title = "**" + sect_element[0]
        sec_title_length = len(sec_title)
        sec_title = sec_title + "*" * \
            (section_length_max-sec_title_length) + '\n'
        par_file.append(sec_title)

        ## Parameters
        for par_element in sect_element:
            #  Loop over all elements in the section list, both parameters ('par') and comments ('comm')
            if par_element[0] == 'comm':
                # Create string for a left-justified comment and append to string List.
                par_line = '** ' + par_element[1] + '\n'
                par_file.append(par_line)
            elif par_element[0] == 'par':
                # Create string for a parameter. Format is par = val
                par_line = par_element[1] + ' = ' + par_element[2]
                par_line_length = len(par_line)
                # The string is filled with blank spaces until the max length is reached
                par_line = par_line + ' '*(lmax - par_line_length)
                # The description can be a multi-line description. The multiple lines are seperated by a '*'
                if '*' in par_element[3]:
                    # MultiLine description. Split it and first append the par=val line as normal
                    temp_desc = par_element[3].split('*')
                    par_line = par_line + '* ' + temp_desc[0] + '\n'
                    par_file.append(par_line)
                    for temp_desc_element in temp_desc[1:]:
                        #  For every extra comment line, fill left part of the line with empty characters and add comment/description as normal.
                        par_line = ' '*lmax + '* ' + temp_desc_element + '\n'
                        par_file.append(par_line)
                else:
                    # Single Line description. Add 'par=val' and comment/description together, seperated by a '*'
                    par_line = par_line + '* ' + par_element[3] + '\n'
                    par_file.append(par_line)

    # Join all individual strings/lines together
    par_file = ''.join(par_file)

    return par_file

def get_inputFile_from_cmd_pars(sim_type, cmd_pars):
    """Get the input file name from the command line parameters except the layer files

    Parameters
    ----------
    sim_type : string
        Which type of simulation to run: simss or zimt
    cmd_pars : List
        List with the command line parameters
    except_layers : bool, optional
        If True, the layer files are excluded from the list, by default True

    Returns
    -------
    string
        The name of the input file
    """
    input_files, newlayers = [], []
    # make sure sim_type is simss or zimt
    sim = sim_type.lower()
    if sim not in ['simss', 'zimt']:
        raise ValueError('sim_type must be either simss or zimt')

    ignore_output_files = ['JVFile', 'scParsFile', 'tJFile', 'varFile', 'logFile']

    # Get the input file name from the command line parameters
    if sim == 'simss':
        for cmd_par in cmd_pars:

            # if not except_layers:
            # if cmd_par['par'].startswith('l') and cmd_par['par'][1:].isdigit(): # layerfile
            #     # input_files.append(cmd_par)
            #     print('1')
            #     newlayers.append(cmd_par)

            if cmd_par['par'].endswith('File') and not cmd_par['par'] in ignore_output_files:
                input_files.append(cmd_par)
            
            if cmd_par['par'] == 'expJV' and cmd_par['val'] != 'none':
                input_files.append(cmd_par)
            
            if cmd_par['par'] == 'genProfile' and (cmd_par['val'] != 'calc' and cmd_par['val'] != 'none'):
                input_files.append(cmd_par)

            # for layer parameters split the cmd_pars[par] after .
            dum_par = cmd_par['par'].split('.')[-1]
            if dum_par.startswith('nk') :
                input_files.append(cmd_par)
            
            if cmd_par['par'] =='spectrum':
                input_files.append(cmd_par)

    else:
        for cmd_par in cmd_pars:
            # if cmd_par['par'].endswith('File') and not cmd_par['par'] in ignore_output_files:
            #     # input_files.append(cmd_par)
            #     newlayers.append(cmd_par)

            if cmd_par['par'].endswith('File') and not cmd_par['par'] in ignore_output_files:
                input_files.append(cmd_par)
            
            if cmd_par['par'] == 'genProfile' and (cmd_par['val'] != 'calc' or cmd_par['val'] != 'none'):
                input_files.append(cmd_par)

            # for layer parameters split the cmd_pars[par] after .
            dum_par = cmd_par['par'].split('.')[-1]
            if dum_par.startswith('nk') :
                input_files.append(cmd_par)
            
            if cmd_par['par'] =='spectrum':
                input_files.append(cmd_par)


    return input_files #, newlayers

def get_inputFile_from_layer(layer, session_path):
    """Get the input file name from the layer parameters

    Parameters
    ----------
    layer : List
        List with the layer parameters
    session_path : string
        Folder path of the current simulation session

    Returns
    -------
    string
        The name of the input file
    """
    # read the layer file
    with open(os.path.join(session_path, layer[2]), encoding='utf-8') as fp:
        layer_par = devpar_read_from_txt(fp)
        fp.close()
    section2update = ['Layers', 'Optics', 'Generation and recombination', 'Interface-layer-to-right', 'Bulk trapping']
    ignore_output_files = ['JVFile', 'scParsFile', 'tJFile', 'varFile', 'logFile']
    input_files = []
    for section in layer_par[layer[2]][1:]:
        if section[0] in section2update:
            for param in section[1:]:
                if param[0] == 'par':
                    if param[1].endswith('File') and not param[1] in ignore_output_files:
                        input_files.append(param)
                    if param[1] == 'expJV':
                        if param[2] != 'none':
                            input_files.append(param)
                    if param[1] == 'genProfile':
                        if param[2] != 'calc' and param[2] != 'none':
                            input_files.append(param)
                    if param[1].startswith('nk'):
                        input_files.append(param)
                    if param[1] == 'spectrum':
                        input_files.append(param)
                               
    return input_files

def make_basename_file_cmd_pars(cmd_pars,except_output_files = True):
    """ Update the command line parameters with the basename of the input files

    Parameters
    ----------
    cmd_pars : List
        List with the command line parameters
    except_output_files : bool, optional
        If True, the output files names are not updated, by default True

    Returns
    -------
    List
        List with the updated command line parameters
    """
    ignore_output_files = ['JVFile', 'scParsFile', 'tJFile', 'varFile', 'logFile']
    for idx, cmd_par in enumerate(cmd_pars):
        if cmd_par['par'] == 'dev_par_file':
            cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])

        if cmd_par['par'] == 'genProfile':
            if cmd_par['val'] != 'calc' and cmd_par['val'] != 'none':
                cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])

        if cmd_par['par'] == 'expJV':
            if cmd_par['val'] != 'none':
                cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])
        
        if cmd_par['par'].endswith('File'):
            if except_output_files:
                if not cmd_par['par'] in ignore_output_files:
                    cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])
            else:
                cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])
    
        if cmd_par['par'].startswith('l') and cmd_par['par'][1:].isdigit():
            cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])

        if cmd_par['par'].startswith('nk'):
            cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])

        if cmd_par['par'] == 'spectrum':
            cmd_pars[idx]['val'] = os.path.basename(cmd_par['val'])

    return cmd_pars

def make_basename_input_files(filename, updateFile = True):
    """Update the layer file with the basename of the input files

    Parameters
    ----------
    filename : string
        path to the layer file
    updateFile : bool, optional
        if True, the layer file is updated with the new file names, else the updated layer file list is returned, by default True

    Returns
    -------
    List
        List with the updated layer parameters
    """    
    # read the layer file
    with open(filename, encoding='utf-8') as fp:
        layer_par = devpar_read_from_txt(fp)
        fp.close()
    
    section2update = ['Layers', 'Optics', 'Generation and recombination', 'Interface-layer-to-right', 'Bulk trapping']
    ignore_output_files = ['JVFile', 'scParsFile', 'tJFile', 'varFile', 'logFile']
    for section in layer_par:
        if section[0] in section2update:
            for param in section[1:]:
                if param[0] == 'par':
                    if param[1].endswith('File') and not param[1] in ignore_output_files:
                        param[2] = os.path.basename(param[2])
                    if param[1].startswith('nk'):
                        param[2] = os.path.basename(param[2])
                    if param[1] == 'spectrum':
                        param[2] = os.path.basename(param[2])

    # Write the updated layer file
    if updateFile == True:
        with open(filename, 'w', encoding='utf-8') as fp:
            fp.write(devpar_write_to_txt(layer_par))
            fp.close()
    else:
        return layer_par


def get_par_from_dev_par(dev_par, par_name):
    """Get the parameter from the device parameters

    Parameters
    ----------
    dev_par : List
        List with the device parameters
    par_name : string
        Name of the parameter

    Returns
    -------
    List
        List with the parameter
    """
    for section in dev_par:
        for param in section[1:]:
            if param[1] == par_name:
                return param 

def ReadParameterFile(path2file):
    """Get all the parameters from the 'Device_parameters.txt' file
    for SIMsalabim and ZimT
    Parameters
    ----------
    path2file : str
        Path to the 'Device_parameters.txt'

    Returns
    -------
    dict
        Contains the parameters and values from the 'Device_parameters.txt'
    """    
    
    lines = []
    ParFileDic = {}
    with open(path2file) as f:
        lines = f.readlines()

    count = 0
    for line in lines:
        line = line.replace(' ', '')
        if line[0] != '*' and (not line.isspace()):
            equal_idx = line.find('=')
            star_idx = line.find('*')
            # print(line[0:equal_idx] , line[equal_idx+1:star_idx])
            ParFileDic[line[0:equal_idx] ] = line[equal_idx+1:star_idx]
            count += 1
            # print(f'line {count}: {line}')   
    return ParFileDic

# def update_dev_par(sim_type, cmd_pars, dev_par, layers):
#     """Update the device parameters with the command line parameters

#     Parameters
#     ----------
#     sim_type : string
#         Which type of simulation to run: simss or zimt
#     cmd_pars : List
#         List with the command line parameters
#     dev_par : List
#         List with the device parameters

#     Returns
#     -------
#     List
#         List with the updated device parameters
#     """
#     # make sure sim_type is simss or zimt
#     sim = sim_type.lower()
#     if sim not in ['simss', 'zimt']:
#         raise ValueError('sim_type must be either simss or zimt')

#     # Get the input file name from the command line parameters
#     # input_files, newlayers = get_inputFile_from_cmd_pars(sim_type, cmd_pars)

#     # Update the device parameters with the command line parameters
#     for 


#################### FUNCTIONS FOR CONTACTLESS DEVICE ##############################

def update_simulation_setup(session_path, simulation_setup, dev_pars, block_layer_file = 'Block.txt'):
    ''' Update the simulation setup file to add a layer on either side and change the layer indices.

    Parameters
    ----------
    session_path : str
        Path to the session folder
    simulation_setup : str
        Name of the simulation setup file
    dev_pars : dict
        Dictionary with the device parameters
    block_layer_file : str, optional
        Name of the blocking layer file, by default 'Block.txt'

    Returns
    -------
    dict
        Updated dictionary with the device parameters
    
    '''

    ## Update the simulation setup file with layer indices, blocking layers, work functions, and force the TCO and BE parameters
    for section in dev_pars[simulation_setup]:
        # Update layer indices
        if section[0] == 'Layers':
            for idx in range(1,len(section)):
                # First overwrite the original layer indices by shifting them with 1, i.e l1 becomes l2 etc.
                # We will insert the new layers after this.

                # Extract the original layer number from the parameter name, which is in the format lX where X is the layer number and increase it with 1
                layer_num  = int(section[idx][1].split('l')[1]) + 1 

                # Update the parameter name with the new layer number
                section[idx][1] = 'l' + str(layer_num)

            # Now insert the new layer at the first and last index
            section.insert(1, ['par', 'l1', block_layer_file, 'Parameter file for blocking layer'])
            section.append(['par', 'l' + str(len(section)), block_layer_file, 'Parameter file for blocking layer'])

            num_layers = len(section)-1
        
    # Write the updated simulation setup file
    simulation_setup_str = devpar_write_to_txt(dev_pars[simulation_setup])
    with open(os.path.join(session_path, simulation_setup), 'w', encoding='utf-8') as fp:
        fp.write(simulation_setup_str)
        fp.close()

    return dev_pars, num_layers
    
def create_block_layer(session_path, dev_pars, layers, block_layer_file = 'Block.txt', block_layer_mat='Air'):
    ''' Create a new layer file for the blocking layer, which is a copy of the first layer to use as a template.
    The parameters of the blocking layer are set to values that make it a blocking layer, 
    like a very thin (1nm) layer with a large band offsets and low effective density of states. 
    The nkLayer parameter is set to the block_layer_mat file.

    Parameters
    ----------
    session_path : str
        Path to the session folder
    dev_pars : dict
        Dictionary with the device parameters
    layers : list
        List with the layers in the device
    block_layer_file : str, optional
        Name of the blocking layer file, by default 'Block.txt'
    block_layer_mat : str, optional
        Name of the blocking layer material, by default 'Air'

    Returns
    -------
    None
    
    '''

    # Initialize a new layer file for the blocking layer, which is a copy of the first layer to use as a template
    block_layer_par = dev_pars[layers[1][2]]

    # Collect parameters that need to be set to 0 for the blocking layer
    pars_to_zero = ['N_D', 'N_A', 'N_t_int', 'N_anion', 'N_cation','ionsMayEnter', 'layerGen', 'N_t_bulk']

    # Go over every section of the layer parameter file and set the relevant parameters to the desired values for the blocking layer
    for section in block_layer_par:
        for line in section[1:]:
            if line[1] == 'L':
                line[2] = '1E-9' # Set the thickness to 1 nm
            elif line[1] == 'eps_r':
                line[2] = '1' # Set the relative permittivity to 1 (vacuum/~air)
            elif line[1] == 'E_c':
                line[2] = '1' # Set the conduction band to 1eV
            elif line[1] == 'E_v':
                line[2] = '9' # Set the valence band to 9eV
            elif line[1] == 'N_c':
                line[2] = '1' # Set the effective density of states in the conduction/valence band to 1
            elif line[1] == 'mu_n' or line[1] == 'mu_p':
                line[2] = '1E-5' # Set the mobility to 1E-5 m^2/Vs (an average value)
            elif line[1] == 'nkLayer':
                nkLayer_value = line[2]
                # split the nkLayer_value by /nk_ and replace the last part with Air.txt
                nkLayer_value_split = nkLayer_value.split('/nk_')
                nkLayer_value_split[-1] = f'{block_layer_mat}.txt'
                line[2] = nkLayer_value_split[0] + '/nk_' + nkLayer_value_split[-1] # Set the nkLayer to the block_layer_mat file
            elif line[1] == 'k_direct':
                line[2] = '1E-20' # Set the direct recomb rate to 1E-20 (very low)
            elif line[1] in pars_to_zero:
                line[2] = '0' # Set several parameters to 0

            # If the parameter is not one of the above, leave it as is, as it is does not have to be changed
    
    # Add the blocking layer to the dev_pars dict with the key being the block_layer_file name
    dev_pars[block_layer_file] = block_layer_par

    # Write the new blocking layer parameter file
    block_layer_str = devpar_write_to_txt(block_layer_par)
    with open(os.path.join(session_path, block_layer_file), 'w', encoding='utf-8') as fp:
        fp.write(block_layer_str)
        fp.close() 

    return dev_pars

def update_cmd_pars_contactless(cmd_pars):
    '''Update the command line parameters with new layer indices, which are now shifted by 1 for a contactless device.
    
    Parameters
    ----------
    cmd_pars : List
        List of dict with the command line parameters
    
    Returns
    -------
    List
        List of dict with the updated command line parameters
    '''

    for cmd_par in cmd_pars:
        # Split the value of the 'par' keey by '.' and check if there are only 2 elements
        par_split = cmd_par['par'].split('.')
        if len(par_split) == 2 and par_split[0].startswith('l') and par_split[0][1:].isdigit():
            # convert par_split[0][1:] to an integer
            layer_num = int(par_split[0][1:])
            layer_num +=1 

            # update the value of the 'par' key with the new layer number
            cmd_par['par'] = 'l' + str(layer_num) + '.' + par_split[1]

    return cmd_pars      

def calc_new_W_F(dev_pars, simulation_setup):
    ''' Calculate the new work function for a contactless device based on the conduction and valence band energies 
    of the available layers. We take the smallest difference between E_c and E_v (assumption: this is the PVK) and 
    set the work function to half the gap above E_c.

    Parameters
    ----------
    dev_pars : dict
        Dictionary with the device parameters
    simulation_setup : str
        Name of the simulation setup file

    Returns
    -------
    float
        Work function for the contactless device (equal for both sides)

    '''
    # Initialize arrays to hold the E_c and E_v values for each layer to calculate the work function W_F
    E_c_array = np.zeros((len(dev_pars)-1))
    E_v_array = np.zeros((len(dev_pars)-1))

    # Loop over all keys in the dev_pars dict but skip the key {simulation_setup} to get Ec and Ev
    for idx,key in enumerate(dev_pars.keys()):
        if key != simulation_setup:
            section_general = dev_pars[key][1] # The second section is the General section, which contains the E_c and E_v values ( The first is the description section)
            for param in section_general:
                # Extract E_c and E_v values and convert to float
                if param[1] == 'E_c':
                    E_c_array[idx-1] = float(param[2])
                if param[1] == 'E_v':
                    E_v_array[idx-1] = float(param[2])

    # Get the absolute difference between E_c and E_v for each layer
    min_gap_array = abs(E_c_array - E_v_array)

    # Find the smallest difference between E_c and E_v, including the associated index of the minimum gap
    min_gap = np.min(min_gap_array)
    min_gap_idx = np.argmin(min_gap_array)
  
    # Set the work function to half the gap
    W_F =  E_c_array[min_gap_idx] + 0.5*min_gap

    return W_F

def create_contactless_device(session_path, simulation_setup, block_layer_file = 'Block.txt', block_layer_mat='Air', force_last_interface = True, cmd_pars = None):
    ''' Create a contactless device by adding a blocking layer on either side of the device.
    This will change the input files! Depending on the flag in the output function, these files are kept or returned to their
    original state.

    Parameters
    ----------
    session_path : str
        Path to the session folder
    simulation_setup : str
        Name of the simulation setup file
    block_layer_file : str, optional
        Name of the blocking layer file, by default 'Block.txt'
    block_layer_mat : str, optional
        Name of the blocking layer material, by default 'Air'
    force_last_interface : bool, optional
        If True, the interface traps at the last interface are set to 0, by default True
    cmd_pars : list, optional
        List of dict with the command line parameters, by default None

    Returns
    -------

    int
        0 if the contactless device was created successfully, 1 if there was an error
    dict
        Updated dictionary with the command line parameters
    str
        Name of the blocking layer file

    '''

    # Load the device parameters and layers from the simulation setup file as an object
    dev_pars,layers = load_device_parameters(session_path, simulation_setup)
    
    for section in dev_pars[simulation_setup]:
        if section[0] == 'Layers':
            # Check if the first and last layer are already the blocking layer, if so, we do not need to add them again
            if (section[1][2] != block_layer_file) ^ (section[-1][2] != block_layer_file):
                print(f'Error:simulation setup file {simulation_setup} is corrupt. The first and last layer must either both be or not be the blocking layer {block_layer_file}. Please check the simulation setup file.')
                return 1, cmd_pars, block_layer_file
            elif (section[1][2] != block_layer_file) and (section[-1][2] != block_layer_file):
                # Update the simulation setup file to add a layer on either side, change the layer indices and update the work functions
                dev_pars, num_layers = update_simulation_setup(session_path, simulation_setup, dev_pars, block_layer_file)

                # Create a new layer file for the blocking layer
                create_block_layer(session_path, dev_pars, layers, block_layer_file, block_layer_mat)
            else:
                # Blocking layers are already present, so we do not need to add them again. Just get the number of layers
                num_layers = len(section)-1

    # Calculate the new work function for the contactless device
    W_F = calc_new_W_F(dev_pars, simulation_setup)

    # Update the nk file of the back electrode to the block_layer_mat file, which is usually Air.txt to prevent reflections
    for section in dev_pars[simulation_setup]:
    # Update layer indices
        if section[0] == 'Optics':
            for line in section[1:]:
                if line[1] == 'nkBE':
                    nkBE_par = line[2]
                    # split the nkBE_par by /nk_ and replace the last part with block_layer_mat file (Uses the default SIMsalabim nk file naming)
                    nkBE_par_split = nkBE_par.split('/nk_')
                    nkBE_par_split[-1] = f'{block_layer_mat}.txt'
                    nkBE_par = nkBE_par_split[0] + '/nk_' + nkBE_par_split[-1]

    # Set the contactless CMD arguments
    contactless_args = [{'par':'W_L','val':f'{W_F:.3f}'},
                        {'par':'W_R','val':f'{W_F:.3f}'},
                        {'par':'L_TCO','val':'0'},
                        {'par':'L_BE','val':'1E-9'},
                        {'par':'nkBE','val':nkBE_par}]
       
    if force_last_interface:
        # Set the interface/surface traps to zero for the last interface
        contactless_args.append({'par':f'l{num_layers-1}.N_t_int','val':'0'})

    # Update the indices of the cmd_pars and add the new command line parameters for the contactless device
    if cmd_pars is not None:
        # Update the command line parameters with the new layer indices, which are now shifted by 1      
        cmd_pars = update_cmd_pars_contactless(cmd_pars)
        cmd_pars.extend(contactless_args)
    else:
        cmd_pars = contactless_args

    return 0, cmd_pars, block_layer_file

def update_logFile(session_path, logFile = 'log.txt'):
    ''' Update the log file to add a line after the line 'Reading in of parameters:' 
    to indicate that a contactless device has been simulated and that the indices of the layers 
    have been shifted by 1 for the set command line parameters.

    Parameters
    ----------
    session_path : str
        Path to the session folder
    logFile : str, optional
        Name of the log file, by default 'log.txt'
    
    Returns
    -------
    int
        0 if the log file was updated successfully, 1 if the log file does not exist

    '''

    # Check if the log file exists
    if os.path.exists(os.path.join(session_path, logFile)):
        # Open the log file and find the line 'Reading in of parameters:'
        with open(os.path.join(session_path, logFile), 'r', encoding='utf-8') as fp:
            lines = fp.readlines()
            fp.close()
        
        for i, line in enumerate(lines):
            if line.strip() == 'Reading in of parameters:':
                # Add a new line after this line with the current date and time
                lines.insert(i, f'\nSimulated a contactless device. Note that the indices of the layers have been shifted by 1 for the set command line parameters. \n')
                break
        
        # Write the updated log file
        with open(os.path.join(session_path, logFile), 'w', encoding='utf-8') as fp:
            fp.writelines(lines)
            fp.close()
        return 0
    else:
        return 1
    
def revert_simulation_setup(dev_pars, session_path, simulation_setup):
    ''' Revert the simulation setup file to its original state by removing the blocking layers and updating 
    the layer indices back to their original values.

    Parameters
    ----------
    dev_pars : dict
        Dictionary with the device parameters
    session_path : str
        Path to the session folder
    simulation_setup : str
        Name of the simulation setup file

    Returns
    -------
    int
        Number of layers in the device after reverting the simulation setup file
    
    '''
    for section in dev_pars[simulation_setup]:
        # Update layer indices
        if section[0] == 'Layers':

            # Get the number of layers in the device
            num_layers = len(section) - 1 # Subtract 1 for the section name

            # Remove the first and last layer, which are the blocking layers
            section.pop(1) # Remove the first blocking layer (first index is only the section name)
            section.pop(-1) # Remove the second blocking layer

            # Update the layer indices of the remaining layers
            for idx in range(1,len(section)):
                # Extract the original layer number from the parameter name, which is in the format lX where X is the layer number and decrease it with 1
                layer_num  = int(section[idx][1].split('l')[1]) - 1 

                # Update the parameter name with the new layer number
                section[idx][1] = 'l' + str(layer_num)

    # Write the updated simulation setup file
    simulation_setup_str = devpar_write_to_txt(dev_pars[simulation_setup])
    with open(os.path.join(session_path, simulation_setup), 'w', encoding='utf-8') as fp:
        fp.write(simulation_setup_str)
        fp.close()

    return num_layers

def format_output_files(session_path, simulation_type, num_layers, JV_file='JV.dat', tJ_file='tJ.dat', Var_file='Var.dat' ):
    ''' Format the output files (JV, tJ, Var) to remove the columns for the blocking layers and update the layer indices 
    back to their original values. In the Var file, the rows for the blocking layers are removed and the x values 
    are shifted to start at 0. Cleaned the leftover interface values for those layers as well

    Parameters
    ----------
    session_path : str
        Path to the session folder
    simulation_type : str
        Type of simulation: 'simss' or 'zimt'
    num_layers : int
        Number of layers in the device after reverting the simulation setup file
    JV_file : str
        Name of the JV file
    tJ_file : str
        Name of the tJ file
    Var_file : str
        Name of the Var file

    Returns
    -------
    None

    '''
    # Init data_JV_tJ as empty dataframe
    data_JV_tJ = pd.DataFrame()

    block_layer_indices = [1, num_layers]

    if simulation_type == 'simss':
        # Check if the JV
        if os.path.exists(os.path.join(session_path, JV_file)):
            data_JV_tJ = pd.read_csv(os.path.join(session_path, JV_file),sep=r'\s+')
    elif simulation_type == 'zimt':
        if os.path.exists(os.path.join(session_path, tJ_file)):
            data_JV_tJ = pd.read_csv(os.path.join(session_path, tJ_file),sep=r'\s+')

    if not data_JV_tJ.empty:
        # Loop over the column headers
        for col in data_JV_tJ.columns:
            if re.search(r'L\d+', col):

                # Get the digits from the column header (Could be one or two depending on the columns)
                digits = re.findall(r'\d+', col)

                # If any of the digits is either the first or last layer, we should remove the column
                if any(int(digit) in block_layer_indices for digit in digits):
                    data_JV_tJ.drop(columns=col, inplace=True)
                else:
                    # If the digit is not equal to the first or last blocking layer index, move the digit down by 1 to restore the original layer indices
                    new_col = col
                    for digit in digits:
                        new_digit = str(int(digit) - 1)
                        new_col = new_col.replace(digit, new_digit)
                    data_JV_tJ.rename(columns={col: new_col}, inplace=True)

        # Save the modified JV or tJ file
        if simulation_type == 'simss':
            data_JV_tJ.to_csv(os.path.join(session_path, JV_file), sep=' ', index=False)
        elif simulation_type == 'zimt':
            data_JV_tJ.to_csv(os.path.join(session_path, tJ_file), sep=' ', index=False)
    else:
        print(f'JV or tJ file does not exist in {session_path}. Skipping formatting of JV or tJ file.')

    # Check if the Var file exists and read it
    if os.path.exists(os.path.join(session_path, Var_file)):
        data_Var = pd.read_csv(os.path.join(session_path, Var_file),sep=r'\s+')

        if simulation_type == 'simss':
            unique_column_name = 'Vext'
        elif simulation_type == 'zimt':
            unique_column_name = 'time'

        val_unique = data_Var[unique_column_name].unique()

        # Drop all rows that have the first or last blocking layer index in the lid column
        rows_to_drop = data_Var[(data_Var['lid'] == block_layer_indices[0]) | (data_Var['lid'] == block_layer_indices[1])].index
        data_Var.drop(rows_to_drop, inplace=True)

        # Shift all values of the column lid down by 1
        data_Var['lid'] = data_Var['lid'] - 1

        # Loop over the unique values and remove the rows that have the first or last blocking layer index in the lid column
        for val in val_unique:

            # Get the subset of the data for the current unique value
            data_Var_val = data_Var[data_Var[unique_column_name] == val]

            # Shift the values in the x column with the first x value to start at 0
            x_min = data_Var_val['x'].min()
            data_Var.loc[data_Var[unique_column_name] == val, 'x'] = data_Var_val['x'] - x_min

            # Fix the last mobility value, which could be changed due to how the interface is handled and stored in the Var file
            indices = data_Var[data_Var[unique_column_name] == val].index
            data_Var.loc[indices[-1], 'mun'] = data_Var.loc[indices[-2], 'mun']
            data_Var.loc[indices[-1], 'mup'] = data_Var.loc[indices[-2], 'mup']

            data_Var.to_csv(os.path.join(session_path, Var_file), sep=' ', index=False, float_format='%.11e')
    else:
        if Var_file != 'none':
            print(f'Var file {Var_file} does not exist in {session_path}. Skipping formatting of Var file.')

    # Save the modified Var file. Write every column in scietific notation with 11 float percisison
    # pd.options.display.float_format = '{:.11e}'.format
    # data_Var.to_csv(os.path.join(session_path, Var_file), sep=' ', index=False, float_format='%.11e')


def process_output_contactless(session_path, simulation_setup, simulation_type, format_output=True, clean_simulation_setup=True, JV_file = 'JV.dat', tJ_file='tJ.dat', Var_file='Var.dat', block_layer_file='Block.txt'):
    ''' Process the output files for a contactless device simulation. The log file is always updated.
     If format_output = True, the simulation setup is reverted to its original state, 
     and the output files are formatted to remove any data related to the blocking layers.

    Parameters
    ----------
    session_path : str
        Path to the session folder
    simulation_setup : str
        Name of the simulation setup file
    simulation_type : str
        Type of simulation: 'simss' or 'zimt'
    format_output : bool
        If True, the simulation setup is reverted to its original state and the output files are formatted
    JV_file : str
        Name of the JV file
    tJ_file : str
        Name of the tJ file
    Var_file : str
        Name of the Var file
    block_layer_file : str
        Name of the blocking layer file

    Returns
    -------
    None
    
    '''
    returncode_logFile = update_logFile(session_path, 'log.txt')

    if returncode_logFile == 1:
        print(f'Warning: could not find log file in {session_path}. Skipping update of log file.')

    if format_output:
        dev_pars,layers = load_device_parameters(session_path, simulation_setup)
        num_layers = len(layers)-1 # Subtract 1 for the simulation setup

        if clean_simulation_setup:
            # Only clean everything when specified by the user. Otherwise issues arise when calling this function multiple times
            # dev_pars,layers = load_device_parameters(session_path, simulation_setup)

            # Revert simulation setup to original state by removing the blocking layers and updating the layer indices
            num_layers = revert_simulation_setup(dev_pars, session_path, simulation_setup)

            # remove the blocking layer file
            if os.path.exists(os.path.join(session_path, block_layer_file)):
                os.remove(os.path.join(session_path, block_layer_file))
            else:
                print(f'Warning: could not find blocking layer file {block_layer_file} in {session_path}. Skipping removal of blocking layer file.')

        # Format the output files to remove any data related to the blocking layers
        format_output_files(session_path, simulation_type, num_layers, JV_file, tJ_file, Var_file)
