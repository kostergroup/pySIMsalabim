"""Perform steady-state JV simulations"""

######### Package Imports #########################################################################

import os, uuid, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import constants
# import pySIMsalabim
## Import pySIMsalabim, if not successful, add the parent directory to the system path
try :
    import pySIMsalabim as sim
except ImportError:
    # Add the parent directory to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import pySIMsalabim as sim
from pySIMsalabim.utils import general as utils_gen
from pySIMsalabim.utils.parallel_sim import *
from pySIMsalabim.utils.utils import update_cmd_pars

######### Functions #################################################################################

def run_SS_JV(simss_device_parameters, session_path, JV_file_name = 'JV.dat', varFile = 'none', G_fracs = [], parallel = False, max_jobs = max(1,os.cpu_count()-1), run_mode = True, **kwargs):
    """

    Parameters
    ----------
    simss_device_parameters : string
        Name of the device parameters file.
    session_path : string
        Path to the session folder where the simulation will run.
    JV_file_name : string
        Name of the JV file.
    parallel : bool, optional
        Run the simulations in parallel, by default False
    max_jobs : int, optional
        Maximum number of parallel jobs, by default max(1,os.cpu_count()-1)
    cmd_pars : _type_, optional
        _description_, by default None
    UUID : str, optional
        _description_, by default ''
    run_mode : bool, optional
        indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default True
    **kwargs : dict
        Additional arguments to be passed to the function.

    Returns
    -------
    int
        Exitcode of the simulation.
    str
        Message from the simulation.

    """

    UUID = kwargs.get('UUID', '') # Check if the user wants to add a UUID to the JV file name
    cmd_pars = kwargs.get('cmd_pars', None) # Check if the user wants to add additional command line parameters to the 
    force_multithreading = kwargs.get('force_multithreading', False) # Check if the user wants to force multithreading instead of using GNU parallel
    cmd_pars = kwargs.get('cmd_pars', None) # Check if the user wants to add additional command line parameters
    # Check if the user wants to force the use of thread safe mode, necessary for Windows with parallel simulations
    if os.name == 'nt':  
        threadsafe = kwargs.get('threadsafe', True) # Check if the user wants to force the use of threads instead of processes
    else:
        threadsafe = kwargs.get('threadsafe', False) # Check if the user wants to force the use of threads instead of processes

    turnoff_autoTidy = kwargs.get('turnoff_autoTidy', None) # Check if the user wants to turn off the autoTidy function in SIMsalabim
    if turnoff_autoTidy is None: 
        if not threadsafe:
            turnoff_autoTidy = True
        else:
            turnoff_autoTidy = False

    # Update the JV file name with the UUID
    if UUID != '':
        dum_str = f'_{UUID}'
    else:
        dum_str = ''
    
    # Define the command to be executed
    if G_fracs is None:
        # Update the filenames with the UUID
        JV_file_name = os.path.join(session_path,JV_file_name)
        logFile = os.path.join(session_path,'log.txt')
        scParsFile = os.path.join(session_path,'scPars.txt')
        if UUID != '':
            JV_file_name_base, JV_file_name_ext = os.path.splitext(JV_file_name)
            JV_file_name = JV_file_name_base + dum_str + JV_file_name_ext
            logFile = os.path.join(session_path,'log'+dum_str+'.txt')
            scParsFile = os.path.join(session_path,'scPars'+dum_str+'.txt')
        if varFile != 'none':
            var_file_base, var_file_ext = os.path.splitext(varFile)
            varFile = var_file_base + dum_str + var_file_ext
            varFile = os.path.join(session_path,varFile)


        
        # Specify the arguments to be attached to the cmd
        SS_JV_args = [{'par':'dev_par_file','val':simss_device_parameters},
                        {'par':'JVFile','val':JV_file_name},
                        {'par':'logFile','val':logFile},
                        {'par':'scParsFile','val':scParsFile}
                        ]
        
        if turnoff_autoTidy:
            SS_JV_args.append({'par':'autoTidy','val':'0'})

        if varFile != 'none':
            SS_JV_args.append({'par':'varFile','val':varFile})

        # Update the cmd_pars with the SS_JV_args
        if cmd_pars is not None:
            SS_JV_args = update_cmd_pars(SS_JV_args, cmd_pars)

        result, message = utils_gen.run_simulation('simss',SS_JV_args,session_path,run_mode = run_mode)

        return result, message

    else:
        # Update the filenames with the UUID
        JV_file_name = os.path.join(session_path,JV_file_name)
        JV_file_name_base, JV_file_name_ext = os.path.splitext(JV_file_name)
        if varFile != 'none':
            var_file_base, var_file_ext = os.path.splitext(varFile)
            varFile = var_file_base + dum_str + var_file_ext
            varFile = os.path.join(session_path,varFile)

        # SS_JV_args = [{'par':'dev_par_file','val':simss_device_parameters}]
        SS_JV_args_list = []
        for G_frac in G_fracs:
            dum_args = [{'par':'dev_par_file','val':simss_device_parameters},
            {'par':'G_frac','val':str(G_frac)},
                                    {'par':'JVFile','val':JV_file_name_base + f'_Gfrac_{G_frac}' + dum_str + JV_file_name_ext},
                                    {'par':'logFile','val':os.path.join(session_path,'log'+f'_Gfrac_{G_frac}'+dum_str+'.txt')},
                                    {'par':'scParsFile','val':os.path.join(session_path,'scPars'+f'_Gfrac_{G_frac}'+dum_str+'.txt')},
                                    {'par':'varFile','val':os.path.join(session_path,var_file_base + f'_Gfrac_{G_frac}' + dum_str +var_file_ext)} if varFile != 'none' else {'par':'varFile','val':'none'}
                                    ]
            
            if turnoff_autoTidy:
                dum_args.append({'par':'autoTidy','val':'0'})
                
            if cmd_pars is not None:
                dum_args = update_cmd_pars(dum_args, cmd_pars)

            SS_JV_args_list.append(dum_args)                             
                                       
        if parallel and len(G_fracs) > 1:
            results = run_simulation_parallel('simss', SS_JV_args_list, session_path, max_jobs, force_multithreading=force_multithreading)
            msg_list = ['' for i in range(len(results))]
        else:
            results, msg_list = [], []
            for dum_args in SS_JV_args_list:

                if threadsafe:
                    result, message = utils_gen.run_simulation_filesafe('simss', dum_args, session_path, run_mode)
                else:
                    result, message = utils_gen.run_simulation('simss', dum_args, session_path, run_mode)
                
                results.append(result.returncode)
                msg_list.append(message)
        
        if all([res == 0 for res in results]):
            return 0, 'All JV simulations completed successfully'
        else:
            return results, msg_list    
    
## Running the function as a standalone script
if __name__ == "__main__":
    ## Manual Steady State input parameters. These are overwritten by command line arguments if provided
    # G_fracs = [0.9, 1.0]
    G_fracs = None

    # Define folder and file paths
    session_path = os.path.join('../../','SIMsalabim','SimSS')

    simss_device_parameters = 'simulation_setup.txt'

    JV_name = 'JV.dat'
    Var_name = 'Var.dat'

    # UUID = str(uuid.uuid4()) # Add a UUID to the simulation
    UUID = ''

    # Not user input
    parallel = False
    run_mode = False # If False, show verbose output in console

    ############## Command line arguments  ##############
    ## Notes
    ## - The command line arguments are optional and can be provided in any order
    ## - Each command line argument must be provided in the format -par_name value
    ## - Possible arguments include all SIMsalabim parameters and Steady State JV specific parameters as listed before
    ## - Special arguments
    ##   - G_fracs : string
    ##     - The G fractions to simulate, separated by a comma
    ##   - sp : string
    ##     - The session path, i.e. the working directory for the simulation
    ##   - simsetup : string
    ##     - The name of the simss simulation setup parameters file
    ##   - UUID : string
    ##     - An UUID to add to the simulation (output)

    cmd_pars_dict = {}
    cmd_pars = []

    # Check if any arguments are provided.
    if len(sys.argv) >= 2:
        # Each arguments should be in the format -par val, i.e. in pairs of two. Skip the first argument as this is the script name
        if not len(sys.argv[1:]) % 2 == 0:
            print('Error in command line parameters. Please provide arguments in the format -par_name value -par_name value ...')
            sys.exit(1)
        else:
            input_list = sys.argv[1:]
            # Loop over the input list and put pairs into a dictionary with the first argument as key and the second argument as value
            for i in range(0,len(input_list),2):
                # Check if the key already exists, if not, add it to the cmd_pars_dict
                if str(input_list[i][1:]) in cmd_pars_dict:
                    print(f'Duplicate parameter found in the command line parameters: {str(input_list[i][1:])}')
                    sys.exit(1)
                else:
                    cmd_pars_dict[str(input_list[i][1:])] = str(input_list[i+1])

    # Check and process specific keys/arguments that are not native SIMsalabim arguments
    # Handle the session_path/sp argument separately, as the other parameters depend on this
    if 'sp' in cmd_pars_dict:
        session_path = cmd_pars_dict['sp']
        # remove from cmd_pars
        cmd_pars_dict.pop('sp')

    # Define mappings for keys and variables
    key_action_map = {
        'simsetup': lambda val: {'zimt_device_parameters': val},
        'G_fracs': lambda val: {'G_fracs': val.split(',')}, # IMPORTANT: if multiple Gfracs are provided, they must be separated by a comma!!
        'JV_name': lambda val: {'JV_name': val},
        'Var_name': lambda val: {'Var_name': val},
        'UUID': lambda val: {'UUID': val},
    }

    for key in list(cmd_pars_dict.keys()):  # Use list to avoid modifying the dictionary while iterating
        if key in key_action_map:
            # Apply the corresponding action
            result = key_action_map[key](cmd_pars_dict[key])
            globals().update(result)  # Dynamically update global variables
            cmd_pars_dict.pop(key)

    # Handle remaining keys in `cmd_pars_dict` and add them to the cmd_pars list
    cmd_pars.extend({'par': key, 'val': value} for key, value in cmd_pars_dict.items())

    # Run the function
    results, message = run_SS_JV(simss_device_parameters, session_path, JV_name, Var_name, G_fracs, parallel = parallel, run_mode = run_mode, cmd_pars=cmd_pars, UUID=UUID)

    # Print the results if simulation failed
    if run_mode:
        if G_fracs == None:
            print(message)
        else:
            if results != 0:
                for i, msg in enumerate(message):
                    print(f'G_frac: {G_fracs[i]} - {msg}')