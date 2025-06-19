"""Functions for processing the device parameters"""
######### Package Imports #########################################################################

import os, shutil, random

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
