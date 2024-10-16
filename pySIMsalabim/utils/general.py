"""Functions for general use"""
######### Package Imports #########################################################################

import os, subprocess, uuid, shutil, time
import pandas as pd
from subprocess import run, PIPE
from pySIMsalabim.utils.device_parameters import *

######### Function Definitions ####################################################################

def fatal_error_message(errorcode):
    """When a 'standard Pascal' fatal error occurs, add the standard error message

    Parameters
    ----------
    errorcode : int
        the error code
    """
    message = ''
    if errorcode == 106:
        message = 'Invalid numeric format: Reported when a non-numeric value is read from a text file'
    elif errorcode == 200:
        message = 'Division by zero: The application attempted to divide a number by zero.'
    elif errorcode == 201:
        message = 'Range check error.'
    elif errorcode == 202:
        message = 'Stack overflow error: This error is only reported when stack checking is enabled.'
    elif errorcode == 205:
        message = 'Floating point overflow.'
    elif errorcode == 206:
        message = 'Floating point underflow.'
    else:
        message = 'A fatal error occured.'
    return message

# def parallel_error_message(errorcode):
#     """When a 'standard Pascal' fatal error occurs, add the standard error message to be used with parallel which does not read the 

#     Parameters
#     ----------
#     errorcode : int
#         the error code

#     Returns
#     -------
#     str
#         the error message

#     """
#     message = ''
#     if errorcode >= 90 and errorcode < 100:
#         message = 'Error '+str(errorcode) +': '
#         if errorcode == 90:
#             message += 'Device parameter file corrupted.'
#         elif errorcode == 91:
#             message += 'Invalid input. Please check your input files for either incorrect layer definition (see SIMsalabim docs), wrong physics, or voltage in tVG_file too large).'
#         elif errorcode == 92:
#             message += 'Invalid input from command line.'
#         elif errorcode == 93:
#             message += 'Numerical failure.'
#         elif errorcode == 94:
#             message += 'Failed to converge, halt (FailureMode = 0).'
#         elif errorcode == 95:
#             message += ' Failed to converge at least 1 point, not halt (FailureMode != 0).'
#         elif errorcode == 96:
#             message += 'Missing input file.'
#         elif errorcode == 97:
#             message += 'Runtime exceeds limit set by timeout.'
#         elif errorcode == 99:
#             message += 'Programming error (i.e. not due to the user!).'
#     elif errorcode > 100:
#         message = 'Fatal error '+str(errorcode) +': '
#         if errorcode == 106:
#             message += 'Invalid numeric format: Reported when a non-numeric value is read from a text file.'
#         elif errorcode == 200:
#             message += 'Division by zero: The application attempted to divide a number by zero.'
#         elif errorcode == 201:
#             message += 'Range check error.'
#         elif errorcode == 202:
#             message += 'Stack overflow error: This error is only reported when stack checking is enabled.'
#         elif errorcode == 205:
#             message += 'Floating point overflow.'
#         elif errorcode == 206:
#             message = 'Floating point underflow.'
#         else:
#             message = 'Unknown error code '+str(errorcode) + ' occurred.'

#     else:
#         message = 'Unknown error code '+str(errorcode) + ' occurred.'

#     return message

def construct_cmd(sim_type, cmd_pars):
    """Construct a single string to use as command to run a SIMsalabim executable

    Parameters
    ----------
    sim_type : string
        Which program to run: simss or zimt
    cmd_pars : List
        List with parameters to add to the simss/zimt cmd line. Each parameter is a dict with par,val keys. 
        Note: when relevant the first entry must be the deviceparameters file with a key: dev_par_file

    Returns
    -------
    string
        Constructed string to run as cmd
    """
    # Start with the executable name
    cmd_line = './' + sim_type

    # if system is 'Windows' use the .exe extension
    if os.name == 'nt':
        cmd_line = sim_type + '.exe'
    

    # Check whether a device parameters file has been defined
    for i in cmd_pars:
        # When specified, the device parameter file must be placed first, as is required by SIMsalabim
        if i['par'] == 'dev_par_file':
            args_single = ' ''' + i['val']+ ' '''
            cmd_line = cmd_line + args_single
            # After the dev_par_file key had been found once, stop the loop. If more than one dev_par_file is specified, the rest are ignored.
            break

    # Add the parameters
    for i in cmd_pars:
        if i['par'] != 'dev_par_file':
            # Add each parameter as " -par_name par_value"
            args_single = ' -' +i['par'] + ' ' + i['val']
            cmd_line = cmd_line + args_single
    
    return cmd_line

def run_simulation(sim_type, cmd_pars, session_path, run_mode = False, verbose = False):
    """Run the SIMsalabim simulation executable with the chosen device parameters. 
        Return the complete result object of the process accompanied by a message with information, 
        in case of both success and failure.

    Parameters
    ----------
    sim_type : string
        Which type of simulation to run: simss or zimt
    cmd_pars : List
        List with parameters to add to the simss/zimt cmd line. Each parameter is a dict with par,val keys. 
        Note: when relevant the first entry must be the deviceparameters file with a key: dev_par_file
    session_path : string
        File path of the simss or zimt executable 
    run_mode : boolean
        True if function is called as part of The Shell, False when called directly. 
        Prevents using streamlit components outside of The Shell.
    verbose : boolean
        True if the console output of the simulation should be printed to the console

    Returns
    -------
    CompletedProcess
        Output object of with returncode and console output of the simulation
    string
        Return message to display on the UI, for both success and failed
    """
    # Construct the command to run the executable
    cmd_line = construct_cmd(sim_type, cmd_pars)
    
    if run_mode:
        # Run the simulation in a shell environment 
        if os.name == 'nt':
            result = run(cmd_line, cwd=session_path,stdout=PIPE, check=False, shell=True)
        else:
            result = run([cmd_line], cwd=session_path, stdout=PIPE, check=False, shell=True)
    
        # Check the results of the process using the returncodes and console output
        if result.returncode != 0 and result.returncode != 95 and result.returncode != 3:
            # SIMsalabim raised an error, stop the program and return the error message on the UI.
            startMessage = False
            message = ''
            result_decode = result.stdout.decode('utf-8')

            if result.returncode >= 100:
                # A fatal (numerical) error occurred. Return errorcode and a standard error message.
                message = fatal_error_message(result.returncode)
            else:
                # Simsalabim raised an error. Read the console output for the details / error messaging. 
                # All linetypes after 'Program will be terminated, press enter.' are considered part of the error message
                for line_console in result_decode.split('\n'):
                    if startMessage is True:
                        # The actual error message. Since the error message can be multi-line, append each line.
                        message = message + line_console + '\n'
                    if 'Program will be terminated.' in line_console:
                        # Last 'regular' line of the console output. The next line is from the error message.
                        startMessage = True

            # Show the message as an error on the screen. Do not continue to the simulation results page.
            message = 'Simulation raised an error with Errorcode: ' + str(result.returncode) + '\n\n' + message
        else:
            # SIMsalabim simulation succeeded
            if result.returncode == 95:
                # In case of errorcode 95, failures during the simulations were encountered but the simulation did not halt. Show 'error' messages on the UI.
                startMessage = False
                message = ''
                result_decode = result.stdout.decode('utf-8')
                for line_console in result_decode.split('\n'):
                    if startMessage is True:
                        # The actual error message. Since the error message can be multi-line, append each line.
                        message = message + line_console + '\n'
                    if 'Program will be terminated.' in line_console:
                        # Last 'regular' line of the console output. The next line is from the error message.
                        startMessage = True

                # Show the message as a success on the screen
                message = 'Simulation completed but raised errorcode: ' + str(result.returncode) + '\n\n' + 'The simulation finished but at least 1 point did not converge. \n\n' + message
            elif result.returncode == 3:
                # Special case, should not occur in the web version.
                # When the program exits as a success but no simulation has been run, e.g. in the case of the autotidy functionality. 
                message = 'Action completed'
            else:
                # Simulation completed as expected.
                message = 'Simulation complete. Output can be found in the Simulation results.'
    else:
        # if verbose:
        if os.name == 'nt':
            result = run(cmd_line, cwd=session_path,stdout=PIPE, check=False, shell=True)
        else:
            result = run([cmd_line], cwd=session_path, stdout=PIPE, check=False, shell=True)

        message = ''
 
    return result, message


def run_simulation_filesafe(sim_type, cmd_pars, session_path, run_mode = False, verbose = False):
    """Run the SIMsalabim simulation executable with the chosen device parameters. 
        Return the complete result object of the process accompanied by a message with information, 
        in case of both success and failure.

    Parameters
    ----------
    sim_type : string
        Which type of simulation to run: simss or zimt
    cmd_pars : List
        List with parameters to add to the simss/zimt cmd line. Each parameter is a dict with par,val keys. 
        Note: when relevant the first entry must be the deviceparameters file with a key: dev_par_file
    session_path : string
        File path of the simss or zimt executable 
    run_mode : boolean
        True if function is called as part of The Shell, False when called directly. 
        Prevents using streamlit components outside of The Shell.
    verbose : boolean
        True if the console output of the simulation should be printed to the console

    Returns
    -------
    CompletedProcess
        Output object of with returncode and console output of the simulation
    string
        Return message to display on the UI, for both success and failed
    """
    # Create a temp folder to store the simulation results
    ID = str(uuid.uuid4())
    tmp_folder = os.path.join(session_path, 'tmp_'+ID)
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)

    # get file setup from cmd_pars
    device_parameters = None

    for cmd_par in cmd_pars:
        if cmd_par['par'] == 'dev_par_file':
            device_parameters = cmd_par['val']
            break

    if device_parameters is None:
        raise ValueError('Device parameters file not found in the command parameters list.')

    # Copy the device parameters file to the temp folder
    make_thread_safe_file_copy(os.path.join(session_path, device_parameters), tmp_folder)

    # copy the executable to the temp folder
    if os.name == 'nt':
        shutil.copy(os.path.join(session_path, sim_type+'.exe'), tmp_folder)
    else:
        shutil.copy(os.path.join(session_path, sim_type), tmp_folder)

    device_parameters = os.path.basename(device_parameters)
    
    while True:
        # copy the file to the temp folder
        try:
            dev_par, layers = load_device_parameters(session_path, device_parameters, run_mode = False)
            break
        except:
            pass 
        time.sleep(0.002)

    # check for new layers in the cmd_pars
    newlayers = []
    idx_layers = []
    for cmd_par in cmd_pars:
        if cmd_par['par'].startswith('l') and cmd_par['par'][1:].isdigit():
            newlayers.append(cmd_par)
            idx_layers.append(int(cmd_par['par'][1:]))
    
    # update layer files with cmd_pars
    if len(newlayers) > 0:
        for layer in layers:
            for cmd_par in cmd_pars:
                if cmd_par['par'] == layer[1]:
                    layer[2] = cmd_par['val']
                    break
    
    # check if we need to add new layers
    newlayers = [x for _, x in sorted(zip(idx_layers, newlayers))]
    idx_layers = sorted(idx_layers)
    if len(idx_layers) > 0:
        if max(idx_layers) > len(layers)-1: # means we need to add new layers
            # check that all the layers between len(layers)-& and max(idx_layers) are in the idx_layers list
            for i in range(len(layers),max(idx_layers)+1):
                if i not in idx_layers:
                    raise ValueError('Missing layer definition for layer '+str(i)+' in the command parameters list.')
            # add the new layers
            for i, layer in zip(idx_layers, newlayers):
                layers.append(['par','l'+str(i),layer['val']],'parameter file for layer '+str(i))
        
            # update dev_par layer files with cmd_pars
            dev_par_keys = list(dev_par.keys())
            for i, section in enumerate(dev_par[dev_par_keys[0]]):
                if section[0].lower() == 'layers':
                    # update section with layers[1:]
                    dev_par[dev_par_keys[0]][i][1:] = layers[1:]   


    # move all layer files to the temp folder
    for layer in layers:
        make_thread_safe_file_copy(os.path.join(session_path, layer[2]), tmp_folder)

    res = store_file_names(dev_par, sim_type, device_parameters, layers, run_mode = False)
    layer_files = res[0]
    optical_files = res[1]
    # make absolute paths
    layer_files = [os.path.abspath(os.path.join(session_path, f)) for f in layer_files]
    optical_files = [os.path.abspath(os.path.join(session_path, f)) for f in optical_files]
    optical_file_basenames = [os.path.basename(f) for f in optical_files]   
    traps_int_files = res[2]
    traps_bulk_files = res[3]
    traps_int_files = [os.path.abspath(os.path.join(session_path, f)) for f in traps_int_files]
    traps_bulk_files = [os.path.abspath(os.path.join(session_path, f)) for f in traps_bulk_files]
    traps_int_file_basenames = [os.path.basename(f) for f in traps_int_files]
    traps_bulk_file_basenames = [os.path.basename(f) for f in traps_bulk_files]

    ExpJV_file = None
    tVGFile = None
    tJFile = None
    JVFile = None
    scParsFile = None
    if sim_type == 'simss':
        if res[4].lower() == 'None'.lower():
            ExpJV_file = None
        else:
            ExpJV_file = res[4]
        JVFile = res[7]
        scParsFile = res[8]
    elif sim_type == 'zimt':
        tVGFile = res[4]
        tJFile = res[7]
    else :
        raise ValueError('Simulation type not recognized.')

    varFile = res[5]
    logFile = res[6] 
    
    # Copy the files to the temporary folder
    for file in layer_files + optical_files + traps_int_files + traps_bulk_files + [ExpJV_file] + [tVGFile]:
        if file is not None and os.path.isfile(file):
            make_thread_safe_file_copy(file, tmp_folder)
        
        # update temp folder files with basename 
        if file in layer_files:
            make_basename_input_files(os.path.join(tmp_folder, os.path.basename(file)))       
    
    input_files = get_inputFile_from_cmd_pars(sim_type, cmd_pars)
    
    input_files = [os.path.abspath(os.path.join(session_path, f['val'])) for f in input_files]
    input_files_basenames = [os.path.basename(f) for f in input_files]
    
    for file in input_files:
        # print(file)
        # if file already in the tmp_folder, remove it and copy the new one
        while True:
            try:
                if os.path.isfile(os.path.join(tmp_folder, os.path.basename(file))):
                    os.remove(os.path.join(tmp_folder, os.path.basename(file)))
                break
            except:
                pass
            # sleep random time to prevent high CPU usage smaller than 5ms
            time.sleep(random.uniform(0.002,0.005))
            
        # if os.path.isfile(os.path.join(tmp_folder, os.path.basename(file))):
        #     os.remove(os.path.join(tmp_folder, os.path.basename(file)))
        make_thread_safe_file_copy(os.path.join(session_path, file), tmp_folder)
    
    # set basename for device parameters
    make_basename_input_files(os.path.join(tmp_folder, os.path.basename(device_parameters)))

    # Construct the command to run the executable
    cmd_pars = make_basename_file_cmd_pars(cmd_pars)
    cmd_line = construct_cmd(sim_type, cmd_pars)

    # Run the simulation
    if os.name == 'nt':
        result = run(cmd_line, cwd=tmp_folder, stdout=PIPE, check=False, shell=True)
    else:
        result = run([cmd_line], cwd=tmp_folder, stdout=PIPE, check=False, shell=True)
    
    # Check the results of the process using the returncodes and console output
    if result.returncode != 0 and result.returncode != 95 and result.returncode != 3:
        # SIMsalabim raised an error, stop the program and return the error message on the UI.
        startMessage = False
        message = ''
        result_decode = result.stdout.decode('utf-8')

        if result.returncode >= 100:
            # A fatal (numerical) error occurred. Return errorcode and a standard error message.
            message = fatal_error_message(result.returncode)
        else:
            # Simsalabim raised an error. Read the console output for the details / error messaging. 
            # All linetypes after 'Program will be terminated, press enter.' are considered part of the error message
            for line_console in result_decode.split('\n'):
                if startMessage is True:
                    # The actual error message. Since the error message can be multi-line, append each line.
                    message = message + line_console + '\n'
                if 'Program will be terminated.' in line_console:
                    # Last 'regular' line of the console output. The next line is from the error message.
                    startMessage = True

        # Show the message as an error on the screen. Do not continue to the simulation results page.
        message = 'Simulation raised an error with Errorcode: ' + str(result.returncode) + '\n\n' + message
    else:
        # SIMsalabim simulation succeeded
        if result.returncode == 95:
            # In case of errorcode 95, failures during the simulations were encountered but the simulation did not halt. Show 'error' messages on the UI.
            startMessage = False
            message = ''
            result_decode = result.stdout.decode('utf-8')
            for line_console in result_decode.split('\n'):
                if startMessage is True:
                    # The actual error message. Since the error message can be multi-line, append each line.
                    message = message + line_console + '\n'
                if 'Program will be terminated.' in line_console:
                    # Last 'regular' line of the console output. The next line is from the error message.
                    startMessage = True

            # Show the message as a success on the screen
            message = 'Simulation completed but raised errorcode: ' + str(result.returncode) + '\n\n' + 'The simulation finished but at least 1 point did not converge. \n\n' + message
        elif result.returncode == 3:
            # Special case, should not occur in the web version.
            # When the program exits as a success but no simulation has been run, e.g. in the case of the autotidy functionality. 
            message = 'Action completed'
        else:
            # Simulation completed as expected.
            message = 'Simulation complete. Output can be found in the Simulation results.'

    # Move output files to the original folder
    if sim_type.lower() == 'simss':
        if os.path.isfile(os.path.join(tmp_folder, varFile)):
            # shutil.move(os.path.join(tmp_folder, varFile), os.path.join(session_path, varFile))
            make_thread_safe_file_copy(os.path.join(tmp_folder, varFile), session_path)
        if os.path.isfile(os.path.join(tmp_folder, logFile)):
            # shutil.move(os.path.join(tmp_folder, logFile), os.path.join(session_path, logFile))
            make_thread_safe_file_copy(os.path.join(tmp_folder, logFile), session_path)
        if os.path.isfile(os.path.join(tmp_folder, JVFile)):
            # shutil.move(os.path.join(tmp_folder, JVFile), session_path)
            make_thread_safe_file_copy(os.path.join(tmp_folder, JVFile), session_path)
        if os.path.isfile(os.path.join(tmp_folder, scParsFile)):
            # shutil.move(os.path.join(tmp_folder, scParsFile), os.path.join(session_path, scParsFile))
            make_thread_safe_file_copy(os.path.join(tmp_folder, scParsFile), session_path)
    elif sim_type.lower() == 'zimt':
        if os.path.isfile(os.path.join(tmp_folder, varFile)):
            # shutil.move(os.path.join(tmp_folder, varFile), os.path.join(session_path, varFile))
            make_thread_safe_file_copy(os.path.join(tmp_folder, varFile), session_path)
        if os.path.isfile(os.path.join(tmp_folder, logFile)):
            # shutil.move(os.path.join(tmp_folder, logFile), os.path.join(session_path, logFile))
            make_thread_safe_file_copy(os.path.join(tmp_folder, logFile), session_path)
        if os.path.isfile(os.path.join(tmp_folder, tVGFile)):
            # shutil.move(os.path.join(tmp_folder, tVGFile), os.path.join(session_path, tVGFile))
            make_thread_safe_file_copy(os.path.join(tmp_folder, tVGFile), session_path)
        if os.path.isfile(os.path.join(tmp_folder, tJFile)):
            # shutil.move(os.path.join(tmp_folder, tJFile), os.path.join(session_path, tJFile))
            make_thread_safe_file_copy(os.path.join(tmp_folder, tJFile), session_path)

    return result, message


    
def make_thread_safe_file_copy(file, destination):
    """Copy a file to a temp folder, and wait until the file is not in use anymore.

    Parameters
    ----------
    file : string
        File path of the file to copy
    destination : string
        File path of the destination folder
    """
    
    # check temp folder exists if not create it
    if not os.path.exists(destination):
        os.makedirs(destination)

    # tries to open the file, if it is in use it will wait until it is not
    while True:
        
        # copy the file to the temp folder
        try:
            shutil.copy(file, destination)
            break
        except:
            pass
        
        # add 2ms delay to prevent high CPU usage
        time.sleep(0.002)
