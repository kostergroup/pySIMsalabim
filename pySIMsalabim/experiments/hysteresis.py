"""Perform JV hysteresis simulations"""
######### Package Imports #########################################################################

import os,sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pySIMsalabim.utils import general as utils_gen
from pySIMsalabim.plots import plot_functions_gen as utils_plot_gen
from pySIMsalabim.utils.utils import update_cmd_pars

######### Function Definitions ####################################################################

def build_tVG_arrays(Vmin,Vmax,scan_speed,direction,steps,G_frac):
    """Build the Arrays for time, voltage and Generation rate for a hysteresis experiment.

    Parameters
    ----------
    Vmin : float 
        minimum voltage
    Vmax : float
        maximum voltage
    scan_speed : float
        Voltage scan speed [V/s]
    direction : integer
        Perform a Vmin-Vmax-Vmin (1) or Vmax-Vmin-Vmax scan (-1)
    steps : integer
        Number of time steps
    G_frac : float
        Device Parameter | Fractional Generation rate

    Returns
    -------
    np.array
        Array of time points
    np.array
        Array of voltages
    np.array
        Array of generation rates
    """    
    # Determine max time point
    tmax = abs((Vmax - Vmin)/scan_speed)
    V, G = [], []
    Vmin_ = Vmin
    Vmax_ = Vmax

    if direction == -1:
        Vmin = Vmax_
        Vmax = Vmin_

    t_min_to_max = np.linspace(0,tmax,int(steps/2))
    t_max_to_min = np.linspace(tmax,2*tmax,int(steps/2))
    t_max_to_min = np.delete(t_max_to_min,[0]) # remove double entry
    t = np.append(t_min_to_max,t_max_to_min)

    for i in t:
        if i < tmax:
            # First  voltage sweep
            V.append(direction*scan_speed*i + Vmin)
        else: 
            # Second voltage sweep
            V.append(-direction*scan_speed*(i-tmax) + Vmax)
        # Append the generation rate
        G.append(G_frac)
    # convert to numpy arrays
    V, G = np.asarray(V), np.asarray(G)
    return t,V,G

def build_tVG_arrays_log(Vmin,Vmax,scan_speed,direction,steps,G_frac,Vminexpo= 1e-2):
    """Build the Arrays for time, voltage and Generation rate for a hysteresis experiment with an exponential voltage sweep.

    Parameters
    ----------
    Vmin : float 
        minimum voltage
    Vmax : float
        maximum voltage
    scan_speed : float
        Voltage scan speed [V/s]
    direction : integer
        Perform a Vmin-Vmax-Vmin (1) or Vmax-Vmin-Vmax scan (-1)
    steps : integer
        Number of time steps
    G_frac : float
        Device Parameter | Fractional Generation rate
    Vminexpo : float
        Voltage at which the exponential voltage steps start if Vmin or Vmax is 0

    Returns
    -------
    np.array
        Array of time points
    np.array
        Array of voltages
    np.array
        Array of generation rates
    """ 

    if Vmin*Vmax >= 0:
        if Vmin == 0:
            V_min_to_max = np.logspace(np.log10(abs(Vminexpo)),np.log10(abs(Vmax)),int(steps/2))
            # add 0 to the beginning of the array
            V_min_to_max = np.insert(V_min_to_max,0,0)
        elif Vmax == 0:
            V_min_to_max = np.logspace(np.log10(abs(Vmin)),np.log10(abs(Vminexpo)),int(steps/2))
            # add 0 to the end of the array
            V_min_to_max = np.append(V_min_to_max,0)
        else:
            if Vmin > 0:
                V_min_to_max = np.logspace(np.log10(abs(Vmin)),np.log10(abs(Vmax)),int(steps/2))
            else:
                V_min_to_max = -np.logspace(np.log10(abs(Vmax)),np.log10(abs(Vmin)),int(steps/2))

        V_max_to_min = V_min_to_max[::-1]
       
        
        # Create t,G arrays for both sweep directions
        if direction == 1:
            # forward -> backward
            V_max_to_min = np.delete(V_max_to_min,[0])# remove double entry
            V = np.append(V_min_to_max,V_max_to_min)
            
        elif direction == -1:
            # backward -> forward
            V_min_to_max = np.delete(V_min_to_max,[0])# remove double entry
            V = np.append(V_max_to_min,V_min_to_max)
        
        G = G_frac * np.ones(len(V))

        # calculate the time array based on the voltage array and the scan speed
        t = np.zeros(len(V))
        for i in range(1,len(V)):
            t[i] = t[i-1] + abs((V[i]-V[i-1])/scan_speed)

    else:
        negative_V = -np.logspace(np.log10(abs(Vmin)),np.log10(abs(Vminexpo)),int(steps/4))
        positive_V = np.logspace(np.log10(abs(Vminexpo)),np.log10(abs(Vmax)),int(steps/4))
        # add 0 at the beginning
        positive_V = np.append(0,positive_V)
        V = np.append(negative_V,positive_V)
        # make back to back
        Vback = V[::-1]

        if direction == 1:
            # remove the first element
            Vback = Vback[1:]
            V = np.append(V,Vback)
            G = G_frac * np.ones(len(V))
        elif direction == -1:
            # remove the last element
            Vback = Vback[:-1]
            V = np.append(Vback,V)
            G = G_frac * np.ones(len(V))
        
        # calculate the time array based on the voltage array and the scan speed
        t = np.zeros(len(V))
        for i in range(1,len(V)):
            t[i] = t[i-1] + abs((V[i]-V[i-1])/scan_speed)
    return t,V,G

def create_tVG_hysteresis(session_path, Vmin, Vmax, scan_speed, direction, steps, G_frac, tVG_name, **kwargs):
    """Create a tVG file for hysteresis experiments. 

    Parameters
    ----------
    session_path : string
        working directory for zimt
    Vmin : float 
        Left voltage boundary
    Vmax : float
        Right voltage boundary
    scan_speed : float
        Voltage scan speed [V/s]
    direction : integer
        Perform a Vmin-Vmax-Vmin (1) or Vmax-Vmin-Vmax scan (-1)
    steps : integer
        Number of time steps
    G_frac : float
        Device Parameter | Fractional Generation rate
    tVG_name : string
        Device Parameter | Name of the tVG file
    **kwargs : dict
        Additional keyword arguments

    Returns
    -------
    integer
        Value to indicate the result of the process
    string
        A message to indicate the result of the process
    """
    # kwargs
    expo_mode = kwargs.get('expo_mode', False) # whether to use exponential voltage steps
    Vminexpo = kwargs.get('Vminexpo', 1e-2) # Voltage at which the exponential voltage steps start if Vmin or Vmax is 0
    # check that Vminexpo is positive
    if Vminexpo <= 0:
        msg = 'Vminexpo must be strictly positive'
        retval = 1
        return retval, msg

    # check that direction is either 1 or -1
    if direction != 1 and direction != -1:
        msg = 'Incorrect scan direction, choose either 1 for a forward - backward scan or -1 for a backward - forward scan'
        retval = 1
        return retval, msg

    # check that Vmin < Vmax
    if Vmin >= Vmax:
        msg = 'Vmin must be smaller than Vmax'
        retval = 1
        return retval, msg    

    # Create two arrays for both time sweeps
    if expo_mode:
        t,V,G = build_tVG_arrays_log(Vmin,Vmax,scan_speed,direction,steps,G_frac,Vminexpo)
    else:
        t,V,G = build_tVG_arrays(Vmin,Vmax,scan_speed,direction,steps,G_frac)
        
    # Set the correct header for the tVG file
    tVG_header = ['t','Vext','G_frac']

    # Combine t,V,G arrays into a DataFrame
    tVG = pd.DataFrame(np.stack([t,np.asarray(V),np.asarray(G)]).T,columns=tVG_header)

    # Create tVG file
    tVG.to_csv(os.path.join(session_path,tVG_name),sep=' ',index=False,float_format='%.5e')

    # tVG file is created, msg a success
    msg = 'Success'
    retval = 0
    
    return retval, msg

def plot_hysteresis_JV(path2file = 'tj.dat'):
    """Plot the hysteresis JV curve

    Parameters
    ----------
    path2file : string
        Path to the tj file

    Returns
    -------
    Axes
        Axes object for the plot

    """
    # Read the data from tj-file
    data_tj = pd.read_csv(path2file, sep=r'\s+')
    
    fig, ax = plt.subplots()
    pars = {'Jext' : 'Simulation'} #'$J_{ext}$'}
    par_x = 'Vext'
    xlabel = '$V_{ext}$ [V]'
    ylabel = 'Current density [Am$^{-2}$]'
    xscale = 'linear'
    yscale = 'linear'
    title = 'JV curve'
    plot_type = plt.plot

    ax = utils_plot_gen.plot_result(data_tj, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type)
    
    return ax

def tVG_exp(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin, scan_speed, direction, G_frac, tVG_name):
    """Create a tVG file for hysteresis experiments where Vext is the same as the voltages in the experimental JV file

    Parameters
    ----------
    session_path : string
        working directory for zimt
    expJV_Vmin_Vmax : string
        Name of the file of the Vmin-Vmax JV scan
    expJV_Vmax_Vmin : string
        Name of the file of the Vmax-Vmin JV scan
    scan_speed : float
        Voltage scan speed [V/s]
    direction : integer
        Perform a Vmin-Vmax-Vmin (1) or Vmax-Vmin-Vmax scan (-1)
    G_frac : float
        Fractional Generation rate
    tVG_name : string
        Name of the tVG file

    Returns
    -------
    integer
        Value to indicate the result of the process
    string
        A message to indicate the result of the process
    """
    
    if direction == 1:
        JV_forward, JV_backward = read_Exp_JV(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin)
    elif direction == -1:
        JV_backward, JV_forward = read_Exp_JV(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin)
    else:
        # Illegal value for direction given
        msg = 'Incorrect scan direction, choose either 1 for Vmin-Vmax-Vmin scan or -1 for a Vmax-Vmin-Vmax scan'
        retval = 1
        return retval, msg

    V_forward = JV_forward.Vext
    V_backward = JV_backward.Vext

    # Create the time array
    t=np.empty(len(V_forward) + len(V_backward))
    t[0]=0

    # First half
    for i in range(1,len(V_forward)):
        t[i]= t[i-1] + abs((V_forward[i]-V_forward[i-1])/scan_speed)

    # Turning point
    t[len(V_forward)]=t[len(V_forward)-1] + abs((V_backward[0]-V_forward.iloc[-1])/scan_speed)

    # Second half
    for i in range(len(V_forward)+1,len(V_forward) + len(V_backward)):
        t[i]= t[i-1] + abs((V_backward[i-len(V_forward)]-V_backward[i-len(V_forward)-1])/scan_speed)

    # Voltage array
    V = np.concatenate([V_forward, V_backward])

    # Set the correct header for the tVG file
    tVG_header = ['t','Vext','G_frac']

    G = G_frac * np.ones(len(t))

    # Combine t,V,G arrays into a DataFrama
    tVG = pd.DataFrame(np.stack([t,np.asarray(V),G]).T,columns=tVG_header)

    # Create tVG file
    tVG.to_csv(os.path.join(session_path,tVG_name),sep=' ',index=False,float_format='%.3e')

    # tVG file is created, msg a success
    msg = 'Success'
    retval = 0
    return retval, msg

def read_Exp_JV(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin):
    """Read experimental forward and backward JV files

    Parameters
    ----------
    session_path : string
        working directory for zimt
    expJV_Vmin_Vmax : string
        Name of the file of the forward JV scan
    expJV_Vmax_Vmin : string
        Name of the file of the backward JV scan

    Returns
    -------
    np.array
        Array of current and voltage of experimental JV from Vmin to Vmax
    np.array
        Array of current and voltage of experimental JV from Vmax to Vmin
    """
    
    expJV_min_max = os.path.join(session_path, expJV_Vmin_Vmax)
    expJV_max_min = os.path.join(session_path, expJV_Vmax_Vmin)
    
    # Determine time corresponding to each voltage V_i
    JV_min_max = pd.read_csv(expJV_min_max, sep=r'\s+')
    JV_max_min = pd.read_csv(expJV_max_min, sep=r'\s+')
    
    return JV_min_max, JV_max_min

def concatJVs(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin, direction):
    """Put the experimental forward and backward JV arrays together
    session_path : string
        working directory for zimt
    expJV_Vmin_Vmax : string
        Name of the file of the forward JV scan
    expJV_Vmax_Vmin : string
        Name of the file of the backward JV scan
    direction : integer
        Perform a Vmin-Vmax-Vmin (1) or Vmax-Vmin-Vmax scan (-1)
    
    Returns
    -------
    np.array
        Array of current and voltage of experimental JV
    """
    
    if direction == 1:
        JV_forward, JV_backward = read_Exp_JV(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin)
    elif direction == -1:
        JV_backward, JV_forward = read_Exp_JV(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin)
    else:
        # Illegal value for direction given
        print('Incorrect scan direction, choose either 1 for Vmin-Vmax-Vmin scan or -1 for a Vmax-Vmin-Vmax scan')
        sys.exit()
    
    expJV = pd.concat([JV_forward, JV_backward], ignore_index=True)   
    return expJV

def read_tj_file(session_path, tj_file_name='tj.dat'):
    """ Read relevant parameters for admittance of the tj file

    Parameters
    ----------
    session_path : string
        Path of the simulation folder for this session
    data_tj : dataFrame
        Pandas dataFrame containing the tj output file from ZimT

    Returns
    -------
    DataFrame
        Pandas dataFrame of the tj_file containing the time, current density, numerical error in the current density and the photogenerated current density
    """

    data = pd.read_csv(os.path.join(session_path,tj_file_name), sep=r'\s+')

    return data

def Compare_Exp_Sim_JV(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin, rms_mode, direction, tj_file_name='tj.dat'):
    """ Calculate the root-mean-square (rms) error of the simulated data compared to the experimental data. The used formulas are
    described in the Manual (see the variable rms_mode in the section 'Description of simulated device parameters').

    Parameters
    ----------
    session_path : string
        Path of the simulation folder for this session
    expJV_Vmin_Vmax : string
        Name of the file of the forward JV scan
    expJV_Vmax_Vmin : string
        Name of the file of the backward JV scan
    rms_mode : string
        Indicates how the normalised rms error should be calculated: either in linear or logarithmic form
    direction : integer
        Perform a Vmin-Vmax-Vmin (1) or Vmax-Vmin-Vmax scan (-1)
    tj_file_name : dataFrame
        Pandas dataFrame containing the tj output file from ZimT

    Returns
    -------
    Float
        Calculated rms-error
    """
        
    JVExp = concatJVs(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin, direction)
    JVSim = read_tj_file(session_path, tj_file_name)[['t', 'Vext', 'Jext']]
    
    # Make an array of voltages that did not converge in simulation
    V_array_not_in_JVSim = np.setdiff1d(JVExp.Vext, JVSim.Vext)
    
    # Remove voltages of experimental data that did not converge in the simulation
    # As the rms-value cannot be calculated, when the voltages of the simulation and experimental data do not overlap
    if len(V_array_not_in_JVSim) > 0:
        disgardedPoints = True
        indices = []
        
        for i in range(len(V_array_not_in_JVSim)):
            # Find indices where voltages do not overlap for every V_i
            index_array = np.where((JVExp.Vext == V_array_not_in_JVSim[i]))[0]
            
            # Add the to-slice-indices to a list
            for j in range(len(index_array)):
                indices.append(index_array[j])
        
        # Delete the indices and convert JVExp from a numpy array in a DataFrame again
        JVExp = np.delete(JVExp, np.sort(indices), axis=0)
        JVExp = pd.DataFrame(JVExp, columns=['Vext', 'Jext'])
    
    rms = 0
    count = 0
    disgardedPoints = False
    
    # Look for the interval [Jmin,Jmax] in both the simulated and experiment data
    Jmin = min(min(JVExp.Jext), min(JVSim.Jext))
    Jmax = max(max(JVExp.Jext), max(JVSim.Jext))
    
    if rms_mode == 'lin' or 'linear':
        # Calculate the sum of squared residuals
        for i in range(len(JVExp)):
            rms = rms + (JVExp.Jext[i] - JVSim.Jext[i])**2
            count += 1
        
        # Calculate the root mean square error and normalise with respect to the interval [Jmin,Jmax]
        rms = np.sqrt(rms/count)/(Jmax-Jmin)
        
    elif rms_mode == 'log' or 'logarithmic':
        # Calculate the sum of squared residuals
        for i in range(len(JVExp)):
            if JVExp.Jext[i]*JVSim.Jext[i]>=0: # We can only calc rms if both are <> 0 and they have the same sign
                rms = rms + np.log(JVExp.Jext[i]/JVSim.Jext[i])**2
            else:
                disgardedPoints = True
            
        # Calculate the root mean square error and normalise with respect to the interval [Jmin,Jmax]
        rms = np.sqrt(rms/count)/abs(np.log(abs(Jmax/Jmin))) # Note: Jmax > Jmin, of course, but ABS(Jmin) can be larger than ABS(Jmax) so we need to use ABS(LN(...)) to get a positive rms

    if disgardedPoints:
        print('Not all JV points were used in computing the rms-error.')
        print('Delete voltages are: ', V_array_not_in_JVSim)
    
    return rms

def Hysteresis_JV(zimt_device_parameters, session_path, UseExpData, scan_speed, direction, G_frac, tVG_name, tj_name = 'tj.dat',
                  run_mode=False, Vmin=0.0, Vmax=0.0, steps =0, expJV_Vmin_Vmax='', expJV_Vmax_Vmin='',rms_mode='lin', **kwargs ):
    """Create a tVG file and perform a JV hysteresis experiment.

    Parameters
    ----------
    zimt_device_parameters : string
        name of the zimt device parmaeters file
    session_path : string
        working directory for zimt
    UseExpData : intger
        If 1, use experimental JV curves. If 0, Use Vmin, Vmax as boundaries
    scan_speed : float
        Voltage scan speed [V/s]
    direction : integer
        Perform a forward-backward (1) or backward-forward scan (-1).
    G_frac : float
        Device Parameter | Fractional generation rate
    tVG_name : string
        Device Parameter | Name of the tVG file
    run_mode : bool, optional
        indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default False
    Vmin : float, optional
        Left voltage boundary, by default 0.0
    Vmax : float, optional
        Right voltage boundary, by default 0.0
    steps : int, optional
        Number of time steps, by default 0
    expJV_Vmin_Vmax : str, optional
        file name of the first expJV curve, by default ''
    expJV_Vmax_Vmin : str, optional
        file name of the second expJV curve, by default ''
    rms_mode : str, optional
        Either 'lin' or 'log' to specify how the rms error is calculated

    Returns
    -------
    CompletedProcess
        Output object of with returncode and console output of the simulation
    string
        Return message to display on the UI, for both success and failed
    rms
        The rms error between the simulated and experimental data. WHen not using experimental data, it is set to 0.0 and can be ignored
    """

    UUID = kwargs.get('UUID', '') # Check if the user wants to add a UUID to the tj file name
    cmd_pars = kwargs.get('cmd_pars', None) # Check if the user wants to add additional command line parameters
    # Check if the user wants to force the use of thread safe mode, necessary for Windows with parallel simulations
    if os.name == 'nt':  
        threadsafe = kwargs.get('threadsafe', True) # Check if the user wants to force the use of threads instead of processes
    else:
        threadsafe = kwargs.get('threadsafe', False) # Check if the user wants to force the use of threads instead of processes

    # tVG file generation additional parameters
    expo_mode = kwargs.get('expo_mode', False) # whether to use exponential time steps
    Vminexpo = kwargs.get('Vminexpo', 1e-2) # minimum voltage after 0 to start the log steps

    # Update the JV file name with the UUID
    if UUID != '':
        dum_str = f'_{UUID}'
    else:
        dum_str = ''

    # Update the filenames with the UUID
    tj_name = os.path.join(session_path, tj_name)
    if UUID != '':
        tj_file_name_base, tj_file_name_ext = os.path.splitext(tj_name)
        tj_name = tj_file_name_base + dum_str + tj_file_name_ext 
        tVG_name_base, tVG_name_ext = os.path.splitext(tVG_name)
        tVG_name = tVG_name_base + dum_str + tVG_name_ext
    varFile = 'none' # we don't use a var file for the hysteresis JV simulation

    rms = 0.0
    if UseExpData == 1:
        # When fitting to experimental data, create a tVG file where Vext is the same as the voltages in the experimental JV file
        if os.path.exists(os.path.join(session_path, expJV_Vmin_Vmax)) and os.path.exists(os.path.join(session_path, expJV_Vmax_Vmin)):
            result, message = tVG_exp(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin, scan_speed, direction, G_frac, tVG_name)
        else:
            result = 1
            message = 'Experimental JV files not found'
    else:
        result, message = create_tVG_hysteresis(session_path, Vmin, Vmax, scan_speed, direction, steps, G_frac, tVG_name, expo_mode=expo_mode, Vminexpo=Vminexpo)

    if result == 0:
        # tVG file created
        Hysteresis_JV_args = [{'par':'dev_par_file','val':zimt_device_parameters},
                              {'par':'tVGFile','val':tVG_name},
                              {'par':'tJFile','val':tj_name},
                              {'par':'varFile','val':varFile},
                              {'par':'logFile','val':'log'+dum_str+'.txt'}
                              ]
        
        if cmd_pars is not None:
            Hysteresis_JV_args = update_cmd_pars(Hysteresis_JV_args, cmd_pars)

        if threadsafe:
            result, message = utils_gen.run_simulation_filesafe('zimt', Hysteresis_JV_args, session_path, run_mode)
        else:
            result, message = utils_gen.run_simulation('zimt', Hysteresis_JV_args, session_path, run_mode)

        if result.returncode == 0 or result.returncode == 95:
            if UseExpData == 1:
                rms = Compare_Exp_Sim_JV(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin, rms_mode, direction, tj_name)

    return result, message, rms

## Running the function as a standalone script
if __name__ == "__main__":
    # SIMsalabim input/output files
    session_path = 'tmp_zimt'
    zimt_device_parameters = os.path.join('device_parameters_zimt.txt')
    tVG_name = 'tVG.txt'
    tj_name = 'tj.dat'
    
    # Hysteresis input parameters
    direction = 1
    scan_speed = 1e1 # V/s
    G_frac = 1 # amount of sun ('calc') or amount of generated electron-hole pairs ('Gehp')
    
    # # Hysteresis input when not fitting
    Vmin = 0 # V
    Vmax = 1.15 # V  
    steps = 1000
    
    # Required input for fitting
    UseExpData = 1 # integer, if 1 read experimental data
    rms_mode = 'log' # lin or log
    expJV_Vmin_Vmax = 'od05_f.txt' # Forward (direction=1)/Backward (direction=-1) JV scan file
    expJV_Vmax_Vmin = 'od05_b.txt' # Backward (direction=1)/Forward (direction=-1) JV scan file
    
    if UseExpData == 1:
        result, message, rms = Hysteresis_JV(zimt_device_parameters, session_path, UseExpData, scan_speed, direction, G_frac, tVG_name, 
                                             expJV_Vmin_Vmax = expJV_Vmin_Vmax, expJV_Vmax_Vmin = expJV_Vmax_Vmin, rms_mode = rms_mode)
    else:
        result, message, rms = Hysteresis_JV(zimt_device_parameters, session_path, UseExpData, scan_speed, direction, G_frac, tVG_name, 
                                             Vmin=Vmin, Vmax=Vmax, steps =steps, rms_mode = rms_mode)
        
    if result.returncode == 0 or result.returncode == 95:
        if UseExpData == 1:
            print('Rms-value: ', "{:.5f}".format(round(rms, 5)))
    
        ax = plot_hysteresis_JV(os.path.join(session_path,'tj.dat'))
        if UseExpData == 1:
            JVExp = concatJVs(session_path, expJV_Vmin_Vmax, expJV_Vmax_Vmin, direction)
            ax.scatter(JVExp.Vext, JVExp.Jext, label='Experimental', color='r')
        
        ax.legend()
        plt.show()
    else:
        print('Convergence issues, no plot is printed')
