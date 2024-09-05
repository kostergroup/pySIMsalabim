"""Perform EQE simulations"""

######### Package Imports #########################################################################

import os, uuid
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import constants
from pySIMsalabim.utils import general as utils_gen
from pySIMsalabim.utils.parallel_sim import *
from pySIMsalabim.utils.utils import update_cmd_pars

######### Constants #################################################################################

h=constants.h
c=constants.c
q=constants.e

######### Functions #################################################################################

def EQE_create_spectrum_files(lambda_array, p, session_path, spectrum_path, tmp_spectrum_path):
    """Create all the spectrum files with monochromatic peaks at the specified wavelength, 
    with a fixed height set by the number of added photons p. The files are stored in a temporary folder: tmp_spectrum.

    Parameters
    ----------
    lambda_array : array
        Array with the wavelengths at which the monochromatic peaks will be created.
    p : float
        Number of photons that are added to the irradiance.
    session_path : string
        Path to the session folder where the files must be created.
    spectrum_path : string
        Path to the original spectrum file.
    tmp_spectrum_path : string
        Path to the temporary folder where the modified spectrum files will be stored.
    """
    for i in lambda_array:
        # Reset the spectrum data on every iteration to avoid accumulation of the added photons at each wavelength
        org_spectrum_data = pd.read_csv(os.path.join(session_path,spectrum_path), sep=r'\s+')

        # Get the filename of the spectrum without any possible path
        spectrum_filename = os.path.basename(spectrum_path)

        #find row with value closest to i and multiply the value in the irradiance column with 10
        row = org_spectrum_data.iloc[(org_spectrum_data['lambda']-i).abs().argsort()[:1]]
        org_spectrum_data.loc[row.index, 'I'] += (p*((h*c)/i)/1e-9) #2% of absorbed photons of Si
        org_spectrum_data.to_csv(os.path.join(tmp_spectrum_path,f'{int(i*1e9)}nm_{spectrum_filename}'), sep=' ', index=False, float_format='%.3e')

def get_CurrDens(JV_file, session_path):
    """ Get the current density  and its from the JV_file as stored in the first row.
    Parameters
    ----------
    JV_file : str, optional
        Name of the file where the JV data is stored. Must be unique for each simulation, by default 'JV.dat'
    session_path : string
        Path to the session folder where the simulation will run. 

    Returns
    -------
    float, float
        Short-circuit current and its error.
    """     
    data_JV = pd.read_csv(os.path.join(session_path,JV_file), sep=r'\s+')
    J0=data_JV['Jext'][0]
    J0_err=data_JV['errJ'][0]

    # Remove the JV file as it is not needed anymore
    os.remove(os.path.join(session_path,JV_file))

    return J0, J0_err

def calc_EQE(Jext,Jext_err,J0_single, J0_err_single, lambda_array,p):
    """Calculate the EQE values for the monochromatic peaks at each wavelength. Based on the change in the short-circuit current and the number of added photons.

    Parameters
    ----------
    Jext : array
        Short-circuit current density for each monochromatic peak.
    Jext_err : array
        Error in the short-circuit current density for each monochromatic peak.
    J0_single : float
        Short-circuit current density for the normal spectrum.
    J0_err_single : float
        Error in the short-circuit current density for the normal spectrum.
    lambda_array : array
        Array with the wavelengths at which the monochromatic peaks were created.
    p : float
        Number of photons that are added to the irradiance.

    Returns
    -------
    array, array, array, array, array
        Arrays with the change in short-circuit current density, error in the change in short-circuit currentdensity,
        monochromatic intensity, EQE values and error in the EQE values.
    """
    # Calculate the change in short-circuit current density and its error
    deltaJ = [abs(x - J0_single) for x in Jext]
    deltaJerr = [x + J0_err_single for x in Jext_err]

    # Calculate the increase in intensity/photon flux/energy of the monochromatic peaks
    I_diff = [((p * h * c) / x) / 1e-9 for x in lambda_array]
    area = 1e-9 * np.array(I_diff)
    E_photon = np.array([(h * c) / x for x in lambda_array])

    # Calculate the EQE values and their errors
    EQE_val=deltaJ/((q*area)/E_photon)
    EQE_err=np.multiply(deltaJerr,((q*area)/E_photon))

    return deltaJ, deltaJerr, I_diff, EQE_val, EQE_err

def run_EQE(simss_device_parameters, session_path, spectrum, lambda_min, lambda_max, lambda_step, Vext, outfile_name, JV_file_name = 'JV.dat', remove_dirs = True, parallel = False, max_jobs = max(1,os.cpu_count()-1), run_mode = True, **kwargs):
    """Run the EQE calculation for a given spectrum and external voltage, and save the results in a file.

    Parameters
    ----------
    simss_device_parameters : string
        Name of the device parameters file.
    session_path : string
        Path to the session folder where the simulation will run.
    spectrum : string
        Path to the original spectrum file.
    lambda_min : float
        Minimum wavelength for the spectrum.
    lambda_max : float
        Maximum wavelength for the spectrum.
    lambda_step : float
        Step size for the wavelength.
    Vext : float
        External voltage at which the simulation will run and the EQE must be calculated.
    outfile_name : string
        Name of the file where the results will be stored.
    JV_file_name : string
        Name of the JV file.
    remove_dirs : bool, optional
        Remove the temporary directories, by default True
    parallel : bool, optional
        Run the simulations in parallel, by default False
    max_jobs : int, optional
        Maximum number of parallel jobs, by default max(1,os.cpu_count()-1)
    run_mode : bool, optional
        indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default True
    **kwargs : dict
        Additional arguments to be passed to the function.

    Returns
    -------
    int
        0 if the function runs successfully.
    """
    
    UUID = kwargs.get('UUID', '') # Check if the user wants to add a UUID to the JV file name
    cmd_pars = kwargs.get('cmd_pars', None) # Check if the user wants to add additional command line parameters to the simulation
    force_multithreading = kwargs.get('force_multithreading', False) # Check if the user wants to force multithreading instead of using GNU parallel 
    if os.name == 'nt':  
        threadsafe = kwargs.get('threadsafe', True) # Check if the user wants to force the use of threads instead of processes
    else:
        threadsafe = kwargs.get('threadsafe', False) # Check if the user wants to force the use of threads instead of processes
        
    # Update the JV file name with the UUID
    if UUID != '':
        dum_str = f'_{UUID}'
    else:
        dum_str = ''

    JV_file_name_base, JV_file_name_ext = os.path.splitext(JV_file_name)
    JV_file_name = JV_file_name_base + dum_str + JV_file_name_ext
    
    msg_list = [] # Init the returnmessage list
    p=0.03*1e21 #number of photons that are added to the irradiance. in this example it is 3% of the number of photons absorbed by a Silicon solar cell in m-2
    
    # Create a tmp folder to store the modified AM1.5G spectra
    # rnd_ID = str(uuid.uuid4())
    tmp_spectrum_path = os.path.join(session_path,'tmp_spectrum'+UUID)
    if not os.path.exists(tmp_spectrum_path):
        os.makedirs(tmp_spectrum_path)

    # Create wavelength array. If the last point in the array is outside the specified range, remove it
    lambda_array_init = np.arange(lambda_min,lambda_max+lambda_step,lambda_step)
    if lambda_array_init[-1] > lambda_max:
        lambda_array = np.delete(lambda_array_init,-1)
    else:
        lambda_array = lambda_array_init

    # convert to m
    lambda_array = lambda_array*1e-9

    EQE_create_spectrum_files(lambda_array, p, session_path, spectrum, tmp_spectrum_path)

    #runs for no monochromatic peak (normal spectrum) and obtains J0 and its err
    # Prepare the arguments for the simulation
    EQE_args = [{'par':'dev_par_file','val':simss_device_parameters},
                    {'par':'autoTidy','val':str(0)}, # unnecessary to tidy up the files all the time
                    {'par':'outputRatio','val':str(0)}, # we don't care about the var file here
                    {'par':'Vmin','val':str(Vext)},
                    {'par':'Vmax','val':str(Vext)},
                    {'par':'spectrum','val':spectrum},
                    {'par':'JVFile','val':os.path.join(session_path,JV_file_name)}, # need to add the session path to the JV file name to make sure it is stored in the session folder
                    # below are unecessary output files but we asign them to avoid errors
                    {'par':'logFile','val':'log'+dum_str+'.txt'},
                    {'par':'varFile','val':'none'},
                    {'par':'scParsFile','val':'scPars'+dum_str+'.txt'}
                    ]
    
    if cmd_pars is not None:
        EQE_args = update_cmd_pars(EQE_args, cmd_pars)
    
    if threadsafe:
        result, message = utils_gen.run_simulation_filesafe('simss', EQE_args, session_path, run_mode)
    else:
        result, message = utils_gen.run_simulation('simss', EQE_args, session_path, run_mode)
    # result, message = run_sim_EQE(simss_device_parameters, session_path, spectrum, Vext, JV_file_name, run_mode)
    
    # If the simulation fails, stop running the script and exit
    if not result.returncode == 0:
        if result.returncode == 95:
            message = f'SIMsalabim raised an error with errorcode {result.returncode}, simulation did not converge.'
        msg_list.append(message)
        return result.returncode, msg_list
    
    # Get the current density Jext and its error
    J0_single, J0_err_single = get_CurrDens(JV_file_name, session_path)

    Jext,Jext_err = [],[]

    #obtains Jext and Jext error for a monochromatic peak at each wavelength        
    if parallel and len(lambda_array) > 1 : # Run the simulations in parallel
        # JV_file_name_base, JV_file_name_ext = os.path.splitext(JV_file_name)
        log_file_name_base, log_file_name_ext = os.path.splitext('log'+dum_str+'.txt')
        scParsFile_name_base, scParsFile_name_ext = os.path.splitext('scPars'+dum_str+'.txt')

        EQE_args_list = []
        for i in lambda_array:
            JV_file_name_single = f'{JV_file_name}_{int(i*1e9)}nm{JV_file_name_ext}'
            dum_args = [{'par':'dev_par_file','val':simss_device_parameters},
                        {'par':'autoTidy','val':str(0)}, # unnecessary to tidy up the files all the time
                        {'par':'outputRatio','val':str(0)}, # we don't care about the var file here
                        {'par':'Vmin','val':str(Vext)},
                        {'par':'Vmax','val':str(Vext)},
                        {'par':'spectrum','val':os.path.join(tmp_spectrum_path,f'{int(i*1e9)}nm_{os.path.basename(spectrum)}')},
                        {'par':'JVFile','val':os.path.join(session_path,JV_file_name_single)}, # makes sure that the JV file is unique for each simulation and is stored in the session folder
                        # below are unecessary output files but we asign them to avoid errors
                        {'par':'logFile','val':f'{log_file_name_base}_{int(i*1e9)}nm{log_file_name_ext}'},
                        {'par':'varFile','val':'none'},
                        {'par':'scParsFile','val':f'{scParsFile_name_base}_{int(i*1e9)}nm{scParsFile_name_ext}'}
                        ]
            if cmd_pars is not None:
                dum_args = update_cmd_pars(dum_args, cmd_pars)
            EQE_args_list.append(dum_args)
        
        results = run_simulation_parallel('simss', EQE_args_list, session_path, max_jobs, force_multithreading=force_multithreading)
        
        for i in lambda_array:
            JV_file_name_single = f'{JV_file_name}_{int(i*1e9)}nm{JV_file_name_ext}'
            J_single, Jerr_single = get_CurrDens(JV_file_name_single,session_path)
            Jext.append(J_single)
            Jext_err.append(Jerr_single)
            
            

    else:
        for i in lambda_array:
            JV_file_name_base, JV_file_name_ext = os.path.splitext(JV_file_name)
            JV_file_name_single = f'{JV_file_name_base}_{int(i*1e9)}nm{JV_file_name_ext}'
            log_file_name_base, log_file_name_ext = os.path.splitext('log'+dum_str+'.txt')
            scParsFile_name_base, scParsFile_name_ext = os.path.splitext('scPars'+dum_str+'.txt')
            
            EQE_args = [{'par':'dev_par_file','val':simss_device_parameters},
                        {'par':'autoTidy','val':str(0)}, # unnecessary to tidy up the files all the time
                        {'par':'outputRatio','val':str(0)}, # we don't care about the var file here
                        {'par':'Vmin','val':str(Vext)},
                        {'par':'Vmax','val':str(Vext)},
                        {'par':'spectrum','val':os.path.join(tmp_spectrum_path,f'{int(i*1e9)}nm_{os.path.basename(spectrum)}')},
                        {'par':'JVFile','val':os.path.join(session_path,JV_file_name_single)},#JV_file_name_single}, # makes sure that the JV file is unique for each simulation and is stored in the session folder
                        # below are unecessary output files but we asign them to avoid errors
                        {'par':'logFile','val':f'{log_file_name_base}_{int(i*1e9)}nm{log_file_name_ext}'},
                        {'par':'varFile','val':'none'},
                        {'par':'scParsFile','val':f'{scParsFile_name_base}_{int(i*1e9)}nm{scParsFile_name_ext}'}
                        ]  

            if cmd_pars is not None:
                EQE_args = update_cmd_pars(EQE_args, cmd_pars)

            if threadsafe:
                result, message = utils_gen.run_simulation_filesafe('simss', EQE_args, session_path, run_mode)
            else:
                result, message = utils_gen.run_simulation('simss', EQE_args, session_path, run_mode)
            # result, message = run_sim_EQE(simss_device_parameters, session_path, os.path.join('tmp_spectrum',f'{int(i*1e9)}_{os.path.basename(spectrum)}'), Vext, JV_file_name_single,run_mode)
            
            if not result.returncode == 0:
                msg_list.append(message)

            J_single, Jerr_single = get_CurrDens(JV_file_name_single,session_path)
            
            Jext.append(J_single)
            Jext_err.append(Jerr_single)


    # Remove the tmp folder as it is not needed anymore
    if remove_dirs:
        for file in os.listdir(tmp_spectrum_path):
            os.remove(os.path.join(tmp_spectrum_path,file))
        os.rmdir(os.path.join(tmp_spectrum_path))

    # remove all files starting with 'log'+dum_str and 'scPars'+dum_str
    for file in os.listdir(session_path):
        if file.startswith('log'+dum_str) or file.startswith('scPars'+dum_str):
            os.remove(os.path.join(session_path,file))
            
    # Calculate EQE
    deltaJ, deltaJerr, I_diff, EQE_val, EQE_err = calc_EQE(Jext,Jext_err,J0_single, J0_err_single, lambda_array,p)

    # Save the results in a file
    fp = open(os.path.join(session_path,outfile_name), 'w')
    fp.write('lambda Jext Jerr deltaJ deltaJerr Imonopeak EQE EQEerr\n')
    for i in range(len(lambda_array)):
        fp.write(f'{lambda_array[i]:.3e} {Jext[i]:.3e} {Jext_err[i]:.3e} {deltaJ[i]:.3e} {deltaJerr[i]:.3e} {I_diff[i]:.3e} {EQE_val[i]:.3e} {EQE_err[i]:.3e}\n')
    fp.close()
    
    if len(msg_list) != 0:
        return 1, msg_list
    else:
        return 0, msg_list

if __name__ == '__main__':
    simss_device_parameters = 'simulation_setup_simss.txt'
    session_path = os.getcwd()
    spectrum = 'Data_spectrum/AM15G.txt'

    lambda_min = 280
    lambda_max = 1000
    lambda_step = 20
    Vext = [0]

    for i in range(len(Vext)):
        outfile_name = f'output_{Vext[i]}V.dat'
        retval = run_EQE(simss_device_parameters, session_path, spectrum, lambda_min, lambda_max, lambda_step, Vext[i], outfile_name, remove_dirs=True, run_mode=False)
    
    #TMP
    plt.figure()
    for i in Vext:
        res = pd.read_csv(f'output_{Vext[i]}V.dat', sep=r'\s+')
        plt.scatter(res['lambda'], res['EQE'], label=f'V = {i}')
        plt.title('EQE for solar cell', fontsize = 16)
        plt.tick_params(axis='both',direction='in')
        plt.xlabel('Wavelength (m)', fontsize = 16)
        plt.ylabel('EQE [%]', fontsize = 16)
        plt.xlim(lambda_min, lambda_max)
        plt.legend()

    plt.show()
