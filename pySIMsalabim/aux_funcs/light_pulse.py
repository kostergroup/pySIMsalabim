"""Functions to run a ZimT simulation using a (Gaussian) light pulse"""
######### Package Imports #########################################################################

import os, sys
import numpy as np
import scipy as sp
# import pySIMsalabim
## Import pySIMsalabim, if not successful, add the parent directory to the system path
try :
    import pySIMsalabim as sim
except ImportError:
    # Add the parent directory to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import pySIMsalabim as sim

from pySIMsalabim.utils import general as utils_gen
from pySIMsalabim.utils.utils import *
from pySIMsalabim.utils.device_parameters import *

######### Function Definitions ####################################################################
def create_spectrum(I_pulse, wavelength, FWHM, session_path, spectrum_name, spectrum_path = '', lambda_min=280E-9, lambda_max=4000E-9, lambda_step=1E-9):
    ''' Create a spectrum file with monochrqamtic wavelength, which contains the wavelength (lambda) and the irradiance (I) for each wavelength. 
    The spectrum is defined as a Gaussian pulse with the specified parameters.

    Parameters
    ----------
    I_pulse : float
        The intensity of the pulse in photons/m^2/pulse
    wavelength : float
        The wavelength of the pulse in meters
    FWHM : float
        The full width at half maximum (FWHM) of the pulse
    session_path : string
        The path to the session folder, which is the working directory for the simulation
    spectrum_name : string
        The name of the spectrum file to create, which will be saved in the session path/spectrum_path
    spectrum_path : string, optional
        The path to the folder where the spectrum file will be saved, relative to the session path, by default ''
    lambda_min : float, optional
        The minimum wavelength to include in the spectrum, by default 280E-9
    lambda_max : float, optional
        The maximum wavelength to include in the spectrum, by default 4000E-9
    lambda_step : float, optional
        The wavelength step to use in the spectrum, by default 1E-9
    
    Returns
    -------
    string
        The path to the created spectrum file, relative to the session path
    '''
    
    # Cover the entire lambda range, even though most will be zero
    lambdas = np.arange(lambda_min, lambda_max, lambda_step)
    I = np.zeros(len(lambdas))

    # Calculate the Irradiance for the given wavelength
    Irr = (I_pulse*sp.constants.h*sp.constants.c/wavelength)*(np.sqrt(np.pi/(4 * np.log(2)))/FWHM)/1E-9 

    # Create a dataframe with the wavelengths and Irr
    df = pd.DataFrame({'lambda': lambdas, 'I': I})

    # find the column where lambda is closest to the main pulse wavelength and add the irradiance for that wavelength
    closest_index = (np.abs(lambdas - wavelength)).argmin()
    df.loc[closest_index, 'I'] = Irr

    # Save the dataframe to a csv file
    df.to_csv(os.path.join(session_path,spectrum_path, spectrum_name), index=False, sep = ' ', float_format='%.3e')

    return os.path.join(spectrum_path, spectrum_name)

def create_tVG_light_pulse(tmax, tVG_name, session_path, t_scale = 'lin', t_step = 1E-9, t_pulse = 40E-9, FWHM = 2E-9):
    ''' Create a tVG file for a light pulse simulation, which contains the time (t), the external voltage (Vext), and the generation profile (G_frac) for each time step. 
    The generation profile is defined as a Gaussian pulse with the specified parameters.

    Parameters
    ----------
    tmax : float
        The maximum time for the experiment
    tVG_name : string
        The name of the tVG file to create, which will be saved in the session path
    session_path : string
        The path to the session folder, which is the working directory for the simulation
    t_scale : string, optional
        The time scale to use for the time array, which can be 'lin' for linear or 'log' for logarithmic, by default 'lin'
    t_step : float, optional
        The time step when using a linear scale and the shortest timestep using a logarithmic scale, by default 1E-9. Note: Make sure the time step is small enough to accurately describe the laser pulse, as defined by the FWHM.
    t_pulse : float, optional
        The center of the pulse in time. Make sure it is far enough from t=0 otherwise first part of pulse will be cut, 
        resulting in lower number of photons, by default 40
    FWHM : float, optional
        The full width at half maximum (FWHM) of the pulse, by default 2E-9

    Returns
    -------
    int
        0 if the tVG file is created successfully, -1 if there is an error
    string
        A message indicating the success or failure of the tVG file creation
    '''

    numPointsDecade = 1000 # Number of points per decade for the logarithmic time array

    if t_scale == 'lin':
        # Create a linear time array from 0 to tmax with a step of tstep
        time = np.arange(0, tmax+ t_step, t_step)
    else:
        # Create a logarithmic time array from tstep to tmax
        steps = int(np.ceil(np.log10(tmax/t_step) * numPointsDecade))
        time = np.logspace(np.log10(t_step), np.log10(tmax), num=steps) 
        # Insert t=0 at the beginning of the time array, as this is skipped in the logspace
        time = np.insert(time, 0, 0)

    V = np.zeros(len(time)) # Initialize the voltage array

    G = np.zeros(len(time)) # Main Pulse Generation Profile

    Track = np.zeros(len(time),dtype=int) # Track state array, fixed to 0 and formatted as integer

    for t in range(len(time)):
        # Skip t=0, as we force it G=0 there
        if t > 0:
            G[t] = np.exp(-((time[t]-t_pulse)/((FWHM/(2*np.sqrt(2*np.log(2))))*np.sqrt(2)))**2) #Input Function (Gaussian Laser Pulse)

    # Write to the tVG file
    tVG = pd.DataFrame({'t': time, 'Vext': V, 'G_frac': G})

    tVG['Track'] = Track.astype(int) # Add the Track column to the DataFrame. This needs to be done separately as the Track column must be an integer and the other columns are floats. 

    tVG.to_csv(os.path.join(session_path,tVG_name), index=False, sep = ' ', float_format='%.4e')

    msg = 'Success'
    retval = 0

    return retval, msg

def run_light_pulse_simu(zimt_simulation_setup, session_path, t_max, t_scale, t_step, t_pulse, FWHM, genProfile, spectrum_type = 'laser', I = 6E15, wavelength = 640E-9, run_mode=False, tVG_name = 'tVG.txt', tj_name = 'tj.dat',log_name = 'log.txt', varFile ='none', cmd_pars=None, turnoff_autoTidy = True, verbose = False, threadsafe = False):
    ''' Run a ZimT simulation for a (gaussian) light pulse. The function will create the necessary tVG file, as well as take into account the type of generation profile specified by the user, and create the necessary spectrum file if needed. 
    The function will also handle the use of blocking layers, by updating the simulation setup file and creating the necessary blocking layer parameter files.
    
    Parameters
    ----------
    zimt_simulation_setup : string
        The name of the ZimT device parameters file, which should be located in the session path
    session_path : string
        The path to the session folder, which is the working directory for the simulation
    t_max : float
        The maximum time for the experiment
    t_scale : string
        The time scale to use for the time array, which can be 'lin' for linear or 'log' for logarithmic
    t_step : float
        The time step for the tVG file
    t_pulse : float
        The center of the pulse in time. Make sure it is far enough from t=0 otherwise first part of pulse will be cut, resulting in lower number of photons
    FWHM : float
        The full width at half maximum (FWHM) of the pulse
    genProfile : string
        The type of generation profile to use, which can be 'calc' for a calculated generation profile based on a spectrum, 'none' for no generation profile (in which case the generation rate should be specified in the simulation setup file or through cmd_pars), or a filename for a user supplied generation profile (in which case the file should be located in the session path)
    spectrum_type : string, optional
        The type of spectrum to use for the calculated generation profile, which can be 'laser' for a Gaussian spectrum based on the specified intensity, wavelength, and FWHM, or 'setup' to use the spectrum as specified in the simulation setup file, by default 'laser'
    I : float, optional
        The intensity of the pulse in photons/m^2/pulse, only used when genProfile is 'calc' and spectrum_type is 'laser', by default 6E15
    wavelength : float, optional
        The wavelength of the pulse in meters, only used when genProfile is 'calc' and spectrum_type is 'laser', by default 640E-9
    run_mode : bool, optional
        If False, show verbose output in console, by default False
    tVG_name : string, optional
        The name of the tVG file, by default 'tVG.txt'
    tj_name : string, optional
        The name of the tJ file, by default 'tj.dat'
    log_name : string, optional
        The name of the log file, by default 'log.txt'
    varFile : string, optional
        The name of the var file to create, by default 'none'. If 'none', no var file will be created and the varFile parameter will not be passed to ZimT.
    cmd_pars : list of dict, optional
        A list of dictionaries with the parameters to update in the simulation setup file, where each dictionary should have the format {'par': 'parameter_name', 'val': 'parameter_value'}, by default None
    turnoff_autoTidy : bool, optional
        Whether to turn off the autoTidy option in ZimT, by default True
    verbose : bool, optional
        Use verbose output, by default False
    threadsafe : bool, optional
        Whether to force run the simulation in a thread-safe way, by default False

    Returns
    -------
    int        
        0 if the simulation ran successfully, -1 if there was an error
    string     
        A message indicating the success or failure of the simulation
    '''
    
    # Create tVG for light pulse
    result, message = create_tVG_light_pulse(t_max, tVG_name, session_path, t_scale, t_step, t_pulse, FWHM)

    # Check if tVG file is created
    if result == 0:

        # Define mandatory options for ZimT:
        lp_args = [{'par':'dev_par_file','val':zimt_simulation_setup},
                        {'par':'tVGFile','val':tVG_name},
                        {'par':'tJFile','val':tj_name},
                        {'par':'varFile','val':varFile},
                        {'par':'logFile','val':log_name},
                        {'par':'genProfile','val':genProfile}]

        # Set the appropriate parameters for the specified genProfile
        if genProfile == 'calc':
            # Create spectrum if the option 'laser' has been specified, otherwise we use the spectrum as specified in the simulation setup
            if spectrum_type == 'laser':
                spectrum = create_spectrum(I, wavelength, FWHM, session_path, 'spectrum.txt', '../Data' )
                lp_args.append({'par':'spectrum', 'val':spectrum})
        elif genProfile != 'none': # genProfile must be userFile, thus this is the filename
            # Check if the file exists first
            if not os.path.isfile(os.path.join(session_path, genProfile)):
                msg = f'User supplied generation profile file not found: {os.path.join(session_path, genProfile)}'
                return -1, msg
        
        if turnoff_autoTidy:
            lp_args.append({'par':'autoTidy','val':'0'})
        
        if cmd_pars is not None:
            lp_args = update_cmd_pars(lp_args, cmd_pars)

        if threadsafe:
            result, message = utils_gen.run_simulation_filesafe('zimt', lp_args, session_path, run_mode, verbose=verbose)
        else:
            result, message = utils_gen.run_simulation('zimt', lp_args, session_path, run_mode, verbose=verbose)

    return result, message