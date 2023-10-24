#############################################################################################
############################# Functions to run simulation code ##############################
#############################################################################################

# Description:
# ------------
# This file contains the functions to run the simulation code from SIMsalabim (i.e. SimSS and ZimT)

######### Package Imports ###################################################################

import subprocess,shutil,os,parmap,sys,platform,itertools,uuid,multiprocessing,warnings,threading,queue,random,time
import pandas as pd
from functools import partial

# Import pySIMsalabim functions
from pySIMsalabim.compile_simsalabim import fpc_prog
from pySIMsalabim.device_parameters import *

######### Function Definitions ##############################################################

def SIMsalabim_error_message(errorcode):
    """When a 'standard Pascal' fatal error occurs, add the standard error message

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
            message += 'Invalid input (physics, or voltage in tVG_file too large).'
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
            message += 'Unknown error'

    else:
        message = 'Unknown error code '+str(errorcode)

    return message

def run_code(name_prog,path2prog,str2run='',show_term_output=False,verbose=False,ignore_error_code=False):
    """Run program 'name_prog' in the folder specified by 'path2prog'.

    Parameters
    ----------
    name_prog : str
        name of the program to run.
    
    path2prog : str
        path to the folder containing  the simulation program.
        (for example './zimt' in Linux and 'zimt.exe' in Windows ).

    st2run : str
        String to run for the name_prog.
    
    show_term_output : bool, optional
        If True, show the terminal output of the program, by default False.
    
    verbose : bool, optional
        Verbose?, by default False.
    
    ignore_error_code : bool, optional
        Ignore all error codes from SIMsalabim, this can lead to imcomplete or wrong data, by default False
    
    Returns
    -------
    
    """
    
    System = platform.system()                  # Operating system
    is_windows = (System == 'Windows')          # Check if we are on Windows
    path2prog = str(path2prog)                  # Convert to string
    curr_dir = os.getcwd()                      # Get current directory
    os.chdir(path2prog)                         # Change directory to working directory

    if show_term_output == True:
        output_direct = None
    else:
        output_direct = subprocess.DEVNULL
    
    if is_windows:
        cmd_list = name_prog.lower()+'.exe ' + str2run
        if not os.path.isfile(path2prog+'\\'+name_prog.lower()+'.exe'):
            fpc_prog(name_prog,path2prog,show_term_output=False,force_fpc=False,verbose=verbose)
    else : 
        # cmd_list = './'+name_prog+' ' + str2run
        curr_dir = os.getcwd()                      # Get current directory
        os.chdir(path2prog)                         # Change directory to working directory
        cmd_list = './'+name_prog.lower()+' ' + str2run
        
        if not os.path.isfile('./'+name_prog.lower()):
            print('Compiling '+name_prog+' in '+path2prog)
            fpc_prog(name_prog,path2prog,show_term_output=False,force_fpc=False,verbose=verbose)
        os.chdir(curr_dir)                          # Change directory back to original directory

    try:
        subprocess.check_call(cmd_list.split(), encoding='utf8', stdout=output_direct, cwd=path2prog, shell=is_windows)
    except subprocess.CalledProcessError as e:
        #don't stop if error code is 95
        if e.returncode == 95 or e.returncode == 97:
            # error coed 95 is a warning that at least one point did not converge
            if verbose:
                if e.returncode == 95:
                    print("Error code 95")
                elif e.returncode == 97:
                    print("Error code 97 Try to increase the timeout setting in device_parameters.txt")

        else:
            if ignore_error_code:
                warnings.warn('Error code '+str(e.returncode)+' found in log file, ignoring error code')
                warnings.warn(SIMsalabim_error_message(e.returncode)+ 'but it is ignored and the simulation continues')
                pass
            else:
                print(SIMsalabim_error_message(e.returncode))
                raise e
        # print(path2prog)
        # raise ChildProcessError
        
    os.chdir(curr_dir)                          # Change directory back to original directory




def run_multiprocess_simu(prog2run,code_name_lst,path_lst,str_lst,max_jobs=max(1,os.cpu_count()-1)):
    """run_multiprocess_simu runs simulations in parallel (if possible) on max_jobs number of threads

    Parameters
    ----------
    prog2run : function
        name of the function that runs the simulations

    code_name_lst : list of str
        list of names of the codes to run
    
    str_lst : list of str
        List containing the strings to run for the simulations

    path_lst : list of str
        List containing the path to the folder containing the simulation program
    
    max_jobs : int, optional
        Number of threads used to run the simulations, by default os.cpu_count()-1
    """
    p = multiprocessing.Pool(max_jobs)
    results = parmap.starmap(prog2run,list(zip(code_name_lst,path_lst,str_lst)), pm_pool=p, pm_processes=max_jobs,pm_pbar=True)
    p.close()
    p.join()

def run_parallel_simu(code_name_lst,path_lst,str_lst,max_jobs=max(1,os.cpu_count()-1),verbose=False,ignore_error_code=False):
    """Runs simulations in parallel on max_jobs number of threads using the
    GNU Parallel program. (https://www.gnu.org/software/parallel/). 
    If this command is used please cite:
    Tange, O. (2021, August 22). GNU Parallel 20210822 ('Kabul').
    Zenodo. https://doi.org/10.5281/zenodo.5233953

    To Install GNU Parallel on linux: (not available on Windows)
    sudo apt update
    sudo apt install parallel

    Parameters
    ----------
    prog2run : function
        name of the function that runs the simulations

    code_name_lst : list of str
        list of names of the codes to run
    
    str_lst : list of str
        List containing the strings to run for the simulations

    path_lst : list of str
        List containing the path to the folder containing the simulation program
    
    max_jobs : int, optional
        Number of threads used to run the simulations, by default os.cpu_count()-1

    verbose : bool, optional
        Display text message, by default False

    ignore_error_code : bool, optional
        Ignore all error codes from SIMsalabim, this can lead to imcomplete or wrong data, by default False
    """
    

    path2prog = path_lst[0]
    filename = 'Str4Parallel_'+str(uuid.uuid4())+'.txt'
    
    with open(os.path.join(path2prog,filename),'w') as tempfilepar:
        for idx,val in enumerate(str_lst):
            str_lst[idx] = './'+code_name_lst[idx].lower() + ' ' + str_lst[idx]
            tempfilepar.write(str_lst[idx] + "\n")
    
    curr_dir = os.getcwd()                      # Get current directory
    os.chdir(path2prog)                         # Change directory to working directory
    log_file = os.path.join(path2prog,'logjob_'+str(uuid.uuid4()) + '.dat')
    cmd_str = 'parallel --joblog '+ log_file +' --jobs '+str(int(max_jobs))+' --bar -a '+os.path.join(path2prog,filename)
    # print(cmd_str)
    if verbose:
        stdout = None
        stderr = None
    else:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL
    try:
        if verbose:
            # Output will be printed to the console
            subprocess.check_call(cmd_str.split(), encoding='utf8', cwd=path2prog)
        else:
            # Output will be redirected to DEVNULL
            subprocess.check_call(cmd_str.split(), encoding='utf8', cwd=path2prog, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir(curr_dir)                          # Change directory back to original directory
    except subprocess.CalledProcessError as e:
        os.chdir(curr_dir)                          # Change directory back to original directory
        #don't stop if error code is 95
        if e.returncode != 0:
            # log = pd.read_csv(log_file,sep='\t',usecols=['Exitval'],error_bad_lines=False)
            # replace error bad line with skip
            log = pd.read_csv(log_file,sep='\t',usecols=['Exitval'],on_bad_lines='skip')
            os.remove(log_file)
            unique_exitval = log['Exitval'].unique()
            if log['Exitval'].isin([0, 95]).all():
                if verbose:
                    for exitval in unique_exitval:
                        print(SIMsalabim_error_message(exitval) + ' found in log file, when running \n'+ str(cmd_str))
                
            else:
                if ignore_error_code:
                    warnings.warn('The following errors were caught but are ignored and the simulation continues: '+str(unique_exitval))
                    if verbose:
                        for exitval in unique_exitval: 
                            warnings.warn(SIMsalabim_error_message(e.returncode) + ' found in log file, when running \n'+ str(cmd_str))
                    pass
                else:
                    print(SIMsalabim_error_message(e.returncode) + ' found in log file, when running \n'+ str(cmd_str))
                    print('Stopping simulation...')
                    raise e

def run_sim_tmp(code_name, path, str2run, tmp_folder,lock,semaphore,verbose=False,ignore_error_code=False):
    """Run simulation in a temporary folder with a copy of all the necessary input files and then moving the output files to the original folder.

    Parameters
    ----------
    code_name : str
        name of the code to run
    path : str
        path to the folder containing the simulation program
    str2run : str
        command string to run
    tmp_folder : str
        path to the temporary folder
    lock : lock
        lock to make sure that two thread do not try to write to the same file at the same time
    semaphore : semaphore
        semaphore to limit the number of threads running at the same time
    verbose : bool, optional
        verbose?, by default False
    ignore_error_code : bool, optional
        Ignore all error codes from SIMsalabim, this can lead to imcomplete or wrong data, by default False

    Raises
    ------
    FileNotFoundError
        File not found
    ErrorCodeError
        Error code from SIMsalabim
    
    """

    semaphore.acquire()  # Acquire a semaphore

    ID = str(uuid.uuid4())
    # Create folder
    if not os.path.isdir(os.path.join(tmp_folder, 'tmp' + ID)):
        os.mkdir(os.path.join(tmp_folder, 'tmp' + ID))

    # Get files to copy
    files2copy = []
    # Check if the code exists
    System = platform.system()  # Get the system we are running on
    is_windows = (System == 'Windows')  # Check if we are on Windows
    if is_windows:
        code_name = code_name.lower() + '.exe'
    else:
        code_name = code_name.lower()

    if os.path.isfile(os.path.join(path, code_name)):
        if code_name is not files2copy:
            files2copy.append(os.path.join(path, code_name))
    else:
        raise FileNotFoundError('Code not found: ' + code_name)

    dev_par = DevParFromStr(str2run)  # Get the device parameter file from the string
    if dev_par == '':  # If no device parameter file is found, use the default one
        dev_par = os.path.join(path, 'device_parameters.txt')

    lock.acquire()
    # check if dev_para exists
    if os.path.isfile(os.path.join(path,dev_par)): # if it exists add it to the list
        dev_par = os.path.join(path,dev_par)
        if dev_par is not files2copy:
            files2copy.append(os.path.join(path,dev_par))
            # check for other necessary files
            ParFileDic = ReadParameterFile(dev_par)
            ParStrDic = GetParFromStr(str2run)
            gen_profile = ChosePar('Gen_profile',ParStrDic,ParFileDic)
            if gen_profile == 'calc':
                for key in ParFileDic.keys():
                    if 'nk_' in key:
                        if ParFileDic[key] is not files2copy:
                            if os.path.isfile(ParFileDic[key]):
                                files2copy.append(ParFileDic[key])
                            elif os.path.isfile(os.path.abspath(os.path.join(path,ParFileDic[key]))):
                                files2copy.append(os.path.abspath(os.path.join(path,ParFileDic[key])))
                            else:
                                print(os.path.abspath(os.path.join(path,ParFileDic[key])))
                                raise FileNotFoundError('File not found: '+ParFileDic[key])

                    elif key == 'spectrum':
                        if ParFileDic[key] is not files2copy:
                            if os.path.isfile(ParFileDic[key]):
                                files2copy.append(ParFileDic[key])
                            elif os.path.isfile(os.path.abspath(os.path.join(path,ParFileDic[key]))):
                                files2copy.append(os.path.abspath(os.path.join(path,ParFileDic[key])))
                            else:
                                raise FileNotFoundError('File not found: '+ParFileDic[key])
                        
    elif os.path.isfile(os.path.abspath(os.path.join(path,dev_par))): # if it exists add it to the list (in case the path is not absolute or in the same folder as the code)
        if os.path.abspath(os.path.abspath(os.path.join(path,dev_par))) is not files2copy:
            dev_par = os.path.abspath(os.path.join(path,dev_par))
            files2copy.append(os.path.abspath(os.path.join(path,dev_par)))
            # check for other necessary files
            ParFileDic = ReadParameterFile(dev_par)
            ParStrDic = GetParFromStr(str2run)
            gen_profile = ChosePar('Gen_profile',ParStrDic,ParFileDic)
            if gen_profile == 'calc':
                for key in ParFileDic.keys():
                    if 'nk_' in key:
                        if ParFileDic[key] is not files2copy:
                            if os.path.isfile(ParFileDic[key]):
                                files2copy.append(ParFileDic[key])
                            elif os.path.isfile(os.path.abspath(os.path.join(path,ParFileDic[key]))):
                                files2copy.append(os.path.abspath(os.path.join(path,ParFileDic[key])))
                            else:
                                raise FileNotFoundError('File not found: '+ParFileDic[key])
                    elif key == 'spectrum':
                        if ParFileDic[key] is not files2copy:
                            if os.path.isfile(ParFileDic[key]):
                                files2copy.append(ParFileDic[key])
                            elif os.path.isfile(os.path.abspath(os.path.join(path,ParFileDic[key]))):
                                files2copy.append(os.path.abspath(os.path.join(path,ParFileDic[key])))
                            else:
                                raise FileNotFoundError('File not found: '+ParFileDic[key])
    else:
        raise FileNotFoundError('Device parameter file not found: '+dev_par)
    
    # copy files to tmp folder
    for file in files2copy:
        filename = os.path.basename(file)
        shutil.copy(os.path.join(file), os.path.join(tmp_folder, 'tmp' + ID, filename))
            
    lock.release()

    # update device parameter file in tmp folder with values from str2run
    # get device parameter file name from dev_par
    dev_par_name = os.path.basename(dev_par)
    ParFileDic = ReadParameterFile(os.path.join(tmp_folder, 'tmp' + ID, dev_par_name))
    ParStrDic = GetParFromStr(str2run)
    for key in ParFileDic.keys():
        if key in ParStrDic.keys():
            if 'nk_' in key:
                ParFileDic[key] = os.path.basename(ParStrDic[key])
            elif key == 'spectrum':
                ParFileDic[key] = os.path.basename(ParStrDic[key])
            elif '_file' in key:
                ParFileDic[key] = os.path.basename(ParStrDic[key])
            else:
                ParFileDic[key] = ParStrDic[key]
        # need to only keep the basefilename since we copied what was needed in each tmp folder
        elif 'nk_' in key:
            ParFileDic[key] = os.path.basename(ParFileDic[key])
        elif key == 'spectrum':
            ParFileDic[key] = os.path.basename(ParFileDic[key])
        elif '_file' in key:
            ParFileDic[key] = os.path.basename(ParFileDic[key])
        

    UpdateDevParFile(ParFileDic,os.path.join(tmp_folder, 'tmp' + ID, dev_par_name),MakeCopy=False)
        

    new_str2run = code_name + ' ' + dev_par_name
    try:
        if platform.system() == 'Windows':
            subprocess.run(new_str2run, shell=True, check=True, cwd=os.path.join(tmp_folder, 'tmp' + ID))
        else:
            new_str2run = './'+new_str2run
            subprocess.run(new_str2run.split(), shell=True, check=True, cwd=os.path.join(tmp_folder, 'tmp' + ID))
    except subprocess.CalledProcessError as e:
        if ignore_error_code:
            warnings.warn('The following errors were caught but are ignored and the simulation continues: '+str(unique_exitval))
            if verbose:
                for exitval in unique_exitval: 
                    warnings.warn(SIMsalabim_error_message(e.returncode) + ' found in log file, when running \n'+ str(cmd_str))
            pass
        else:
            print(SIMsalabim_error_message(e.returncode) + ' found in log file, when running \n'+ str(cmd_str))
            print('Stopping simulation...')
            raise e
    finally:
        semaphore.release()

    # Clean up
    # move all the output files to the original folder (i.e. all files that were not copied)
    files2copy_basename = [os.path.basename(file) for file in files2copy]
    lock.acquire()
    for file in os.listdir(os.path.join(tmp_folder, 'tmp' + ID)):
        if os.path.basename(file) not in files2copy_basename:
            # if file already exists in the original folder, remove it
            if os.path.isfile(os.path.join(path, os.path.basename(file))):
                os.remove(os.path.join(path, os.path.basename(file)))
            shutil.move(os.path.join(tmp_folder, 'tmp' + ID, file), os.path.join(path,file))
    lock.release()
    # remove tmp folder
    shutil.rmtree(os.path.join(tmp_folder, 'tmp' + ID))
    if verbose:
        print('Thread ' + ID + ' finished')

def worker(q,lock,tmp_folder,semaphore,verbose,ignore_error_code):
    """Thread worker function for the run_sim_parallel_windows function

    Parameters
    ----------
    q : queue
        queue to communicate with the worker threads
    lock : lock
        lock to make sure that two thread do not try to write to the same file at the same time
    tmp_folder : str
        path to the temporary folder
    semaphore : semaphore
        semaphore to limit the number of threads running at the same time
    verbose : bool
        verbose?
    ignore_error_code : bool
        Ignore all error codes from SIMsalabim, this can lead to imcomplete or wrong data
    """    
    while True:
        item = q.get()
        if item is None:
            break
        code_name, path, str_val = item
        run_sim_tmp(code_name, path, str_val, tmp_folder,lock,semaphore,verbose,ignore_error_code)
        q.task_done()


def run_sim_parallel_windows(code_name_lst,path_lst,str_lst,max_jobs=max(1,os.cpu_count()-1),verbose=False,ignore_error_code=False):
    """Runs simulations in parallel on max_jobs number of threads.  
    This procedure should work on Windows and Linux but it is not as efficient as run_parallel_simu on Linux.
    Yet, it is the only way to run simulations in parallel on Windows is a thread safe way and making sure that two thread do not try to write to the same file at the same time.
    This is achieved by running the simulation in a temporary folder with a copy of all the necessary input files and then moving the output files to the original folder.

    Parameters
    ----------
    prog2run : function
        name of the function that runs the simulations

    code_name_lst : list of str
        list of names of the codes to run
    
    str_lst : list of str
        List containing the strings to run for the simulations

    path_lst : list of str
        List containing the path to the folder containing the simulation program
    
    max_jobs : int, optional
        Number of threads used to run the simulations, by default os.cpu_count()-1

    verbose : bool, optional
        Display text message, by default False

    ignore_error_code : bool, optional
        Ignore all error codes from SIMsalabim, this can lead to imcomplete or wrong data, by default False
    """

    lock = threading.Lock()    # Create a lock   
    semaphore = threading.Semaphore(max_jobs)  # Create a semaphore

    # Create tmp folder
    tmp_folder = os.path.join(path_lst[0], 'tmp')
    if os.path.isdir(tmp_folder):
        shutil.rmtree(tmp_folder)
        os.mkdir(tmp_folder)
    else:
        os.mkdir(tmp_folder)

    tmp_folder_lst = [tmp_folder] * len(str_lst)

    # Create a queue to communicate with the worker threads
    q = queue.Queue()

    # Start worker threads
    threads = []
    for i in range(len(str_lst)):
        t = threading.Thread(target=partial(worker,q=q,lock=lock,tmp_folder=tmp_folder_lst[i],semaphore=semaphore,verbose=verbose,ignore_error_code=ignore_error_code))
        t.start()
        threads.append(t)

    # Add tasks to the queue
    for code_name, path, str_val in zip(code_name_lst, path_lst, str_lst):
        q.put((code_name, path, str_val))

    # Wait for all tasks to be finished
    q.join()

    # Stop workers
    for i in range(len(str_lst)):
        q.put(None)

    for t in threads:
        t.join()

    # Clean up
    shutil.rmtree(tmp_folder)

def RunSimulation(Simulation_Inputs,max_jobs=os.cpu_count()-2 ,do_multiprocessing=True,verbose=False,ignore_error_code=False):
    """RunSimulation runs the simulation code using the inputs provided by PrepareSimuInputs function.

    Parameters
    ----------
    Simulation_inputs : list
        needed inputs for the simulations, see PrepareSimuInputs function for an example of the input
    max_jobs : int, optional
        number of parallel thread to run the simulations, by default os.cpu_count()-2
    do_multiprocessing : bool, optional
        whether to do multiprocessing when possible , by default True
    verbose : bool, optional
        Display text message, by default False
    ignore_error_code : bool, optional
        Ignore all error codes from SIMsalabim, this can lead to imcomplete or wrong data, by default False
    """    
    str_lst,JV_files,Var_files,scPars_files,code_name_lst,path_lst,labels = Simulation_Inputs
    
    # Check if parallel is available
    # if do_multiprocessing and (shutil.which('parallel') == None):
    #     do_multiprocessing = False
    #     if verbose:
    #         print('GNU Parallel not found, running simulations sequentially')
    #         print('Please install GNU Parallel (https://www.gnu.org/software/parallel/)')
    #         print('or try:')
    #         print('python -c "from pySIMsalabim.get_gnu_parallel import get_GNU_parallel; get_GNU_parallel()"')

    got_parallel = (shutil.which('parallel') != None)
    is_windows = (platform.system() == 'Windows')
    # Run simulation
    if do_multiprocessing and (len(str_lst) > 1):
        if verbose:
            print('Running simulations in parallel')
        if is_windows:
            run_sim_parallel_windows(code_name_lst,path_lst,str_lst,max_jobs=max_jobs,verbose=verbose,ignore_error_code=ignore_error_code)
        else:
            run_parallel_simu(code_name_lst,path_lst,str_lst,int(max_jobs),verbose=verbose,ignore_error_code=ignore_error_code)
        # run_multiprocess_simu(run_code,code_name_lst,path_lst,str_lst,int(max_jobs)) #old way of running the simulations for some reason in Ubuntu 22.04 it stopped working, worked on Ubuntu until 20.10 so you test it in case you do not want to use parallel 
        
    else:
        if verbose:
            show_progress = True
        else:
            show_progress = False
        for i in range(len(str_lst)):
            run_code(code_name_lst[i],path_lst[i],str_lst[i],show_term_output=show_progress,ignore_error_code=ignore_error_code)



def prepare_cmd_output(path2simu,parameters=None,fixed_str=None,itertool_product=False,CodeName = 'SimSS',output_Var=False,cropname=True,verbose=False):
    """Prepare the command strings to run and the fixed parameters and output files
    If itertool_product is True, this procedure will make command with fixed_str and all the possible combinations of the input parameters in parameters. (see itertools.product)
    If itertool_product is False, this procedure will make command with fixed_str and the input parameters in parameters in the order they are given. (see df.iterrows())

    Parameters
    ----------
    path2simu : str
        path to the folder containing  the simulation program.
    parameters : list, optional
        list of dictionaries containing the parameters to simulate, by default None
        Structure example: [{'name':'Gfrac','values':list(np.geomspace(1e-3,5,3))},{'name':'mun_0','values':list(np.geomspace(1e-8,1e-7,3))}]
    fixed_str : str, optional
        Add any fixed string to the simulation command, by default None
    itertool_product : bool, optional
        If True, use itertools.product to make all combinations of the parameters, if False use df.iterrows() and run the simulations in the order the parameters are given, by default False
    CodeName : str, optional
        code name, can be ['SimSS','simss','ZimT','zimt'], by default 'SimSS'
    output_Var : bool, optional
        Output the Var file?, by default False
    cropname : bool, optional
        Crop the name of the output files to a random uuid (use this is you generate filenames too long), by default True
    verbose : bool, optional
        Verbose?, by default False
    """    

    if fixed_str is None:
        if verbose:
            print('No fixed string given, using default value')
        fixed_str = ''

    if parameters is None:
        if verbose:
            print('No parameters list was given, using default value')
        parameters = []
    
    # Initialize
    str_lst,JV_files,Var_files,scPars_files,code_name_lst,path_lst,labels,val,nam = [],[],[],[],[],[],[],[],[]

    if len(parameters) == 0:
        if verbose:
            print('No parameters given')

        if output_Var:
            Var_files.append(os.path.join(Path2Simu , str('Var.dat')))
            dum_str = 'Var.dat'
        else:
            Var_files.append('none')
            dum_str = 'none -OutputRatio 0'

        str_lst.append(fixed_str+ ' -JV_file JV.dat -scPars_file scPars.dat -Var_file '+ dum_str )
        JV_files.append(os.path.join(Path2Simu , str('JV.dat')))
        scPars_files.append(os.path.join(Path2Simu , str('scPars.dat')))
        code_name_lst.append(CodeName)
        path_lst.append(path2simu)
        labels.append('Simulation')

        return str_lst,JV_files,Var_files,scPars_files,code_name_lst,path_lst,labels
    
    if len(parameters) == 1:
        itertool_product = False
    
    for param in parameters:
        val.append(param['values'])
        nam.append(param['name'])

    if itertool_product:
        idx = 0
        for i in list(itertools.product(*val)):
            str_line,lab = '',''
            JV_name = 'JV'
            Var_name = 'Var'
            scPars_name = 'scPars'
            for j,name in zip(i,nam):
                str_line = str_line +'-'+name+' {:.2e} '.format(j)
                lab = lab+name+' {:.2e} '.format(j)
                JV_name = JV_name +'_'+name +'_{:.2e}'.format(j)
                Var_name = Var_name +'_'+ name +'_{:.2e}'.format(j)
                scPars_name = scPars_name +'_'+ name +'_{:.2e}'.format(j)
            if not output_Var:
                Var_name = 'none'
            else:
                if cropname:
                    Var_name = str(uuid.uuid4())
                else:
                    Var_name = Var_name+'.dat'
            if cropname:
                rand_uuid = str(uuid.uuid4())
                JV_name = 'JV_' + rand_uuid 
                scPars_name = 'scPars_' + rand_uuid
            str_lst.append(fixed_str+ ' ' +str_line+ '-JV_file '+JV_name+ '.dat -Var_file '+Var_name+' -scPars_file '+scPars_name+'.dat')# -ExpJV '+JVexp_lst[idx])
            JV_files.append(os.path.join(Path2Simu , str(JV_name+ '.dat')))
            Var_files.append(os.path.join(Path2Simu , str(Var_name+ '.dat')))
            scPars_files.append(os.path.join(Path2Simu , str(scPars_name+ '.dat')))
            code_name_lst.append(CodeName)
            path_lst.append(Path2Simu)
            labels.append(lab)
            idx += 1
    else:
        if not all(len(l) == len(val[0]) for l in val):
            raise ValueError('Error in the input parameters list!\n The length of each list in the parameters list must be the same')
        val = np.asarray(val)
        param2run = pd.DataFrame(val.T,columns=names)

        idx = 0
        for index, row in param2run.iterrows():
            str_line = ''
            lab = ''
            JV_name = 'JV'
            Var_name = 'Var'
            scPars_name = 'scPars'
            for name in param2run.columns:
                str_line = str_line +'-'+name+' {:.2e} '.format(row[name])
                lab = lab+name+' {:.2e} '.format(row[name])
                JV_name = JV_name +'_'+name +'_{:.2e}'.format(row[name])
                Var_name = Var_name +'_'+ name +'_{:.2e}'.format(row[name])
                scPars_name = scPars_name +'_'+ name +'_{:.2e}'.format(row[name])
            if not output_Var:
                Var_name = 'none'
            else:
                if cropname:
                    Var_name = str(uuid.uuid4())
                else:
                    Var_name = Var_name+'.dat'
            if cropname:
                rand_uuid = str(uuid.uuid4())
                JV_name = 'JV_' + rand_uuid 
                scPars_name = 'scPars_' + rand_uuid
            str_lst.append(fixed_str+ ' ' +str_line+ '-JV_file '+JV_name+ '.dat -Var_file '+Var_name+' -scPars_file '+scPars_name+'.dat')# -ExpJV '+JVexp_lst[idx])
            JV_files.append(os.path.join(Path2Simu , str(JV_name+ '.dat')))
            Var_files.append(os.path.join(Path2Simu , str(Var_name+ '.dat')))
            scPars_files.append(os.path.join(Path2Simu , str(scPars_name+ '.dat')))
            code_name_lst.append(CodeName)
            path_lst.append(Path2Simu)
            labels.append(lab)
            idx += 1



# def PrepareSimuInputs(Path2Simu,parameters=None,fixed_str=None,CodeName = 'SimSS',output_Var=False,cropname=True,verbose=False):
#     """Prepare the command strings to run and the fixed parameters and output files
#     This procedure will make command with fixed_str and all the possible combinations of the input parameters in parameters. (see itertools.product)

#     Parameters
#     ----------
#     Path2Simu : str
#         path to the folder containing  the simulation program.
#     parameters : list, optional
#         list of dictionaries containing the parameters to simulate, by default None
#         Structure example: [{'name':'Gfrac','values':list(np.geomspace(1e-3,5,3))},{'name':'mun_0','values':list(np.geomspace(1e-8,1e-7,3))}]
#     fixed_str : _type_, optional
#         Add any fixed string to the simulation command, by default None
#     CodeName : str, optional
#         code name, can be ['SimSS','simss','ZimT','zimt'], by default 'SimSS'
#     output_Var : bool, optional
#         Output the Var file?, by default False
#     cropname : bool, optional
#         Crop the name of the output files to a random uuid (use this is you generate filenames too long), by default True        
#     verbose : bool, optional
#         Verbose?, by default False

#     Returns
#     -------
#     list
#         list of lists containing the command strings to run the simulations, the output files and the fixed parameters
#         str_lst, JV_files, Var_files, scPars_files, code_name_lst, path_lst, labels
#     """    
#     ## Prepare strings to run
#     # Fixed string
#     if fixed_str is None:
#         if verbose:
#             print('No fixed string given, using default value')
#         fixed_str = ''  # add any fixed string to the simulation command

#     # Parameters to vary
#     if parameters is None:
#         if verbose:
#             print('No parameters list was given, using default value')
#         parameters = []
#         parameters.append({'name':'Gfrac','values':[0]})

    
#     # Initialize     
#     str_lst,JV_files,Var_files,scPars_files,code_name_lst,path_lst,labels,val,nam = [],[],[],[],[],[],[],[],[]

#     if len(parameters) > 1:
#         for param in parameters: # initalize lists of values and names
#             val.append(param['values'])
#             nam.append(param['name'])

#         idx = 0
#         for i in list(itertools.product(*val)): # iterate over all combinations of parameters
#             str_line = ''
#             lab = ''
#             JV_name = 'JV'
#             Var_name = 'Var'
#             scPars_name = 'scPars'
#             for j,name in zip(i,nam):
#                 str_line = str_line +'-'+name+' {:.2e} '.format(j)
#                 lab = lab+name+' {:.2e} '.format(j)
#                 JV_name = JV_name +'_'+name +'_{:.2e}'.format(j)
#                 Var_name = Var_name +'_'+ name +'_{:.2e}'.format(j)
#                 scPars_name = scPars_name +'_'+ name +'_{:.2e}'.format(j)
#             if not output_Var:
#                 Var_name = 'none'
#                 add_str = ''
#             else:
#                 if cropname:
#                     Var_name = str(uuid.uuid4())
#                 else:
#                     Var_name = Var_name+'.dat'
#             if cropname:
#                 rand_uuid = str(uuid.uuid4())
#                 JV_name = 'JV_' + rand_uuid 
#                 scPars_name = 'scPars_' + rand_uuid
#             str_lst.append(fixed_str+add_str+ ' ' +str_line+ '-JV_file '+JV_name+ '.dat -Var_file '+Var_name+' -scPars_file '+scPars_name+'.dat')# -ExpJV '+JVexp_lst[idx])
#             JV_files.append(os.path.join(Path2Simu , str(JV_name+ '.dat')))
#             Var_files.append(os.path.join(Path2Simu , str(Var_name+ '.dat')))
#             scPars_files.append(os.path.join(Path2Simu , str(scPars_name+ '.dat')))
#             code_name_lst.append(CodeName)
#             path_lst.append(Path2Simu)
#             labels.append(lab)
#             idx += 1
#     elif len(parameters) == 1:
#         # str_line = ''
#         # lab = ''
#         # JV_name = 'JV'
#         # Var_name = 'Var'
#         # scPars_name = 'scPars'
#         name = parameters[0]['name']
#         idx = 0
#         for j in parameters[0]['values']:
#             str_line = ''
#             lab = ''
#             JV_name = 'JV'
#             Var_name = 'Var'
#             scPars_name = 'scPars'
#             str_line = '-'+name+' {:.2e} '.format(j)
#             lab = name+' {:.2e} '.format(j)
#             JV_name = JV_name +'_'+name +'_{:.2e}'.format(j)
#             Var_name = Var_name +'_'+ name +'_{:.2e}'.format(j)
#             if not output_Var:
#                 Var_name = 'none'
#                 add_str = ' -OutputRatio 0'
#             else:
#                 if cropname:
#                     Var_name = str(uuid.uuid4())
#                 add_str = ''
#             if cropname:
#                 rand_uuid = str(uuid.uuid4())
#                 JV_name = 'JV_' + rand_uuid 
#                 scPars_name= 'scPars_' + rand_uuid

#             scPars_name = scPars_name +'_'+ name +'_{:.2e}'.format(j)
#             str_lst.append(fixed_str+add_str+ ' ' +str_line+ '-JV_file '+JV_name+ '.dat -Var_file '+Var_name+' -scPars_file '+scPars_name+'.dat')# -ExpJV '+JVexp_lst[idx])
#             JV_files.append(os.path.join(Path2Simu , str(JV_name+ '.dat')))
#             Var_files.append(os.path.join(Path2Simu , str(Var_name+ '.dat')))
#             scPars_files.append(os.path.join(Path2Simu , str(scPars_name+ '.dat')))
#             code_name_lst.append(CodeName)
#             path_lst.append(Path2Simu)
#             labels.append(lab)

            
#             idx += 1
#     else:
#         print('No parameters given')
#         if output_Var:
#             Var_files.append(os.path.join(Path2Simu , str('Var.dat')))
#             dum_str = 'Var.dat'
#         else:
#             Var_files.append('none')
#             dum_str = 'none -OutputRatio 0'
#         str_lst.append(fixed_str+ ' -JV_file JV.dat -scPars_file scPars.dat -Var_file '+ dum_str )
#         JV_files.append(os.path.join(Path2Simu , str('JV.dat')))
        
#         scPars_files.append(os.path.join(Path2Simu , str('scPars.dat')))
#         code_name_lst.append(CodeName)
#         path_lst.append(Path2Simu)
#         labels.append('Simulation')


    
#     return str_lst,JV_files,Var_files,scPars_files,code_name_lst,path_lst,labels

# def DegradationPrepareSimuInputs(Path2Simu,parameters=None,fixed_str=None,CodeName = 'SimSS',output_Var=False,cropname=True,verbose=False):
#     """Prepare the command strings to run and the fixed parameters and output files
#     This procedure will make command with fixed_str and all the possible combinations of the input parameters in parameters. (see itertools.product)

#     Parameters
#     ----------
#     Path2Simu : str
#         path to the folder containing  the simulation program.
#     parameters : list, optional
#         list of dictionaries containing the parameters to simulate, by default None
#         Structure example: [{'name':'Gfrac','values':list(np.geomspace(1e-3,5,3))},{'name':'mun_0','values':list(np.geomspace(1e-8,1e-7,3))}]
#     fixed_str : _type_, optional
#         Add any fixed string to the simulation command, by default None
#     CodeName : str, optional
#         code name, can be ['SimSS','simss','ZimT','zimt'], by default 'SimSS'
#     output_Var : bool, optional
#         Output the Var file?, by default False
#     cropname : bool, optional
#         Crop the name of the output files to a random uuid (use this is you generate filenames too long), by default True
#     verbose : bool, optional
#         Verbose?, by default False

#     Returns
#     -------
#     list
#         list of lists containing the command strings to run the simulations, the output files and the fixed parameters
#         str_lst, JV_files, Var_files, scPars_files, code_name_lst, path_lst, labels
#     """    
#     ## Prepare strings to run
#     # Fixed string
#     if fixed_str is None:
#         if verbose:
#             print('No fixed string given, using default value')
#         fixed_str = ''  # add any fixed string to the simulation command

#     # Parameters to vary
#     if parameters is None:
#         if verbose:
#             print('No parameters list was given, using default value')
#         parameters = []
#         parameters.append({'name':'Gfrac','values':[0]})

    
#     # Initialize     
#     str_lst,JV_files,Var_files,scPars_files,code_name_lst,path_lst,labels,val,nam = [],[],[],[],[],[],[],[],[]
#     names = []

#     if len(parameters) > 1:
#         for i in parameters:
#             names.append(i['name'])
#             val.append(i['values'])
        
#         if not all(len(l) == len(val[0]) for l in val):
#             raise ValueError('Error in the input parameters list!\n The length of each list in the parameters list must be the same')
#         val = np.asarray(val)
#         param2run = pd.DataFrame(val.T,columns=names)

#         idx = 0
#         for index, row in param2run.iterrows():
#             str_line = ''
#             lab = ''
#             JV_name = 'JV'
#             Var_name = 'Var'
#             scPars_name = 'scPars'
#             for name in param2run.columns:
#                 str_line = str_line +'-'+name+' {:.2e} '.format(row[name])
#                 lab = lab+name+' {:.2e} '.format(row[name])
#                 JV_name = JV_name +'_'+name +'_{:.2e}'.format(row[name])
#                 Var_name = Var_name +'_'+ name +'_{:.2e}'.format(row[name])
#                 scPars_name = scPars_name +'_'+ name +'_{:.2e}'.format(row[name])
#             if not output_Var:
#                 Var_name = 'none'
#                 add_str = ''
#             else:
#                 if cropname:
#                     Var_name = str(uuid.uuid4())
#                 else:
#                     Var_name = Var_name+'.dat'
            
#             if cropname:
#                 rand_uuid = str(uuid.uuid4())
#                 JV_name = 'JV_' + rand_uuid 
#                 scPars_name = 'scPars_' + rand_uuid
#             str_lst.append(fixed_str+add_str+ ' ' +str_line+ '-JV_file '+JV_name+ '.dat -Var_file '+Var_name+' -scPars_file '+scPars_name+'.dat')# -ExpJV '+JVexp_lst[idx])
#             JV_files.append(os.path.join(Path2Simu , str(JV_name+ '.dat')))
#             Var_files.append(os.path.join(Path2Simu , str(Var_name+ '.dat')))
#             scPars_files.append(os.path.join(Path2Simu , str(scPars_name+ '.dat')))
#             code_name_lst.append(CodeName)
#             path_lst.append(Path2Simu)
#             labels.append(lab)
#             idx += 1
#     elif len(parameters) == 1:
#         # str_line = ''
#         # lab = ''
#         # JV_name = 'JV'
#         # Var_name = 'Var'
#         # scPars_name = 'scPars'
#         name = parameters[0]['name']
#         idx = 0
#         for j in parameters[0]['values']:
#             str_line = ''
#             lab = ''
#             JV_name = 'JV'
#             Var_name = 'Var'
#             scPars_name = 'scPars'
#             str_line = '-'+name+' {:.2e} '.format(j)
#             lab = name+' {:.2e} '.format(j)
#             JV_name = JV_name +'_'+name +'_{:.2e}'.format(j)
#             Var_name = Var_name +'_'+ name +'_{:.2e}'.format(j)
#             if not output_Var:
#                 Var_name = 'none'
#                 add_str = ''
#             else:
#                 Var_name = Var_name+'.dat'
#             if cropname:
#                 rand_uuid = str(uuid.uuid4())
#                 JV_name = 'JV_' + rand_uuid 
#                 scPars_name= 'scPars_' + rand_uuid
#             scPars_name = scPars_name +'_'+ name +'_{:.2e}'.format(j)
#             str_lst.append(fixed_str+add_str+ ' ' +str_line+ '-JV_file '+JV_name+ '.dat -Var_file '+Var_name+' -scPars_file '+scPars_name+'.dat')# -ExpJV '+JVexp_lst[idx])
#             JV_files.append(os.path.join(Path2Simu , str(JV_name+ '.dat')))
#             Var_files.append(os.path.join(Path2Simu , str(Var_name+ '.dat')))
#             scPars_files.append(os.path.join(Path2Simu , str(scPars_name+ '.dat')))
#             code_name_lst.append(CodeName)
#             path_lst.append(Path2Simu)
#             labels.append(lab)
#     else:
#         print('No parameters given')
#         str_lst.append(fixed_str+ ' -JV_file JV.dat -Var_file Var.dat -scPars_file scPars.dat')# -ExpJV '+JVexp_lst[idx])
#         JV_files.append(os.path.join(Path2Simu , str('JV.dat')))
#         if output_Var:
#             Var_files.append(os.path.join(Path2Simu , str('Var.dat')))
#         else:
#             Var_files.append('none')
#         scPars_files.append(os.path.join(Path2Simu , str('scPars.dat')))
#         code_name_lst.append(CodeName)
#         path_lst.append(Path2Simu)
#         labels.append('Simulation')



if __name__ == '__main__':

    print('I am not doing anything, please import me in your script'+'\n')