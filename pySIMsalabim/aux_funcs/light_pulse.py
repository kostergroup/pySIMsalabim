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

def gaussian_pulse(time, t_pulse, FWHM):
    ''' Normalised Gaussian light pulse (peak = 1) evaluated on a time array. G is forced to 0 at the first time point (t=0).

    Parameters
    ----------
    time : array
        The time array
    t_pulse : float
        The center of the pulse in time
    FWHM : float
        The full width at half maximum (FWHM) of the pulse

    Returns
    -------
    array
        The generation profile (G_frac) for each time point
    '''
    sigma = FWHM/(2*np.sqrt(2*np.log(2)))
    G = np.exp(-((np.asarray(time) - t_pulse)/(sigma*np.sqrt(2)))**2) # Input Function (Gaussian Laser Pulse)
    G[0] = 0 # Force G=0 at t=0
    return G

def create_tVG_light_pulse(tmax, tVG_name, session_path, t_scale = 'lin', t_step = 1E-9, t_pulse = 40E-9, FWHM = 2E-9, freq = None, num_pulses = None, steps = 1000, G_frac = 1, steps_FWHM = 200):
    ''' Create a tVG file for a light pulse simulation, which contains the time (t), the external voltage (Vext), the generation profile (G_frac) and the Track state for each time step. 
    The generation profile is defined as a Gaussian pulse with the specified parameters.

    Two modes are available:

    - single pulse (num_pulses is None, default): one pulse, simulated from t=0 until tmax, using t_scale and t_step.
    - pulse train (num_pulses is not None): num_pulses pulses with a repetition frequency freq. Each period (1/freq) is
      resolved with a fine linear grid (FWHM/steps_FWHM) over the pulse followed by 'steps' logarithmically spaced points until the end of the period ('log' t_scale), 
      or with 'steps' linearly spaced points over the period ('lin' t_scale). The grid of one pulse is then repeated num_pulses times. tmax and t_step are ignored in this mode.
      The Track column is 1 at the end of the first period and 3 at the end of the following periods.

    Parameters
    ----------
    tmax : float
        The maximum time for the experiment (single pulse only)
    tVG_name : string
        The name of the tVG file to create, which will be saved in the session path
    session_path : string
        The path to the session folder, which is the working directory for the simulation
    t_scale : string, optional
        The time scale to use for the time array, which can be 'lin' for linear or 'log' for logarithmic, by default 'lin'
    t_step : float, optional
        The time step when using a linear scale and the shortest timestep using a logarithmic scale (single pulse only), by default 1E-9. Note: Make sure the time step is small enough to accurately describe the laser pulse, as defined by the FWHM.
    t_pulse : float, optional
        The center of the pulse in time (within each period for a pulse train). Make sure it is far enough from t=0 otherwise first part of pulse will be cut, 
        resulting in lower number of photons, by default 40E-9
    FWHM : float, optional
        The full width at half maximum (FWHM) of the pulse, by default 2E-9
    freq : float, optional
        The repetition frequency of the pulses in Hz, required when num_pulses is not None, by default None
    num_pulses : int, optional
        The number of pulses. If None, a single pulse is simulated until tmax, by default None
    steps : int, optional
        The number of time steps per pulse, i.e. per period 1/freq (pulse train only), by default 1000. For t_scale = 'lin' this is the total number of points per pulse. For t_scale = 'log' this is the number of points after the pulse; the pulse itself (from t=0 to t_pulse + 2*FWHM) is resolved with an additional fixed step of FWHM/steps_FWHM.
    G_frac : float, optional
        Scaling factor applied to the generation profile, by default 1
    steps_FWHM : int, optional
        The number of time steps per FWHM used to resolve the pulse for t_scale = 'log' (pulse train only), i.e. the time step over the pulse is FWHM/steps_FWHM, by default 200

    Returns
    -------
    int
        0 if the tVG file is created successfully, -1 if there is an error
    string
        A message indicating the success or failure of the tVG file creation
    '''

    if num_pulses is None:
        ########### Single pulse until tmax ###########
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

        G = gaussian_pulse(time, t_pulse, FWHM)
        Track = np.zeros(len(time),dtype=int) # Track state array, fixed to 0
        float_format = '%.4e'
    else:
        ########### Pulse train with frequency freq ###########
        if freq is None or freq <= 0:
            return -1, 'A positive freq must be specified when num_pulses is not None'
        if num_pulses < 1:
            return -1, 'num_pulses must be at least 1'

        t_period = 1 / freq # Duration of one period
        pulse_stop = t_pulse + FWHM*2 # End of the finely resolved part of the pulse
        if pulse_stop >= t_period:
            return -1, f'The pulse (t_pulse + 2*FWHM = {pulse_stop:.3e} s) does not fit in one period (1/freq = {t_period:.3e} s)'

        if t_scale == 'log':
            t_step_pulse = FWHM / steps_FWHM # steps_FWHM time steps per FWHM to accurately capture the shape of the pulse
            time_ = np.arange(t_step_pulse, pulse_stop, t_step_pulse)
            time_ = np.insert(time_, 0, 0) # Start at t=0
            # After the pulse, use a logarithmic time scale until the end of the period
            time_ = np.concatenate((time_[:-1], np.geomspace(time_[-1], t_period, steps)))
        else:
            time_ = np.linspace(0, t_period, steps)
            if t_pulse not in time_:
                # Make sure the pulse maximum is part of the time array
                time_ = np.sort(np.concatenate((time_, [t_pulse])))

        G_ = gaussian_pulse(time_, t_pulse, FWHM) # Generation profile of one period

        # Track is 1 at the end of the first period and 3 at the end of the following periods
        Track_first = np.zeros(len(time_), dtype=int)
        Track_first[-1] = 1
        Track_next = np.zeros(len(time_), dtype=int)
        Track_next[-1] = 3

        # Repeat the period num_pulses times, skipping t=0 of the repeated periods as it equals the end of the previous one
        time = np.concatenate([time_] + [time_[1:] + n*t_period for n in range(1, num_pulses)])
        G = np.concatenate([G_] + [G_[1:]] * (num_pulses - 1))
        Track = np.concatenate([Track_first] + [Track_next[1:]] * (num_pulses - 1))

        # Make sure the precision of the time column is sufficient to distinguish subsequent time values
        res = abs(np.log10(np.max(time)) - np.log10(FWHM/10)) 
        float_format = f'%.{int(np.ceil(res)+2)}e'

    V = np.zeros(len(time)) # Voltage array

    # Write to the tVG file
    tVG = pd.DataFrame({'t': time, 'Vext': V, 'G_frac': G*G_frac})
    tVG['Track'] = Track.astype(int) # Add the Track column separately, as it must be an integer and the other columns are floats

    # Drop duplicate time values, which can occur when the time step is smaller than the precision of the time values. SIMsalabim stops on duplicate times. Keep the first occurrence.
    tVG = tVG.drop_duplicates(subset=['t'], keep='first')

    tVG.to_csv(os.path.join(session_path,tVG_name), index=False, sep = ' ', float_format=float_format)

    msg = 'Success'
    retval = 0

    return retval, msg

def run_light_pulse_simu(zimt_simulation_setup, session_path, t_max, t_scale, t_step, t_pulse, FWHM, genProfile, spectrum_type = 'laser', I = 6E15, wavelength = 640E-9, run_mode=False, tVG_name = 'tVG.txt', tj_name = 'tj.dat',log_name = 'log.txt', varFile ='none', cmd_pars=None, turnoff_autoTidy = True, verbose = False, threadsafe = False, freq = None, num_pulses = None, steps = 1000, G_frac = 1, steps_FWHM = 200):
    ''' Run a ZimT simulation for a (gaussian) light pulse, or a train of light pulses when num_pulses is not None. The function will create the necessary tVG file, as well as take into account the type of generation profile specified by the user, and create the necessary spectrum file if needed. 
    Blocking layers (contactless device) are not handled here, see create_contactless_device in utils/device_parameters.py.
    
    Parameters
    ----------
    zimt_simulation_setup : string
        The name of the ZimT device parameters file, which should be located in the session path
    session_path : string
        The path to the session folder, which is the working directory for the simulation
    t_max : float
        The maximum time for the experiment (single pulse only)
    t_scale : string
        The time scale to use for the time array, which can be 'lin' for linear or 'log' for logarithmic
    t_step : float
        The time step for the tVG file (single pulse only)
    t_pulse : float
        The center of the pulse in time (within each period for a pulse train). Make sure it is far enough from t=0 otherwise first part of pulse will be cut, resulting in lower number of photons
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
    freq : float, optional
        The repetition frequency of the pulses in Hz, required when num_pulses is not None, by default None
    num_pulses : int, optional
        The number of pulses. If None, a single pulse is simulated until t_max, by default None
    steps : int, optional
        The number of time steps per pulse, i.e. per period 1/freq (pulse train only), by default 1000. For t_scale = 'lin' this is the total number of points per pulse. For t_scale = 'log' this is the number of points after the pulse; the pulse itself (from t=0 to t_pulse + 2*FWHM) is resolved with an additional fixed step of FWHM/steps_FWHM.
    G_frac : float, optional
        Scaling factor applied to the generation profile, by default 1
    steps_FWHM : int, optional
        The number of time steps per FWHM used to resolve the pulse for t_scale = 'log' (pulse train only), i.e. the time step over the pulse is FWHM/steps_FWHM, by default 200

    Returns
    -------
    int        
        0 if the simulation ran successfully, -1 if there was an error
    string     
        A message indicating the success or failure of the simulation
    '''
    
    # Create tVG for light pulse
    result, message = create_tVG_light_pulse(t_max, tVG_name, session_path, t_scale, t_step, t_pulse, FWHM, freq=freq, num_pulses=num_pulses, steps=steps, G_frac=G_frac, steps_FWHM=steps_FWHM)

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