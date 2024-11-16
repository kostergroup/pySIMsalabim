"""Functions for general use"""
######### Package Imports #########################################################################

import os, zipfile, subprocess, uuid, shutil, threading, queue
import pandas as pd
from subprocess import run, PIPE
from functools import partial
from threading import Thread
from pySIMsalabim.utils.general import *
from pySIMsalabim.utils.device_parameters import *

######### Function Definitions ####################################################################
def parallel_error_message(errorcode):
    """When a 'standard Pascal' fatal error occurs, add the standard error message to be used with parallel which does not read the 

    Parameters
    ----------
    errorcode : int
        the error code

    Returns
    -------
    str
        the error message

    """
    message = ''
    if errorcode >= 90 and errorcode < 100:
        message = 'Error '+str(errorcode) +': '
        if errorcode == 90:
            message += 'Device parameter file corrupted.'
        elif errorcode == 91:
            message += 'Invalid input. Please check your input files for either incorrect layer definition (see SIMsalabim docs), wrong physics, or voltage in tVG_file too large).'
        elif errorcode == 92:
            message += 'Invalid input from command line.'
        elif errorcode == 93:
            message += 'Numerical failure.'
        elif errorcode == 94:
            message += 'Failed to converge, halt (FailureMode = 0).'
        elif errorcode == 95:
            message += ' Failed to converge at least 1 point, not halt (FailureMode != 0).'
        elif errorcode == 96:
            message += 'Missing input file.'
        elif errorcode == 97:
            message += 'Runtime exceeds limit set by timeout.'
        elif errorcode == 99:
            message += 'Programming error (i.e. not due to the user!).'
    elif errorcode > 100:
        message = 'Fatal error '+str(errorcode) +': '
        if errorcode == 106:
            message += 'Invalid numeric format: Reported when a non-numeric value is read from a text file.'
        elif errorcode == 200:
            message += 'Division by zero: The application attempted to divide a number by zero.'
        elif errorcode == 201:
            message += 'Range check error.'
        elif errorcode == 202:
            message += 'Stack overflow error: This error is only reported when stack checking is enabled.'
        elif errorcode == 205:
            message += 'Floating point overflow.'
        elif errorcode == 206:
            message = 'Floating point underflow.'
        else:
            message = 'Unknown error code '+str(errorcode) + ' occurred.'

    else:
        message = 'Unknown error code '+str(errorcode) + ' occurred.'

    return message

def run_simulation_parallel(sim_type, cmd_pars_list, session_path, max_jobs = max(1,os.cpu_count()-1), verbose=False, **kwargs):
    """Run the SIMsalabim simulation executable with the chosen device parameters.  
    Select the correct function to run the simulation in parallel based on the operating system.

    Parameters
    ----------
    sim_type : string
        Which type of simulation to run: simss or zimt
    cmd_pars_list : List
        List of list with parameters to add to the simss/zimt cmd line. Each parameter is a dict with par,val keys. 
        Note: when relevant the first entry must be the deviceparameters file with a key: dev_par_file
    session_path : string
        File path of the simss or zimt executable 
    max_jobs : int
        Maximum number of parallel jobs to run. Default is the number of CPU cores - 1
    verbose : bool
        If True, print the output of the simulation to the console
    **kwargs : dict
        Additional keyword arguments to pass to the function
    Returns
    -------
    CompletedProcess
        Output object of with returncode and console output of the simulation

    """    
    force_multithreading = kwargs.get('force_multithreading', False)

    if os.name == 'nt':
        # Windows
        result_list = run_simulation_multithreaded_windows(sim_type, cmd_pars_list, session_path, max_jobs, verbose)
    else:
        # Linux
        if shutil.which('parallel') is not None and not force_multithreading:
            result, msg_list, return_code_list  = run_simulation_GNU_parallel(sim_type, cmd_pars_list, session_path, max_jobs, verbose)
            result_list = return_code_list
        else:
            result_list = run_simulation_multithreaded_linux(sim_type, cmd_pars_list, session_path, max_jobs, verbose)

    return result_list

def run_simulation_GNU_parallel(sim_type, cmd_pars_list, session_path, max_jobs = max(1,os.cpu_count()-1),verbose=False):
    """Run the SIMsalabim simulation executable with the chosen device parameters.  
        The simulation is run in parallel using the GNU Parallel program. (https://www.gnu.org/software/parallel/).
        If this command is used please cite:
        Tange, O. (2021, August 22). GNU Parallel 20210822 ('Kabul').
        Zenodo. https://doi.org/10.5281/zenodo.5233953

        To Install GNU Parallel on linux: (not available on Windows)
        sudo apt-get update
        sudo apt-get install parallel
        
        or try to run the install_GNU_parallel_Linux() function from the install module.
        import pySIMsalabim.install as install
        install.install_GNU_parallel_Linux()

        Return the complete result object of the process accompanied by a message with information, 
        in case of both success and failure.

    Parameters
    ----------
    sim_type : string
        Which type of simulation to run: simss or zimt
    cmd_pars_list : List
        List of list with parameters to add to the simss/zimt cmd line. Each parameter is a dict with par,val keys. 
        Note: when relevant the first entry must be the deviceparameters file with a key: dev_par_file
    session_path : string
        File path of the simss or zimt executable 
    max_jobs : int
        Maximum number of parallel jobs to run. Default is the number of CPU cores - 1

    Returns
    -------
    CompletedProcess
        Output object of with returncode and console output of the simulation
    List
        Return list of messages for each simulation
    List
        Return list of return codes for each simulation
    """
    # Construct the command to run the executable
    cmd_line_list = []
    for cmd_pars in cmd_pars_list:
        cmd_line = construct_cmd(sim_type, cmd_pars)
        cmd_line_list.append(cmd_line)
    
    # Construct the file and command to run the GNU parallel
    uuid_str = str(uuid.uuid4())
    filename = 'Str4Parallel_'+uuid_str+'.txt'
    log_file = os.path.join(session_path,'logjob_'+uuid_str+ '.dat')

    with open(os.path.join(session_path,filename),'w') as tempfilepar:
        for cmd_line in cmd_line_list:
            tempfilepar.write(cmd_line+'\n')

    cmd_parallel = 'parallel --joblog '+ log_file +' --jobs '+str(int(max_jobs))+' -a '+os.path.join(session_path,filename)
    
    result = run([cmd_parallel], cwd=session_path,stdout=PIPE, check=False, shell=True)
    msg_list,return_code_list = [],[]

    # if result.returncode != 0:
    log = pd.read_csv(log_file, sep='\t',usecols=['Exitval'],on_bad_lines='skip')

    # check if all jobs have been completed successfully, i.e. all exitvals are 0, 95 or 3
    if not all(val in [0, 95, 3] for val in log['Exitval']):
        for idx, val in enumerate(log['Exitval']):
            message = ''
            if val != 0 and val != 95 and val != 3:
                if val >= 90 :
                    # Show the message as an error on the screen. Do not continue to the simulation results page.
                    msg_list.append('Simulation raised an error with Errorcode: ' + str(val) + '\n\n' + parallel_error_message(val))
                else:
                    msg_list.append(parallel_error_message(val))
            else:
                if val == 95:
                    # In case of errorcode 95, failures during the simulations were encountered but the simulation did not halt. Show 'error' messages on the UI.
                    msg_list.append('Simulation completed but raised errorcode: ' + str(val) + '\n\n' + 'The simulation finished but at least 1 point did not converge.')
                elif val == 3:
                    # Special case, should not occur in the web version.
                    # When the program exits as a success but no simulation has been run, e.g. in the case of the autotidy functionality. 
                    msg_list.append('Action completed')
                else:
                    # Simulation completed as expected.
                    msg_list.append('Simulation completed.')

    return_code_list = log['Exitval'].tolist()  

    # remove the temporary files
    os.remove(os.path.join(session_path,filename))
    os.remove(log_file)

    return result, msg_list, return_code_list

def run_simulation_multithreaded_windows(sim_type,cmd_pars_list,session_path,max_jobs=max(1,os.cpu_count()-1),verbose=False):
    """Runs simulations in parallel on max_jobs number of threads.  
    This procedure should work on Windows and Linux but it is not as efficient as run_parallel_simu on Linux.
    Yet, it is the only way to run simulations in parallel on Windows in a thread safe way and making sure that two thread do not try to write to the same file at the same time.
    This is achieved by running the simulation in a temporary folder with a copy of all the necessary input files and then moving the output files to the original folder.


    Parameters
    ----------
    sim_type : string
        Which type of simulation to run: simss or zimt
    cmd_pars_list : List
        List of list with parameters to add to the simss/zimt cmd line. Each parameter is a dict with par,val keys. 
        Note: when relevant the first entry must be the deviceparameters file with a key: dev_par_file
    session_path : string
        File path of the simss or zimt executable 
    max_jobs : int
        Maximum number of parallel jobs to run. Default is the number of CPU cores - 1
    verbose : bool
        If True, print the output of the simulation to the console
    
    Returns
    -------
    List
        List of CompletedProcess objects with returncode and console output of the simulation

    """    
    
    lock = threading.Lock()    # Create a lock   
    semaphore = threading.Semaphore(max_jobs)  # Create a semaphore

    # Create tmp folder
    rnd_ID = str(uuid.uuid4())
    tmp_folder = os.path.join(session_path, 'tmp'+rnd_ID) # Generate a unique ID for the temporary folder to make sure there are no conflicts with other processes
    if os.path.isdir(tmp_folder):
        shutil.rmtree(tmp_folder)
        os.mkdir(tmp_folder)
    else:
        os.mkdir(tmp_folder)

    tmp_folder_lst = [tmp_folder] * len(cmd_pars_list)

    # Create a queue to communicate with the worker threads
    q = queue.Queue()

    # Start worker threads
    threads = []
    for i in range(len(cmd_pars_list)):
        t = CustomThread(target=partial(worker_windows,q=q,lock=lock,tmp_folder=tmp_folder_lst[i],semaphore=semaphore,verbose=verbose))
        t.start()
        threads.append(t)

    # Add tasks to the queue
    for code_name, cmd_pars, path in zip([sim_type] * len(cmd_pars_list), cmd_pars_list, tmp_folder_lst):
        q.put((code_name, cmd_pars, path, session_path))

    # Wait for all tasks to be finished
    q.join()
    
    # Stop workers
    for i in range(len(cmd_pars_list)):
        q.put(None)
    
    result_list = []
    for t in threads:
        result_list.append(t.join())
     
    # # Clean up
    shutil.rmtree(tmp_folder)

    return result_list

def worker_windows(q,lock,tmp_folder,semaphore,verbose=False):
    """Worker function that runs the simulation in a temporary folder and moves the output files to the original folder. 

    Parameters
    ----------
    q : queue
        Queue to communicate with the main thread
    lock : threading.Lock
        Lock to prevent multiple threads from writing to the same file at the same time
    tmp_folder : string
        Temporary folder to run the simulation in
    semaphore : threading.Semaphore
        Semaphore to limit the number of parallel jobs
    verbose : bool
        If True, print the output of the simulation to the console

    """
    while True:
        # Get task from the queue
        task = q.get()
        if task is None:
            break

        # Unpack task
        sim_type, cmd_pars, path, session_path = task

        device_parameters = None

        for cmd_par in cmd_pars:
            if cmd_par['par'] == 'dev_par_file':
                device_parameters = cmd_par['val']
                break
    
        if device_parameters is None:
            raise ValueError('Device parameters file not found in the command parameters list.')

        # Acquire semaphore
        semaphore.acquire()

        # create a temporary folder for the simulation
        ID = str(uuid.uuid4()) # Generate a unique ID for the temporary folder
        tmp_folder = os.path.join(tmp_folder, ID)
        if not os.path.isdir(tmp_folder):
            os.mkdir(tmp_folder)

        # Copy all necessary files to the temporary folder
        lock.acquire()
        # copy the executable to the temporary folder

        if os.name == 'nt':
            shutil.copy(os.path.join(session_path, sim_type + '.exe'), tmp_folder)
        else:
            shutil.copy(os.path.join(session_path, sim_type), tmp_folder)

        dev_par, layers = load_device_parameters(session_path, device_parameters, run_mode = False)

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


        # move all layers to the temporary folder
        for layer in layers:
            shutil.copy(os.path.join(session_path, layer[2]), tmp_folder)
        
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
        else:
            tVGFile = res[4]
            tJFile = res[7]

        varFile = res[5]
        logFile = res[6]


        # Copy the files to the temporary folder
        for file in layer_files + optical_files + traps_int_files + traps_bulk_files + [ExpJV_file] + [tVGFile]:
            if file is not None and os.path.isfile(file):
                shutil.copy(file, tmp_folder)
            
            # update temp folder files with basename 
            if file in layer_files:
                make_basename_input_files(os.path.join(tmp_folder, os.path.basename(file)))       

        # move files from cmd_pars to the temporary folder and overwrite if necessary
        input_files = get_inputFile_from_cmd_pars(sim_type, cmd_pars)
        input_files = [os.path.abspath(os.path.join(session_path, f['val'])) for f in input_files]
        input_files_basenames = [os.path.basename(f) for f in input_files]
        for file in input_files:
            # if file already in the tmp_folder, remove it and copy the new one
            if os.path.isfile(os.path.join(tmp_folder, os.path.basename(file))):
                os.remove(os.path.join(tmp_folder, os.path.basename(file)))
            shutil.copy(os.path.join(session_path, file), tmp_folder)

        # set basename for device parameters
        make_basename_input_files(os.path.join(tmp_folder, os.path.basename(device_parameters)))


        # check the input files for the new layers
        # for layer in newlayers:
        #     input_files2 = get_inputFile_from_layer(layer,session_path)
        #     for file in input_files2:
        #         # if file does not exist in the tmp_folder, copy it. Otherwise, copy it if it is not in the input_files list
        #         if not os.path.isfile(os.path.join(tmp_folder, os.path.basename(file))):
        #             shutil.copy(os.path.join(session_path, file), tmp_folder)
        #         else:
        #             if not os.path.basename(file) in input_files_basenames:
        #                 shutil.copy(os.path.join(session_path, file), tmp_folder)

        lock.release()

        # Construct the command to run the executable
        cmd_pars = make_basename_file_cmd_pars(cmd_pars)
        cmd_line = construct_cmd(sim_type, cmd_pars)

        # Run the simulation
        result = run(cmd_line, cwd=tmp_folder, stdout=PIPE, check=False, shell=True)

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
        lock.acquire()
        if sim_type.lower() == 'simss':
            if os.path.isfile(os.path.join(tmp_folder, varFile)):
                shutil.move(os.path.join(tmp_folder, varFile), os.path.join(session_path, varFile))
            if os.path.isfile(os.path.join(tmp_folder, logFile)):
                shutil.move(os.path.join(tmp_folder, logFile), os.path.join(session_path, logFile))
            if os.path.isfile(os.path.join(tmp_folder, JVFile)):
                shutil.move(os.path.join(tmp_folder, JVFile), session_path)
            if os.path.isfile(os.path.join(tmp_folder, scParsFile)):
                shutil.move(os.path.join(tmp_folder, scParsFile), os.path.join(session_path, scParsFile))
        elif sim_type.lower() == 'zimt':
            if os.path.isfile(os.path.join(tmp_folder, varFile)):
                shutil.move(os.path.join(tmp_folder, varFile), os.path.join(session_path, varFile))
            if os.path.isfile(os.path.join(tmp_folder, logFile)):
                shutil.move(os.path.join(tmp_folder, logFile), os.path.join(session_path, logFile))
            if os.path.isfile(os.path.join(tmp_folder, tVGFile)):
             shutil.move(os.path.join(tmp_folder, tVGFile), os.path.join(session_path, tVGFile))
            if os.path.isfile(os.path.join(tmp_folder, tJFile)):
                shutil.move(os.path.join(tmp_folder, tJFile), os.path.join(session_path, tJFile))
        lock.release()

        # Release semaphore
        semaphore.release()

        # Print output if verbose
        if verbose:
            print(result.stdout)

        # Notify the queue that the task is done
        q.task_done()
    
    return result, message

def worker_linux(q,lock,semaphore,verbose=False):
    """Worker function that runs the simulation in a temporary folder and moves the output files to the original folder. 

    Parameters
    ----------
    q : queue
        Queue to communicate with the main thread
    lock : threading.Lock
        Lock to prevent multiple threads from writing to the same file at the same time
    semaphore : threading.Semaphore
        Semaphore to limit the number of parallel jobs
    verbose : bool
        If True, print the output of the simulation to the console

    """
    while True:
        # Get task from the queue
        task = q.get()
        if task is None:
            break
        
        # Unpack task
        sim_type, cmd_pars, session_path = task

        # Acquire semaphore
        semaphore.acquire()

        result, message = run_simulation(sim_type, cmd_pars, session_path, run_mode = False, verbose=verbose)

        # Release semaphore
        semaphore.release()

        # Print output if verbose
        if verbose:
            print(result.stdout)

        # Notify the queue that the task is done
        q.task_done()

        return result, message

def run_simulation_multithreaded_linux(sim_type,cmd_pars_list,session_path,max_jobs=max(1,os.cpu_count()-1),verbose=False):
    """Runs simulations in parallel on max_jobs number of threads.  
    This procedure should work on Windows and Linux but it is not as efficient as run_parallel_simu on Linux.
    Yet, it is the only way to run simulations in parallel on Windows in a thread safe way and making sure that two thread do not try to write to the same file at the same time.
    This is achieved by running the simulation in a temporary folder with a copy of all the necessary input files and then moving the output files to the original folder.


    Parameters
    ----------
    sim_type : string
        Which type of simulation to run: simss or zimt
    cmd_pars_list : List
        List of list with parameters to add to the simss/zimt cmd line. Each parameter is a dict with par,val keys. 
        Note: when relevant the first entry must be the deviceparameters file with a key: dev_par_file
    session_path : string
        File path of the simss or zimt executable 
    max_jobs : int
        Maximum number of parallel jobs to run. Default is the number of CPU cores - 1
    verbose : bool
        If True, print the output of the simulation to the console
    
    Returns
    -------
    List
        List of CompletedProcess objects with returncode and console output of the simulation

    """    
 
    lock = threading.Lock()    # Create a lock   
    semaphore = threading.Semaphore(max_jobs)  # Create a semaphore

    # Create a queue to communicate with the worker threads
    q = queue.Queue()

    # Start worker threads
    threads = []
    for i in range(len(cmd_pars_list)):
        t = CustomThread(target=partial(worker_linux,q=q,lock=lock,semaphore=semaphore,verbose=verbose))
        t.start()
        threads.append(t)

    # Add tasks to the queue
    for code_name, cmd_pars in zip([sim_type] * len(cmd_pars_list), cmd_pars_list):
        q.put((code_name, cmd_pars, session_path))

    # Wait for all tasks to be finished
    q.join()

    # Stop workers
    for i in range(len(cmd_pars_list)):
        q.put(None)

    result_list = []
    for t in threads:
        result_list.append(t.join())
    
    return result_list

# Custom thread class to return the result of the thread
class CustomThread(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
 
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
             
    def join(self, *args):
        Thread.join(self, *args)
        return self._return












