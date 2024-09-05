"""Perform JV hysteresis simulations"""
######### Package Imports #########################################################################

import os,sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# from pySIMsalabim.utils import general as utils_gen
# from pySIMsalabim.plots import plot_functions_gen as utils_plot_gen
# from pySIMsalabim.utils.utils import update_cmd_pars

######### Function Definitions ####################################################################

def build_tVG_arrays(t, tmax, V, G, scan_speed, V1, V2, Genrate, sign):
    """Build the Arrays for voltage and Generation rate for a hysteresis experiment.

    Parameters
    ----------
    t : array
        Array with all time positions, from 0 to tmax
    tmax : float
        Last time point
    V : array
        Array to store voltages
    G : array
        Array to store generation rate
    scan_speed : float
        Voltage scan speed [V/s]
    V1 : float
        Left voltage boundary
    V2 : float
        Right voltage boundary
    Genrate : float
        Generation rate
    sign : integer
        Indicator to swap the sign for either s forward-backward or s backward-forward scan

    Returns
    -------
    array,array
        Filled V, G arrays
    """
    for i in t:
        if i < tmax:
            # First  voltage sweep
            V.append(sign*scan_speed*i + V1)
        else: 
            # Second voltage sweep
            V.append(-sign*scan_speed*(i-tmax) + V2)
        # Append the generation rate
        G.append(Genrate)
    return V,G

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
    expo_mode = kwargs.get('expo_mode', False) # whether to use exponential time steps
    mintime = kwargs.get('mintime', abs(1e-3/scan_speed)) # minimum time after 0 to start the log time steps, by default 1e-3/scan_speed so that the first voltage is 1 mV if we start from 0

    V,G = [],[]

    # Determine max time point
    tmax = abs((Vmax - Vmin)/scan_speed)

    # Create two arrays for both time sweeps
    if not expo_mode:
        t_min_to_max = np.linspace(0,tmax,int(steps/2))
        t_max_to_min = np.linspace(tmax,2*tmax,int(steps/2))
        t_max_to_min = np.delete(t_max_to_min,[0]) # remove double entry
    else:
        # Create exponential time steps
        t_min_to_max = np.logspace(np.log10(mintime),np.log10(tmax),int(steps/2))
        # add 0 to the beginning of the array
        t_min_to_max = np.insert(t_min_to_max,0,0)
        t_max_to_min = 2*tmax - t_min_to_max[::-1]
        t_max_to_min = np.delete(t_max_to_min,[0]) # remove double entry
        
    t = np.append(t_min_to_max,t_max_to_min)

    # Create V,G arrays for both sweep directions
    if direction == 1:
        # forward -> backward
        V,G = build_tVG_arrays(t, tmax, V,G, scan_speed, Vmin, Vmax, G_frac, direction)
    elif direction == -1:
        # backward -> forward
        V,G = build_tVG_arrays(t, tmax, V,G, scan_speed, Vmax, Vmin, G_frac, direction)
    else:
        # Illegal value for direction given
        msg = 'Incorrect scan direction, choose either 1 for a forward - backward scan or -1 for a backward - forward scan'
        retval = 1
        return retval, msg
   
    # Set the correct header for the tVG file
    tVG_header = ['t','Vext','G_frac']

    # Combine t,V,G arrays into a DataFrame
    tVG = pd.DataFrame(np.stack([t,np.asarray(V),np.asarray(G)]).T,columns=tVG_header)

    # Create tVG file
    tVG.to_csv(os.path.join(session_path,tVG_name),sep=' ',index=False,float_format='%.3e')

    # tVG file is created, msg a success
    msg = 'Success'
    retval = 0
    
    return retval, msg


def main():
    cwd = os.getcwd()
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup_sclc.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    scan_speed = 1
    direction = 1
    G_frac = 0
    tVG_name = os.path.join(session_path,'tVG.txt')
    Vmin = 0.0
    Vmax = 5
    steps = 200
    expo_mode = True
    mintime = abs(1e-2/scan_speed)

    # Create tVG file
    retval, msg = create_tVG_hysteresis(session_path, Vmin, Vmax, scan_speed, direction, steps, G_frac, tVG_name, expo_mode=expo_mode, mintime=mintime)

    print(msg)


if __name__ == '__main__':
    main()


    # t_min_to_max = np.logspace(np.log10(mintime),np.log10(tmax),int(steps/2))
    #     # add 0 to the beginning of the array
    #     t_min_to_max = np.insert(t_min_to_max,0,0)
    #     t_max_to_min = 2*tmax - t_min_to_max[::-1]
    #     t_max_to_min = np.delete(t_max_to_min,[0]) # remove double entry
