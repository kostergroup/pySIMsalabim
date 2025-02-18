"""Perform capacitance simulations"""
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

def create_tVG_CV(V_0, V_max, del_V, V_step, G_frac, tVG_name, session_path, freq, ini_timeFactor, timeFactor):
    """Create a tVG file for capacitance experiment. 

    Parameters
    ----------
    V_0 : float
        Initial voltage
    V_max : float
        Maximum voltage
    del_V : float
        Voltage step that is applied directly after t=0
    V_step : float
        Voltage difference, determines at which voltages the capacitance is determined
    G_frac : float
        Fractional light intensity
    tVG_name : string
        Name of the tVG file
    session_path : string
        Path of the simulation folder for this session
    freq : float
        Frequency at which the capacitance-voltage measurement is performed
    ini_timeFactor : float
        Constant defining the size of the initial timestep
    timeFactor : float
        Exponential increase of the timestep, to reduce the amount of timepoints necessary. Use values close to 1.

    Returns
    -------
    string
        A message to indicate the result of the process
    """        

    # Starting line of the tVG file: header + datapoints at time=0. Set the correct header
    tVG_lines = 't Vext G_frac\n'

    # Loop until V reaches V_max, in other words go from Vmin to Vmax with in V_step steps. Add some extra margin on the Vmax to prevent missing the last voltage point due to numerical accuracy.
    while V_0 <= V_max + V_max*1E-5:
        time = 0
        del_t = ini_timeFactor/freq
        tVG_lines += f'{time:.3e} {V_0:.3e} {G_frac:.3e}\n'
        
        # Make the other lines in the tVG file
        while time < 1/freq: #max time: 1/f_min is enough!
            time += del_t
            del_t = del_t * timeFactor
            tVG_lines += f'{time:.3e} {V_0+del_V:.3e} {G_frac:.3e}\n'
    
        V_0 += V_step

    # Write the tVG lines to the tVG file
    with open(os.path.join(session_path,tVG_name), 'w') as file:
        file.write(tVG_lines)

    # tVG file is created, message a success
    msg = 'Success'
    retval = 0

    return retval, msg

def create_tVG_CV_Rseries(Vint, del_V, G_frac, tVG_name, session_path, freq, ini_timeFactor, timeFactor):
    """Create a tVG file for capacitance experiment. 

    Parameters
    ----------
    V_int : float
        Adjusted internal voltage to correct for series resistance later
    del_V : float
        Voltage step that is applied directly after t=0
    G_frac : float
        Fractional light intensity
    tVG_name : string
        Name of the tVG file
    session_path : string
        Path of the simulation folder for this session
    freq : float
        Frequency at which the capacitance-voltage measurement is performed
    ini_timeFactor : float
        Constant defining the size of the initial timestep
    timeFactor : float
        Exponential increase of the timestep, to reduce the amount of timepoints necessary. Use values close to 1.

    Returns
    -------
    string
        A message to indicate the result of the process
    """        

    # Starting line of the tVG file: header + datapoints at time=0. Set the correct header
    tVG_lines = 't Vext G_frac\n'

    # Loop until V reaches V_max, in other words go from Vmin to Vmax with in V_step steps. Add some extra margin on the Vmax to prevent missing the last voltage point due to numerical accuracy.
    for V_0 in Vint:
        time = 0
        del_t = ini_timeFactor/freq
        tVG_lines += f'{time:.3e} {V_0:.3e} {G_frac:.3e}\n'
        
        # Make the other lines in the tVG file
        while time < 1/freq:
            time += del_t
            del_t = del_t * timeFactor
            tVG_lines += f'{time:.3e} {V_0+del_V:.3e} {G_frac:.3e}\n'

    # while V_0 <= V_max + V_max*1E-5:
    #     time = 0
    #     del_t = ini_timeFactor/freq
    #     tVG_lines += f'{time:.3e} {V_0:.3e} {G_frac:.3e}\n'
        
    #     # Make the other lines in the tVG file
    #     while time < 1/freq: #max time: 1/f_min is enough!
    #         time += del_t
    #         del_t = del_t * timeFactor
    #         tVG_lines += f'{time:.3e} {V_0+del_V:.3e} {G_frac:.3e}\n'
    
    #     V_0 += V_step

    # Write the tVG lines to the tVG file
    with open(os.path.join(session_path,tVG_name), 'w') as file:
        file.write(tVG_lines)

    # tVG file is created, message a success
    msg = 'Success'
    retval = 0

    return retval, msg

def create_tVG_SS_CV(V_min, V_max,Vstep, G_frac, tVG_name, session_path):
    """ Creates the tVG file for the steady state simulation with only t 0 and V_0

    Parameters
    ----------
    V_min : float 
        Initial voltage
    V_max : float
        Maximum voltage
    del_V : float
        Voltage step that is applied after t=0
    G_frac : float
        Fractional light intensity
    tVG_name : string
        Name of the tVG file
    session_path : string
        Path of the simulation folder for this session

    Returns
    -------
    string
        A message to indicate the result of the process

    
    """    

    # Starting line of the tVG file: header + datapoints at time=0. Set the correct header
    tVG_lines = 't Vext G_frac\n' #+ f'{0} {V_0} {G_frac:.3e}\n'
    V_0 =V_min
    while V_0 <= V_max + V_max*1E-5:
        time = 0
        tVG_lines += f'{time:.3e} {V_0:.3e} {G_frac:.3e}\n'
        V_0 += Vstep

    # Write the tVG lines to the tVG file
    with open(os.path.join(session_path,tVG_name), 'w') as file:
        file.write(tVG_lines)

    # tVG file is created, message a success
    msg = 'Success'
    retval = 0

    return retval, msg

def calc_capacitance_forOneVoltage(I, errI, time, VStep, freq):
    """Fourier Decomposition formula which computes the capacitance at frequency freq (Hz) and its complex error
    Based on S.E. Laux, IEEE Trans. Electron Dev. 32 (10), 2028 (1985), eq. 5b
    We integrate from 0 to time[imax] at frequency 1/time[imax]

    Parameters
    ----------
    I : np.array
        Array of currents
    errI : np.array
        Numerical error in calculated currents (output of ZimT)
    time : np.array
        Array with all time positions, from 0 to tmax
    VStep : float
        Voltage step
    imax : integer
        Index of the last timestep/first frequency for which the integrals are calculated

    Returns
    -------
    float
        Capacitance at frequency f: C(f)
    float
        Numerical error in calculated capacitance
    """

    imax = len(I)
    Iinf = I[imax-1] # I at infinite time, i.e. the last one we have.
	
    #prepare array for integrants:
    int2 = np.empty(imax)
    int4 = np.empty(imax)
	
    for i in range(imax):
        cosfac = math.cos(2*math.pi*freq*time[i])
        int2[i] = cosfac*(I[i] - Iinf)	
        int4[i] = cosfac*(I[i] + errI[i] - Iinf - errI[imax-1])	

    #Compute the capacitance:
    cap = scipy.integrate.trapezoid(int2, time)/VStep
	
    #and again, but now with the error added to the current:	
    capErr = scipy.integrate.trapezoid(int4, time)/VStep

    # error is the difference between cap and capPlusErr:
    errC = abs( cap - capErr )

    #now return capacitance, its error and the corresponding frequency:	
    return cap, errC

def calc_capacitance(data, del_V, freq):
    """ Calculate the capacitance over the time range
    
    Parameters
    ----------
    data : dataFrame
        Pandas dataFrame containing the time, voltage, current density and numerical error in the current density of the tj_file
    del_V : float
        Voltage step that is applied directly after t=0
    freq : float
        Frequency at which the capacitance-voltage measurement is performed

    Returns
    -------
    np.array
        Array of the capacitance
    np.array
        Array of the capacitance error
    """
       
    idx_time_zero = data.index[data['t'] == 0] # Find all indices where time is equal to 0
    amountOfVoltagePoints = len(idx_time_zero)
    
    # Prepare array for capacitance & its error:
    cap = np.empty(amountOfVoltagePoints)
    errC = np.empty(amountOfVoltagePoints)

    # Get the capacitance for each voltage step by taking the Fourier Transform over the t & I arrays
    for i in range(amountOfVoltagePoints-1):
        start_idx = idx_time_zero[i]
        end_idx = idx_time_zero[i+1]-1
                
        Jext_subarray = np.array( data.loc[start_idx:end_idx, 'Jext'] )
        errJ_subarray = np.array( data.loc[start_idx:end_idx, 'errJ'] )
        time_subarray = np.array( data.loc[start_idx:end_idx, 't'] )
        
        cap[i], errC[i] = calc_capacitance_forOneVoltage(Jext_subarray, errJ_subarray, time_subarray, del_V, freq)
        
    # Handle the last index from t=0 to tmax_n
    Jext_subarray = np.array( data.loc[idx_time_zero[-1]:, 'Jext'] )
    errJ_subarray = np.array( data.loc[idx_time_zero[-1]:, 'errJ'] )
    time_subarray = np.array( data.loc[idx_time_zero[-1]:, 't'] )
    cap[-1], errC[-1] = calc_capacitance_forOneVoltage(Jext_subarray, errJ_subarray, time_subarray, del_V, freq)
    
    return cap, errC

def calc_impedance_limit_time(I, errI, time, VStep, imax):
    """Fourier Decomposition formula which computes the impedance at frequency freq (Hz) and its complex error
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
    VStep : float
        Voltage step
    imax : integer
        Index of the last timestep/first frequency for which the integrals are calculated

    Returns
    -------
    float
        Frequency belonging to Z(f)
    complex number
        Impedance at frequency f: Z(f)
    complex number
        Numerical error in calculated impedance Z(f)
    """

    freq=1/time[-1] #we obtain the frequency from the time array
    Iinf = I[-1] # I at infinite time, i.e. the last one we have.
    imax = len(I)
    #prepare array for integrants:
    int1 = np.empty(imax)
    int2 = np.empty(imax)
    int3 = np.empty(imax)
    int4 = np.empty(imax)
	
    #now we use only part of the time array:
    timeLim = time
    for i,t in enumerate(time) :
        sinfac = math.sin(2*math.pi*freq*timeLim[i])
        cosfac = math.cos(2*math.pi*freq*timeLim[i])
        int1[i] = sinfac*(I[i] - Iinf)
        int2[i] = cosfac*(I[i] - Iinf)	
        int3[i] = sinfac*(I[i] + errI[i] - Iinf - errI[-1])
        int4[i] = cosfac*(I[i] + errI[i] - Iinf - errI[-1])	

    #now compute the conductance and capacitance:
    cond = (Iinf - I[0] + 2*math.pi*freq*scipy.integrate.trapezoid(int1, timeLim))/VStep
    cap = scipy.integrate.trapezoid(int2, timeLim)/VStep
    #convert to impedance:
    Z = 1/(cond + 2J*math.pi*freq*cap)
	
    #and again, but now with the error added to the current:	
    condErr = (Iinf + errI[-1] - I[0] - errI[0] + 2*math.pi*freq*scipy.integrate.trapezoid(int3, timeLim))/VStep
    capErr = scipy.integrate.trapezoid(int4, timeLim)/VStep
    #convert to impedance:
    Z2 = 1/(condErr + 2J*math.pi*freq*capErr)
    
    #error is the difference between Z and Z2:
    errZ = Z - Z2
    
    #now return complex impedance, its error and the corresponding frequency:	
    return freq, Z, errZ

def calc_impedance_CV(data, del_V, isToPlot,session_path,zimt_device_parameters,Rseries=0,Rshunt=-1e3):
    """ Calculate the impedance over the frequency range
    
    Parameters
    ----------
    data : dataFrame
        Pandas dataFrame containing the time, voltage, current density and numerical error in the current density of the tj_file
    del_V : float
        Voltage step
    isToPlot : list
        List of array indices that will be used in the plotting

    Returns
    -------
    np.array
        Array of frequencies
    np.array
        Array of the real component of impedance
    np.array
        Array of the imaginary component of impedance
    np.array
        Array of complex error
    np.array
        Array of capacitance	
    np.array
        Array of conductance
    np.array
        Array of error in capacitance	
    np.array
        Array of error in conductance
    """
    # init the arrays for the impedance and its error:
    numFreqPoints = len(isToPlot)
    # V = np.empty(numFreqPoints)
    ReZ = np.empty(numFreqPoints)
    ImZ = np.empty(numFreqPoints)
    Z = [1 + 1J] * numFreqPoints
    errZ = [1 + 1J] * numFreqPoints
    C = np.empty(numFreqPoints)
    G = np.empty(numFreqPoints)
    errC = np.empty(numFreqPoints)
    errG = np.empty(numFreqPoints)


    # We need to know the series and shunt resistance to calculate the impedance correctly later on
    # dev_val,lyrs_dum = load_device_parameters(session_path, zimt_device_parameters)
    # for i in dev_val[zimt_device_parameters]:
    #     if i[0] == 'Contacts':
    #         contacts = i
    #         break

    # for i in contacts[1:]:
    #     if i[1] == 'R_series':
    #         Rseries = float(i[2])
    #     elif i[1] == 'R_shunt':
    #         Rshunt = float(i[2])

    for i in range(numFreqPoints):
        imax=isToPlot[i]
        if i == 0:
            data_dum = data.loc[0:imax]
        else:
            data_dum = data.loc[isToPlot[i-1]+1:imax]
        
        freq, Z[i], errZ[i] = calc_impedance_limit_time(np.asarray(data_dum['Jext']), np.asarray(data_dum['errJ']), np.asarray(data_dum['t']), del_V, imax)

        if Rseries > 0 and Rshunt > 0:
            # Correct the impedance for the series resistance
            Z[i] = Rseries + 1/(1/Z[i] + 1/Rshunt)
        elif Rseries > 0 and Rshunt < 0:
            # Correct the impedance for the series resistance
            Z[i] = Rseries + Z[i]
        elif Rshunt > 0 and Rseries <= 0:
            # Correct the impedance for the shunt resistance
            invZ = 1/Z[i]
            Z[i] = 1/(invZ + 1/Rshunt)

        invZ = 1/Z[i]
        
        # we are only interested in the absolute value of the real and imag components:
        ReZ[i] = Z[i].real
        ImZ[i] = Z[i].imag
        C[i] = 1/(2*math.pi*freq)*invZ.imag
        G[i] = invZ.real

        errC[i] = abs(1/(2*math.pi*freq)*(invZ.imag**2)*errZ[i].real)
        errG[i] = abs((invZ.real**2)*errZ[i].imag)
    
    return ReZ, ImZ, errZ, C, G, errC, errG

def store_capacitance_data(session_path, V, cap, errC, output_file='CapVol.dat'):
    """ Save the capacitance & its error in one file called CapVol.dat
    
    Parameters
    ----------
    session_path : string
        working directory for zimt
    V : np.array
        Array of frequencies
    cap : np.array
        Array of the capacitance
    errC : np.array
        Array of the capacitance error
    output_file : string
        Filename where the capacitance data is stored
    """

    with open(os.path.join(session_path,output_file), 'w') as file:
        file.write('V C errC' + '\n')
        for i in range(len(V)):
            file.write(f'{V[i]:.6e} {cap[i]:.6e} {errC[i]:.6e}' + '\n')

def get_capacitance(data, freq, V_0, V_max, del_V, V_step, session_path, zimt_device_parameters, output_file):
    """Calculate the capacitance from the simulation result

    Parameters
    ----------
    data : DataFrame
        DataFrame with the simulation results (tj.dat) file
    freq : float
        Frequency at which the capacitance-voltage measurement is performed
    V_0 : float
        Initial voltage
    V_max : float
        Maximum voltage
    del_V : float
        Voltage step that is applied directly after t=0
    V_step : float
        Voltage difference, determines at which voltages the capacitance is determined
    session_path : string
        working directory for zimt
    output_file : string
        Filename where the capacitance data is stored

    Returns
    -------
    integer,string
        returns -1 (failed) or 1 (success), including a message
    """  
    # get indexes of the time points where the voltage changes
    isToPlot = data.index[data['t'] == 0]
    # do -1 to get the last index
    isToPlot = isToPlot - 1
    # remove the first index, because we start at t=0
    isToPlot = isToPlot[1:]
    # add the last index to the end
    isToPlot = np.append(isToPlot, len(data['t'])-1)
    V = np.linspace(V_0, V_max, num=math.ceil((V_max-V_0)/V_step)+1, endpoint=True)

    ReZ, ImZ, errZ, C, G, errC, errG = calc_impedance_CV(data, del_V, isToPlot,session_path, zimt_device_parameters)

    # Write the capacitance results to a file
    store_capacitance_data(session_path, V, C, errC, output_file)

    # If the capacitance is calculated, message a success
    msg = 'Success'
    retval = 0
    
    return retval, msg

def cap_plot(session_path, output_file, xscale='linear', yscale='linear', plot_type = plt.errorbar):
    """ Plot the capacitance against voltage

    Parameters
    ----------
    session_path : string
        working directory for zimt
    output_file : string
        Filename where the capacitance data is stored
    xscale : string
        Scale of the x-axis. E.g linear or log
    yscale : string
        Scale of the y-axis. E.g linear or log
    plot_type : matplotlib.pyplot
        Type of plot to display
    """
    # Read the data from CapVol-file
    data = pd.read_csv(os.path.join(session_path,output_file), sep=r'\s+')

    # Define the plot parameters
    fig, ax = plt.subplots()
    pars = {'C' : 'Capacitance' }
    par_x = 'V'
    xlabel = 'Voltage [V]'
    ylabel = 'Capacitance [Fm$^{-2}$]'
    title = 'Capacitance-Voltage'
    
    # Plot with or without errorbars
    if plot_type == plt.errorbar:
        ax = utils_plot.plot_result(data, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type, 
                                            [], data['errC'], legend=False)
    else:
        ax = utils_plot.plot_result(data, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type, legend=False)

    plt.show()

def MottSchottky_plot(session_path, output_file, xscale='linear', yscale='linear', plot_type = plt.errorbar):
    """ Plot the 1/capacitance^2 against voltage

    Parameters
    ----------
    session_path : string
        working directory for zimt
    output_file : string
        Filename where the capacitance data is stored
    xscale : string
        Scale of the x-axis. E.g linear or log
    yscale : string
        Scale of the y-axis. E.g linear or log
    plot_type : matplotlib.pyplot
        Type of plot to display
    """
    # Read the data from CapVol-file
    data = pd.read_csv(os.path.join(session_path,output_file), sep=r'\s+')

    # Define the plot parameters
    fig, ax = plt.subplots()
    pars = {'1/C2' : 'Capacitance' }
    par_x = 'V'
    xlabel = 'Voltage [V]'
    ylabel = '1/Capacitance$^2$ [Fm$^{-2}$]$^{-2}$'
    title = 'Mott-Schottky'
    
    data['1/C2'] = 1/(data['C'])**2

    # Plot with or without errorbars
    if plot_type == plt.errorbar:
        ax = utils_plot.plot_result(data, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type, 
                                            [], data['errC'], legend=False)
    else:
        ax = utils_plot.plot_result(data, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type, legend=False)

    plt.show()

def plot_capacitance(session_path, output_file='CapVol.dat'):
    """Make a plot of the capacitance against voltage and the Mott-Schottky plot

    Parameters
    ----------
    session_path : string
        working directory for zimt
    """

    cap_plot(session_path, output_file)

    MottSchottky_plot(session_path, output_file)

def run_CV_simu(zimt_device_parameters, session_path, freq, V_min, V_max, V_step, G_frac=1, del_V=0.01,  run_mode=False,tVG_name='tVG.txt',  output_file = 'CapVol.dat', tj_name = 'tj.dat', varFile = 'none', ini_timeFactor=1e-3, timeFactor=1.02,**kwargs):
    """Create a tVG file and run ZimT with capacitance device parameters

    Parameters
    ----------
    zimt_device_parameters : string
        Name of the zimt device parameters file
    session_path : string, optional
        working directory for zimt
    freq : float
        Frequency at which the capacitance-voltage measurement is performed
    V_min : float
        Initial voltage
    V_max : float
        Maximum voltage
    V_step : float
        Voltage difference, determines at which voltages the capacitance is determined
    G_frac : float, optional
        Fractional light intensity, by default 1
    del_V : float, optional
        Voltage step that is applied directly after t=0, by default 0.01
    run_mode : bool, optional
        Indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default False  
    tVG_name : string, optional
        Name of the tVG file, by default tVG.txt
    output_file : string, optional
        Name of the file where the capacitance data is stored, by default CapVol.dat
    tj_name : string, optional
        Name of the tj file where the capacitance data is stored, by default tj.dat
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
    
    # Update the file names with the UUID
    if UUID != '':
        dum_str = f'_{UUID}'
    else:
        dum_str = ''

    turnoff_autoTidy = kwargs.get('turnoff_autoTidy', None) # Check if the user wants to turn off the autoTidy function in SIMsalabim
    if turnoff_autoTidy is None: 
        if not threadsafe:
            turnoff_autoTidy = True
        else:
            turnoff_autoTidy = False

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

    # The simulations with Rseries and Rshunt often do not converge, so we first run a steady state simulation to get the internal voltage and then run the impedance simulation with Rseries = 0 and Rshunt = -Rshunt. We will correct the impedance afterwards. This is a workaround to improve the convergence of the impedance simulation that should remain accurate to estimate the impedance.
    #default values for Rseries and Rshunt
    Rseries = 0
    Rshunt = -1e3

    # Do the steady state simulation to calculate the internal voltage in case of series resistance
    # Create tVG
    result, message = create_tVG_SS_CV(V_min, V_max, V_step, G_frac, tVG_name, session_path)

    # Get the device parameters and Rseries and Rshunt
    dev_val,layers_dum = load_device_parameters(session_path, zimt_device_parameters)
    for i in dev_val[zimt_device_parameters]:
        if i[0] == 'Contacts':
            contacts = i
            break

    for i in contacts[1:]:
        if i[1] == 'R_series':
            Rseries = float(i[2])
        elif i[1] == 'R_shunt':
            Rshunt = float(i[2])

    # Check if R_series and R_shunt are defined in cmd_pars
    idx_Rseries, idx_Rshunt = None, None
    if cmd_pars is not None:
        for idx, i in enumerate(cmd_pars):
            if i['par'] == 'R_series':
                Rseries = float(i['val'])
                idx_Rseries = idx
            elif i['par'] == 'R_shunt':
                Rshunt = float(i['val'])
                idx_Rshunt = idx

    if Rseries > 0:
        # Check if tVG file is created
        if result == 0:
            # In order for zimt to converge, set absolute tolerance of Poisson solver small enough
            tolPois = 10**(math.floor(math.log10(abs(del_V)))-4)

            # Define mandatory options for ZimT to run well with impedance:
            CV_SS_args = [{'par':'dev_par_file','val':zimt_device_parameters},
                                {'par':'tVGFile','val':tVG_name},
                                {'par':'tolPois','val':str(tolPois)},
                                {'par':'limitDigits','val':'0'},
                                {'par':'currDiffInt','val':'2'},
                                {'par':'tJFile','val':tj_name},
                                {'par':'varFile','val':varFile},
                                {'par':'logFile','val':'log'+dum_str+'.txt'}
                                ]
            if turnoff_autoTidy:
                CV_SS_args.append({'par':'autoTidy','val':'0'})

            if cmd_pars is not None:
                CV_SS_args = update_cmd_pars(CV_SS_args, cmd_pars)
            
            if threadsafe:
                result, message = utils_gen.run_simulation_filesafe('zimt', CV_SS_args, session_path, run_mode)
            else:
                result, message = utils_gen.run_simulation('zimt', CV_SS_args, session_path, run_mode)
            
            if result.returncode == 0 or result.returncode == 95:
                data = read_tj_file(session_path, tj_file_name=tj_name)

                Vext = np.asarray(data['Vext'])
                Jext = np.asarray(data['Jext'])
                Vint = Vext - Jext*Rseries
            else:
                return result.returncode, message
        else:
            return result, message

        # Create tVG
        result, message = create_tVG_CV_Rseries(Vint, del_V, G_frac, tVG_name, session_path, freq, ini_timeFactor, timeFactor)

    else:            
        # Create tVG
        result, message = create_tVG_CV(V_min, V_max, del_V, V_step, G_frac, tVG_name, session_path, freq, ini_timeFactor, timeFactor)

    # remove the Rseries and Rshunt from cmd_pars
    if idx_Rseries is not None and idx_Rshunt is not None:
        if idx_Rseries < idx_Rshunt:
            cmd_pars.pop(idx_Rshunt)
            cmd_pars.pop(idx_Rseries)
        else:
            cmd_pars.pop(idx_Rseries)
            cmd_pars.pop(idx_Rshunt)
    elif idx_Rseries is not None and idx_Rshunt is None:
        cmd_pars.pop(idx_Rseries)
    elif idx_Rshunt is not None and idx_Rseries is None:
        cmd_pars.pop(idx_Rshunt)

    # Check if tVG file is created
    if result == 0:
        # In order for zimt to converge, set absolute tolerance of Poisson solver small enough
        tolPois = 10**(math.floor(math.log10(abs(del_V)))-4)

        # Define mandatory options for ZimT to run well with CV:
        CV_args = [{'par':'dev_par_file','val':zimt_device_parameters},
                        {'par':'tVGFile','val':tVG_name},
                        {'par':'tolPois','val':str(tolPois)},
                        {'par':'limitDigits','val':'0'},
                        {'par':'currDiffInt','val':'2'},
                        {'par':'tJFile','val':tj_name},
                        {'par':'varFile','val':varFile},
                        {'par':'logFile','val':'log'+dum_str+'.txt'},
                        # We remove Rseries and Rshunt as the simulation is either to converge that way, we will correct the impedance afterwards
                        {'par':'R_series','val':str(0)},
                        {'par':'R_shunt','val':str(-abs(Rshunt))}]
        
        if turnoff_autoTidy:
            CV_args.append({'par':'autoTidy','val':'0'})
            
        if cmd_pars is not None:
                CV_args = update_cmd_pars(CV_args, cmd_pars)

        if threadsafe:
            result, message = utils_gen.run_simulation_filesafe('zimt', CV_args, session_path, run_mode)
        else:
            result, message = utils_gen.run_simulation('zimt', CV_args, session_path, run_mode)

        if result.returncode == 0 or result.returncode == 95:
            data = read_tj_file(session_path, tj_file_name=tj_name)

            result, message = get_capacitance(data, freq, V_min, V_max, del_V, V_step, session_path, zimt_device_parameters, output_file)
            return result, message

        else:
            return result.returncode, message
        
    return result, message

######### Running the function as a standalone script #############################################
if __name__ == "__main__":
    ## Manual CV input parameters. These are overwritten by command line arguments if provided
    freq = 1e4
    V_min = 0.5
    V_max = 1.0
    del_V = 10e-3
    V_step = 0.1    
    G_frac = 0

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
    run_mode = False # If False, show verbose output in console

    ############## Command line arguments  ##############
    ## Notes
    ## - The command line arguments are optional and can be provided in any order
    ## - Each command line argument must be provided in the format -par_name value
    ## - Possible arguments include all SIMsalabim parameters and CV specific parameters as listed before
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
        'freq': lambda val: {'freq': float(val)},
        'V_min': lambda val: {'V_min': float(val)},
        'V_max': lambda val: {'V_max': float(val)},
        'del_V': lambda val: {'del_V': float(val)},
        'V_step': lambda val: {'V_step': float(val)},
        'G_frac': lambda val: {'G_frac': float(val)},
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

    # Run Capacitance-Voltage   
    result, message = run_CV_simu(zimt_device_parameters, session_path, freq, V_min, V_max, V_step, G_frac, del_V,run_mode=False, tVG_name=tVG_name, 
                                    output_file = output_name, tj_name = tj_name, ini_timeFactor=ini_timeFactor, timeFactor=timeFactor, cmd_pars=cmd_pars, UUID=UUID)

    # Make the capacitance-voltage plot
    if result == 0 or result == 95:
        plot_capacitance(session_path, os.path.basename(output_name))
    else:
        print(message)
        sys.exit(1)


    
