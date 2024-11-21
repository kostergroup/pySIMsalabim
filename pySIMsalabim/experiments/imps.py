"""Perform Intensity-Modulated Photocurrent Spectroscopy (IMPS) simulations"""
######### Package Imports #########################################################################

import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import scipy.integrate
# import pySIMsalabim
## Import pySIMsalabim, if not successful, add the parent directory to the system path
try :
    import pySIMsalabim as sim
except ImportError:
    # Add the parent directory to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import pySIMsalabim as sim
from pySIMsalabim.utils import general as utils_gen
from pySIMsalabim.plots import plot_functions as utils_plot
from pySIMsalabim.utils.utils import *
from pySIMsalabim.utils.device_parameters import *

######### Function Definitions ####################################################################

def create_tVG_IMPS(V, G_frac, del_G, tVG_name, session_path, f_min, f_max, ini_timeFactor, timeFactor):
    """Create a tVG file for IMPS experiments.

    Parameters
    ----------
    V : float
        Voltage, the voltage is constant over the whole time range
    G_frac : float
        Fractional light intensity
    del_G : float
        Applied generation rate increase at t=0
    tVG_name : string
        Name of the tVG file
    session_path : string
        Path of the simulation folder for this session
    f_min : float
        Minimum frequency
    f_max : float
        Maximum frequency
    ini_timeFactor : float
        Constant defining the size of the initial timestep
    timeFactor : float
        Exponential increase of the timestep, to reduce the amount of timepoints necessary. Use values close to 1.

    Returns
    -------
    string
        A message to indicate the result of the process
    """
    
    time = 0
    del_t = ini_timeFactor/f_max

    # Starting line of the tVG file: header + datapoints at time=0. Set the correct header
    tVG_lines = 't Vext G_frac\n' + f'{time:.3e} {V} {G_frac:.3e}\n'

    # Make the other lines in the tVG file
    while time < 1/f_min: #max time: 1/f_min is enough!
        time = time+del_t
        tVG_lines += f'{time:.3e} {V} {G_frac+del_G:.3e}\n'
        del_t = del_t * timeFactor # At first, we keep delt constant to its minimum values

    # Export tVG file to ZimT folder
    with open(os.path.join(session_path,tVG_name), 'w') as file:
        file.write(tVG_lines)

    # tVG file is created, message a success
    msg = 'Success'
    retval = 0
    return retval, msg

# def read_tj_file(session_path, tj_file_name='tj.dat'):
#     """ Read relevant parameters for admittance of the tj file

#     Parameters
#     ----------
#     session_path : string
#         Path of the simulation folder for this session
#     data_tj : dataFrame
#         Pandas dataFrame containing the tj output file from ZimT

#     Returns
#     -------
#     DataFrame
#         Pandas dataFrame of the tj_file containing the time, current density, numerical error in the current density and the photogenerated current density
#     """

#     data = pd.read_csv(os.path.join(session_path,tj_file_name), sep=r'\s+')

#     return data

# def get_integral_bounds(data, f_min=1e-2, f_max=1e6, f_steps=20):
#     """ Determine integral bounds in the time domain, used to compute the conductance and capacitance

#     Parameters
#     ----------
#     data : dataFrame
#         Pandas dataFrame containing the time, current density, numerical error in the current density and the photogenerated current density of the tj_file
#     f_min : float
#         Minimum frequency
#     f_max : float
#         Maximum frequency
#     f_steps : float
#         Frequency steps

#     Returns
#     -------
#     list
#         List of array indices that will be used in the plotting
#     """

#     # Total number of time points
#     numTimePoints = len(data['t'])

#     # Check which time index corresponds to 1/fmax. We call this istart:
#     istart = -1
#     for i in range(numTimePoints):
#         if math.isclose(data['t'][i], 1/f_max, rel_tol = 2/f_steps): #note: don't use == to compare 2 floating points!
#             istart = i

#     # Starting time point could not be found
#     if istart == -1:
#         msg = 'Could not find a time that corresponds to the highest frequency.'
#         return -1, msg
    
#     # print('Found istart: ', istart)

#     # ifin: last index we should plot, corresponds to time = 1/f_min:
#     ifin = numTimePoints - 1

#     # isToPlot starts with istart:
#     isToPlot = [istart]

#     PlotRatio = max(1, round( (ifin-istart)/(math.log10(f_max/f_min) * f_steps)))

#     # Incorrect plot ratio
#     if PlotRatio < 1:
#         msg = 'PlotRatio smaller than 1. It should at least be 1'
#         return -1, msg

#     # Then add the other indices:
#     for i in range(istart+1, ifin-1):
#         if (i-istart) % PlotRatio == 0: # note: % is python's modulo operator.
#             isToPlot.append(i) # add the index to our array

#     # Also include the last index:
#     isToPlot.append(ifin)

#     # Integral bounds have been determined, return the array with indices and a success message
#     msg = 'Success'
#     return isToPlot, msg

def calc_IMPS_limit_time(I, errI, time, imax):
    """Fourier Decomposition formula which computes the admittance at frequency freq (Hz) and its complex error
    Based on S.E. Laux, IEEE Trans. Electron Dev. 32 (10), 2028 (1985), eq. 5a, 5b
    We integrate from 0 to time[imax] at frequency 1/time[imax]

    Parameters
    ----------
    I : np.array
        Array of currents
    errI : np.array
        Numerical error in calculated currents (output of ZimT)
    time : np.array
        Array with all time positions, from 0 to tmax
    imax : integer
        Index of the last timestep/first frequency for which the integrals are calculated

    Returns
    -------
    float
        Frequency belonging to Y(f)
    complex number
        Admittance at frequency f: Y(f)
    complex number
        Numerical error in calculated admittance Y(f)
    """

    freq=1/time[imax] #we obtain the frequency from the time array
    Iinf = I[imax] # I at infinite time, i.e. the last one we have.
	
    #prepare array for integrants:
    int1 = np.empty(imax)
    int2 = np.empty(imax)
    int3 = np.empty(imax)
    int4 = np.empty(imax)
	
    #now we use only part of the time array:
    timeLim = time[0:imax]
	
    for i in range(imax) :
        sinfac = math.sin(2*math.pi*freq*timeLim[i])
        cosfac = math.cos(2*math.pi*freq*timeLim[i])
        int1[i] = sinfac*(I[i] - Iinf)
        int2[i] = cosfac*(I[i] - Iinf)	
        int3[i] = sinfac*(I[i] + errI[i] - Iinf - errI[imax])
        int4[i] = cosfac*(I[i] + errI[i] - Iinf - errI[imax])	

    #now compute the conductance and capacitance:
    cond = (Iinf - I[0] + 2*math.pi*freq*scipy.integrate.trapezoid(int1, timeLim))
    cap = scipy.integrate.trapezoid(int2, timeLim)
    #convert to admittance:
    Y = cond + 2J*math.pi*freq*cap
	
    #and again, but now with the error added to the current:	
    condErr = (Iinf + errI[imax] - I[0] - errI[0] + 2*math.pi*freq*scipy.integrate.trapezoid(int3, timeLim))
    capErr = scipy.integrate.trapezoid(int4, timeLim)
    #convert to admittance:
    Y2 = condErr + 2J*math.pi*freq*capErr
    
    #error is the difference between Y and Y2:
    errY = Y - Y2
    
    #now return complex admittance, its error and the corresponding frequency:	
    return freq, Y, errY

def calc_IMPS(data, isToPlot):
    """ Calculate the admittance over the frequency range
    
    Parameters
    ----------
    data : dataFrame
        Pandas dataFrame containing the time, current density, numerical error in the current density and the photogenerated current density of the tj_file
    isToPlot : list
        List of array indices that will be used in the plotting

    Returns
    -------
    np.array
        Array of frequencies
    np.array
        Array of the real component of admittance
    np.array
        Array of the imaginary component of admittance
    np.array
        Array of complex error
    """
    # init the arrays for the admittance and its error:
    numFreqPoints = len(isToPlot)
    freq = np.empty(numFreqPoints)
    ReY = np.empty(numFreqPoints)
    ImY = np.empty(numFreqPoints)
    Y = [1 + 1J] * numFreqPoints
    errY = [1 + 1J] * numFreqPoints

    for i in range(numFreqPoints):
        imax=isToPlot[i]
        freq[i], Y[i], errY[i] = calc_IMPS_limit_time(data['Jext'], data['errJ'], data['t'], imax)
        # we are only interested in the absolute value of the real and imag components:
        ReY[i] =(Y[i].real)
        ImY[i] = (Y[i].imag)
    
    return freq, ReY, ImY, errY

def store_IMPS_data(session_path, freq, ReY, ImY, errY, output_file):
    """ Save the frequency, real & imaginary part of the admittance & its error in one file called freqY.dat
    
    Parameters
    ----------
    session_path : string
        working directory for zimt
    freq : np.array
        Array of frequencies
    ReY : np.array
        Array of the real component of admittance
    ImY : np.array
        Array of the imaginary component of admittance
    errY : np.array
        Array of complex error in admittance
    """

    with open(os.path.join(session_path,output_file), 'w') as file:
        file.write('freq ReY ImY ReErrY ImErrY' + '\n')
        for i in range(len(freq)):
            file.write(f'{freq[i]:.6e} {ReY[i]:.6e} {ImY[i]:.6e} {abs(errY[i].real):.6e} {abs(errY[i].imag):.6e}' + '\n')

    # print('The data of the IMPS graphs is written to ' + output_file)

def get_IMPS(data, f_min, f_max, f_steps, session_path, output_file):
    """Calculate the IMPS from the simulation result

    Parameters
    ----------
    data : DataFrame
        DataFrame with the simulation results (tj.dat) file
    f_min : float
        Minimum frequency
    f_max : float
        Maximum frequency
    f_steps : float
        Frequency step
    session_path : string
        working directory for zimt
    output_file : string
        name of the file where the IMPS data is stored

    Returns
    -------
    integer,string
        returns -1 (failed) or 1 (success), including a message
    """
    isToPlot, msg = get_integral_bounds(data, f_min, f_max, f_steps)

    if isToPlot != -1:
        # Integral bounds have been determined, continue to calculate the IMPS
        freq, ReY, ImY, errY = calc_IMPS(data, isToPlot)

        # Write IMPS results to a file
        store_IMPS_data(session_path, freq, ReY, ImY, errY, output_file)

        msg = 'Success'
        return 0, msg
    else:
        # Failed to determine integral bounds, exit with the error message
        return -1, msg

def IMPS_plot(session_path, output_file, xscale='log', yscale='log', plot_type = plt.plot):
    """ Plot the real and imaginary part of the admittance against frequency

    Parameters
    ----------
    session_path : string
        working directory for zimt
    xscale : string
        Scale of the x-axis. E.g linear or log
    yscale_ax1 : string
        Scale of the left y-axis. E.g linear or log
    yscale_ax2 : string
        Scale of the right y-axis. E.g linear or log
    """
    # Read the data from freqY-file
    data_freqY = pd.read_csv(os.path.join(session_path,output_file), sep=r'\s+')

    # Flip the ImY data to the first quadrant
    # data["ImY"] = data["ImY"]*-1*-1

    # Define the plot parameters, two y axis
    pars_imps = {'ImY' : '-Im Y [A/m$^2$]' }
    selected = ['ImY']
    par_x = 'freq'
    xlabel = 'frequency [Hz]'
    ylabel = 'Im Y'
    title = 'Computed IMPS'
    fig, ax = plt.subplots()
    utils_plot.plot_result(data_freqY, pars_imps, selected, par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type)

    plt.show()

def ColeCole_plot(session_path, output_file, xscale='linear', yscale='linear', plot_type = plt.errorbar):
    """ Plot the Cole-Cole plot with the real and imaginary part of the admittance against frequency

    Parameters
    ----------
    session_path : string
        working directory for zimt
    output_file : string
        Filename where the admittance data is stored
    xscale : string
        Scale of the x-axis. E.g linear or log
    yscale : string
        Scale of the y-axis. E.g linear or log
    plot_type : matplotlib.pyplot
        Type of plot to display
    """
    # Read the data from freqY-file
    data = pd.read_csv(os.path.join(session_path,output_file), sep=r'\s+')
    
    fig, ax = plt.subplots()
    pars_nyq = {'ImY' : '-Im Y [A/m$^2$]'}
    par_x_nyq = 'ReY'
    par_weight_nyq = 'freq'
    xlabel_nyq = 'Re Y [A/m$^2$]'
    ylabel_nyq = '-Im Y [A/m$^2$]'
    weightlabel_nyq = 'frequency [Hz]'
    weight_norm_nyq = 'log'
    title_nyq = 'Cole-Cole plot'

    # Plot the Cole-Cole plot with or without errorbars
    if plot_type == plt.errorbar:
        ax = utils_plot.plot_result(data, pars_nyq, list(pars_nyq.keys()), par_x_nyq, xlabel_nyq, ylabel_nyq, xscale, yscale, title_nyq, ax, plot_type, 
                                            [], data['ImErrY'], legend=False)
    else:
        ax = utils_plot.plot_result(data, pars_nyq, list(pars_nyq.keys()), par_x_nyq, xlabel_nyq, ylabel_nyq, xscale, yscale, title_nyq, ax, plot_type, legend=False)

    plt.show()



def plot_IMPS(session_path, output_file='freqY.dat'):
    """Plot admittance of IMPS

    Parameters
    ----------
    session_path : string
        working directory for zimt
    """
    # IMPS plot
    IMPS_plot(session_path,output_file)

    # Cole-Cole plot
    ColeCole_plot(session_path,output_file)

def run_IMPS_simu(zimt_device_parameters, session_path, f_min, f_max, f_steps, V, G_frac, GStep = 0.05, run_mode=False, tVG_name = 'tVG.txt', output_file = 'freqY.dat', tj_name = 'tj.dat',varFile ='none', ini_timeFactor=1e-3, timeFactor=1.02, **kwargs):
    """Create a tVG file and run ZimT with admittance device parameters

    Parameters
    ----------
    zimt_device_parameters : string
        Name of the zimt device parameters file
    session_path : string
        Path of the simulation folder for this session
    f_min : float
        Minimum frequency
    f_max : float
        Maximum frequency
    f_steps : float
        Frequency step
    V : float
        Voltage, the voltage is constant over the whole time range
    G_frac : float
        Fractional light intensity
    GStep : float, optional
        Applied generation rate increase at t=0, by default 0.05
    run_mode : bool, optional
        Indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default False
    tVG_name : string, optional
        Name of the tVG file, by default tVG.txt
    output_file : string, optional
        Name of the file where the admittance data is stored, by default freqY.dat
    tj_name : string, optional
        Name of the tj file where the admittance data is stored, by default tj.dat
    varFile : string, optional
        Name of the var file, by default 'none'
    ini_timeFactor : float, optional
        Constant defining the size of the initial timestep, by default 1e-3
    timeFactor : float, optional
        Exponential increase of the timestep, to reduce the amount of timepoints necessary. Use values close to 1., by default 1.02
       
    Returns
    -------
    CompletedProcess
        Output object of with returncode and console output of the simulation
    string
        Return message to display on the UI, for both success and failed
    """
    UUID = kwargs.get('UUID', '') # Check if the user wants to add a UUID to the tj file name
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

    # Update the file names with the UUID
    if UUID != '':
        dum_str = f'_{UUID}'
    else:
        dum_str = ''

    # Update the filenames with the UUID
    tj_name = os.path.join(session_path, tj_name)
    output_file = os.path.join(session_path, output_file)
    tVG_name = os.path.join(session_path, tVG_name)
    if UUID != '':
        tj_file_name_base, tj_file_name_ext = os.path.splitext(tj_name)
        tj_name = tj_file_name_base + dum_str + tj_file_name_ext 
        tVG_name_base, tVG_name_ext = os.path.splitext(tVG_name)
        tVG_name = tVG_name_base + dum_str + tVG_name_ext
        output_file_base, output_file_ext = os.path.splitext(output_file)
        output_file = output_file_base + dum_str + output_file_ext
        if varFile != 'none':
            var_file_base, var_file_ext = os.path.splitext(varFile)
            varFile = var_file_base + dum_str + var_file_ext
            varFile = os.path.join(session_path,varFile)
    # varFile = 'none' # we don't use a var file for this simulation

    # Create tVG
    result, message = create_tVG_IMPS(V, G_frac, GStep, tVG_name, session_path, f_min, f_max, ini_timeFactor, timeFactor)

    # Check if tVG file is created
    if result == 0:
        # Define mandatory options for ZimT to run well with IMPS:
        IMPS_args = [{'par':'dev_par_file','val':zimt_device_parameters},
                        {'par':'tVGFile','val':tVG_name},
                        {'par':'limitDigits','val':'0'},
                        {'par':'currDiffInt','val':'2'},
                        {'par':'tJFile','val':tj_name},
                        {'par':'varFile','val':varFile},
                        {'par':'logFile','val':'log'+dum_str+'.txt'}]
        
        if turnoff_autoTidy:
            IMPS_args.append({'par':'autoTidy','val':'0'})
        
        if cmd_pars is not None:
            IMPS_args = update_cmd_pars(IMPS_args, cmd_pars)

        if threadsafe:
            result, message = utils_gen.run_simulation_filesafe('zimt', IMPS_args, session_path, run_mode)
        else:
            result, message = utils_gen.run_simulation('zimt', IMPS_args, session_path, run_mode)

        if result.returncode == 0 or result.returncode == 95:
            data = read_tj_file(session_path, tj_file_name=tj_name)

            result, message = get_IMPS(data, f_min, f_max, f_steps, session_path, output_file)
            return result, message

        else:
            return result.returncode, message

    return result, message

## Running the function as a standalone script
if __name__ == "__main__":
    # IMPS input parameters
    f_min = 1e-2 # org 1e-2
    f_max = 5e6# org 1e6
    f_steps = 30 # org 30
    V_0 = 1.0 # Float or 'oc' for the open-circuit voltage
    G_frac = 1
    fac_G = 5e-2 # org 2e-1, use around 0.2 for IMPS

    # Define folder and file paths
    session_path = os.path.join('../../','SIMsalabim','ZimT')

    zimt_device_parameters = 'simulation_setup.txt'

    tVG_name = 'tVG.txt'
    tj_name = 'tj.dat'
    output_name = 'freqZ.dat'

    # UUID = str(uuid.uuid4()) # Add a UUID to the simulation
    UUID = ''

    # Not user input
    ini_timeFactor = 1e-3 # Initial timestep factor, org 1e-3
    timeFactor = 1.02 # Increase in timestep every step to reduce the amount of datapoints necessary, use value close to 1 as this is best! Org 1.02
    run_mode = False  # If False, show verbose output in console

    ############## Command line arguments  ##############
    ## Notes
    ## - The command line arguments are optional and can be provided in any order
    ## - Each command line argument must be provided in the format -par_name value
    ## - Possible arguments include all SIMsalabim parameters and IMPS specific parameters as listed before
    ## - Special arguments
    ##   - sp : string
    ##     - The session path, i.e. the working directory for the simulation
    ##   - simsetup : string
    ##     - The name of the zimt simulation setup parameters file
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
        'f_min': lambda val: {'f_min': float(val)},
        'f_max': lambda val: {'f_max': float(val)},
        'f_steps': lambda val: {'f_steps': int(val)},
        'V_0': lambda val: {'V_0': float(val)},
        'G_frac': lambda val: {'G_frac': float(val)},
        'fac_G': lambda val: {'fac_G': float(val)},
        'tVG_name': lambda val: {'tVG_name': val},
        'tj_name': lambda val: {'tj_name': val},
        'out_name': lambda val: {'output_name': val},
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


    # Run IMPS spectroscopy
    GStep = G_frac*fac_G

    # result, message = run_IMPS_simu(zimt_device_parameters, f_min, f_max, f_steps, V, G_frac, GStep, tVG_name=tVG_name,  session_path= session_path, run_mode=False, ini_timeFactor=ini_timeFactor, timeFactor=timeFactor)
    result, message = run_IMPS_simu(zimt_device_parameters,session_path, f_min, f_max, f_steps, V_0, G_frac, GStep, run_mode=False, tVG_name=tVG_name, 
                                        output_file = output_name, tj_name = tj_name, ini_timeFactor=ini_timeFactor, timeFactor=timeFactor, cmd_pars=cmd_pars, UUID=UUID)

    # Make the IMPS plots
    if result == 0 or result == 95:
        plot_IMPS(session_path, os.path.basename(output_name))
    else:
        print(message)
        sys.exit(1)

