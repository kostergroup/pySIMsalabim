"""Perform JV sweep simulations"""
######### Package Imports #########################################################################

import os,sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import trapezoid
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
from pySIMsalabim.utils.utils import update_cmd_pars

######### Function Definitions ####################################################################

def build_tVG_arrays(Vmin,Vmax,scan_speed,direction,steps,G_frac,stabilized=False):
    """Build the Arrays for time, voltage and Generation rate for a JV experiment.

    Parameters
    ----------
    Vmin : float 
        minimum voltage
    Vmax : float
        maximum voltage
    scan_speed : float
        Voltage scan speed [V/s]
    direction : integer
        Perform a Vmin-Vmax (1) or Vmax-Vmin scan (-1)
    steps : integer
        Number of time steps
    G_frac : float
        Device Parameter | Fractional Generation rate
    stabilized : bool, optional
        If True, create a tVG file for a stabilized JV sweep i.e. steady-state. Default is False.

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
    if stabilized:
        t = np.zeros(steps)
    else:
        t = np.linspace(0, tmax, steps)

    if direction == 1: # Vmin to Vmax
        V = np.linspace(Vmin, Vmax, steps)
    elif direction == -1: # Vmax to Vmin
        V = np.linspace(Vmax, Vmin, steps)
    else:
        raise ValueError("Direction must be 1 or -1")

    G = G_frac * np.ones(steps)
    
    return t,V,G

def build_tVG_arrays_log(Vmin,Vmax,Vacc,scan_speed,direction,steps,G_frac,stabilized=False):
    """Build the Arrays for time, voltage and Generation rate for a JV experiment with an exponential voltage sweep.

    Parameters
    ----------
    Vmin : float 
        minimum voltage
    Vmax : float
        maximum voltage
    Vacc : float
        Point of accumulation of row of V's, note: Vacc should be slightly larger than Vmax or slightly lower than Vmin
    scan_speed : float
        Voltage scan speed [V/s]
    direction : integer
        Perform a Vmin-Vmax (1) or Vmax-Vmin scan (-1)
    steps : integer
        Number of time steps
    G_frac : float
        Device Parameter | Fractional Generation rate
    stabilized : bool, optional
        If True, create a tVG file for a stabilized JV sweep i.e. steady-state. Default is False.

    Returns
    -------
    np.array
        Array of time points
    np.array
        Array of voltages
    np.array
        Array of generation rates
    """ 
    if Vacc >= Vmin and Vacc <= Vmax:
        raise ValueError('Vacc must not be between Vmin and Vmax')
    
    d = Vacc-Vmax
    V_sweep = [ Vacc - d * np.exp((1 - i/(steps - 1)) * np.log((Vacc - Vmin)/d)) for i in range(steps) ]
    V_sweep = np.array(V_sweep)
    if Vmin == 0:
        # find idx of the min of V_sweep and set it to 0
        min_idx = np.argmin(V_sweep)
        V_sweep[min_idx] = 0
    elif Vmax == 0:
        # find idx of the max of V_sweep and set it to 0
        max_idx = np.argmax(V_sweep)
        V_sweep[max_idx] = 0

    if direction == 1:
        # forward
        V = V_sweep
    elif direction == -1:
        # backward
        V = V_sweep[::-1]
    G = G_frac * np.ones(len(V))
    # calculate the time array based on the voltage array and the scan speed
    t = np.zeros(len(V))
    if not stabilized:
        for i in range(1,len(V)):
            t[i] = t[i-1] + abs((V[i]-V[i-1])/scan_speed)

    return t,V,G

def create_tVG_sweep(session_path, Vmin, Vmax, scan_speed, direction, steps, G_frac, tVG_name, Vacc=None,Vdist=1,stabilized=False,**kwargs):
    """Create a tVG file for JV experiments. 

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
        Perform a Vmin-Vmax (1) or Vmax-Vmin scan (-1)
    steps : integer
        Number of time steps
    G_frac : float
        Device Parameter | Fractional Generation rate
    Vacc : float, optional
        Point of accumulation of row of V's, note: Vacc should be slightly larger than Vmax or slightly lower than Vmin, only needed if Vdist=2, else ignored, default is None
    Vdist : integer, optional
        Voltage distribution type (1: linear, 2: exponential), default is 1
    tVG_name : string
        Device Parameter | Name of the tVG file
    stabilized : bool, optional
        If True, create a tVG file for a stabilized JV sweep i.e. steady-state. Default is False.
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
    
    expo_mode = True if Vdist == 2 else False
    if expo_mode and Vacc is None:
        msg = 'When expo_mode is True, Vacc must be provided'
        retval = 1
        return retval, msg
    
    # check that direction is either 1 or -1
    if direction != 1 and direction != -1:
        msg = 'Incorrect scan direction, choose either 1 for a forward scan or -1 for a backward scan'
        retval = 1
        return retval, msg

    # check that Vmin < Vmax
    if Vmin >= Vmax:
        msg = 'Vmin must be smaller than Vmax'
        retval = 1
        return retval, msg    

    # Create arrays for the time sweep
    if expo_mode:
        t,V,G = build_tVG_arrays_log(Vmin,Vmax,Vacc,scan_speed,direction,steps,G_frac,stabilized=stabilized)
    else:
        t,V,G = build_tVG_arrays(Vmin,Vmax,scan_speed,direction,steps,G_frac,stabilized=stabilized)

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

def plot_JV_sweep(session_path, path2file = 'tj.dat'):
    """Plot the JV curve

    Parameters
    ----------
    session_path : string
        working directory for zimt
    path2file : string
        Path to the tj file

    Returns
    -------
    Axes
        Axes object for the plot

    """
    # Read the data from tj-file
    data_tj = pd.read_csv(os.path.join(session_path,path2file), sep=r'\s+')
    
    fig, ax = plt.subplots()
    pars = {'Jext' : 'Simulation'} #'$J_{ext}$'}
    par_x = 'Vext'
    xlabel = '$V_{ext}$ [V]'
    ylabel = 'Current density [Am$^{-2}$]'
    xscale = 'linear'
    yscale = 'linear'
    title = 'JV curve'
    plot_type = plt.plot

    ax = utils_plot.plot_result(data_tj, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type)
    plt.tight_layout() # make it fit in the window
    
    return ax

def read_Exp_JV(session_path, expJV_file):
    """Read experimental JV file

    Parameters
    ----------
    session_path : string
        working directory for zimt
    expJV_file : string
        Name of the file of the JV scan

    Returns
    -------
    pd.DataFrame
        DataFrame of current and voltage of experimental JV
    """
    
    expJV_path = os.path.join(session_path, expJV_file)
    
    # Determine time corresponding to each voltage V_i
    JV = pd.read_csv(expJV_path, sep=r'\s+')
    
    return JV

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

def Compare_Exp_Sim_JV(session_path, expJV_file, rms_mode, tj_file_name='tj.dat'):
    """ Calculate the root-mean-square (rms) error of the simulated data compared to the experimental data. The used formulas are
    described in the Manual (see the variable rms_mode in the section 'Description of simulated device parameters').

    Parameters
    ----------
    session_path : string
        Path of the simulation folder for this session
    expJV_file : string
        Name of the file of the experimental JV scan
    rms_mode : string
        Indicates how the normalised rms error should be calculated: either in linear or logarithmic form
    tj_file_name : dataFrame
        Pandas dataFrame containing the tj output file from ZimT

    Returns
    -------
    Float
        Calculated rms-error
    """
        
    JVExp = read_Exp_JV(session_path, expJV_file)
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
        JVExp = JVExp.drop(np.sort(indices)).reset_index(drop=True)
    
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

def JV_sweep(zimt_device_parameters, session_path, UseExpData, scan_speed=None, direction=1, G_frac=1, tVG_name='tVG.txt', tj_name = 'tj.dat',varFile='none',
                  run_mode=False, Vmin=0.0, Vmax=0.0, steps =0, expJV_file='',rms_mode='lin', stabilized=False, **kwargs ):
    """Create a tVG file and perform a JV sweep experiment.

    Parameters
    ----------
    zimt_device_parameters : string
        name of the zimt device parameters file
    session_path : string
        working directory for zimt
    UseExpData : integer
        If 1, use experimental JV curves. If 0, Use Vmin, Vmax as boundaries
    scan_speed : float, optional
        Voltage scan speed [V/s], by default None
    direction : integer, optional
        Perform a forward (1) or backward scan (-1), by default 1
    G_frac : float, optional
        Device Parameter | Fractional generation rate, by default 1
    run_mode : bool, optional
        Indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default False  
    tVG_name : string, optional
        Device Parameter | Name of the tVG file, by default 'tVG.txt'
    tj_name : string, optional
        Name of the tj file, by default 'tj.dat'
    varFile : string, optional
        Name of the var file, by default 'none'
    run_mode : bool, optional
        indicate whether the script is in 'web' mode (True) or standalone mode (False). Used to control the console output, by default False
    Vmin : float, optional
        Left voltage boundary, by default 0.0
    Vmax : float, optional
        Right voltage boundary, by default 0.0
    steps : int, optional
        Number of time steps, by default 0
    expJV_file : str, optional
        file name of the expJV curve, by default ''
    rms_mode : str, optional
        Either 'lin' or 'log' to specify how the rms error is calculated
    stabilized : bool, optional
        If True, perform a stabilized JV sweep i.e. steady-state. Default is False.

    Returns
    -------
    CompletedProcess
        Output object of with returncode and console output of the simulation
    string
        Return message to display on the UI, for both success and failed
    dict
        Dictionary containing the special output values of the simulation. In this case, the rms error ('rms').
    """
    verbose = kwargs.get('verbose', False) # Check if the user wants to see the console output
    UUID = kwargs.get('UUID', '') # Check if the user wants to add a UUID to the tj file name
    cmd_pars = kwargs.get('cmd_pars', None) # Check if the user wants to add additional command line parameters
    Vdist = kwargs.get('Vdist', 1) # Voltage distribution type (1: linear, 2: exponential)
    Vacc = kwargs.get('Vacc', None) # Point of accumulation of row of V's, note: Vacc should be slightly larger than Vmax or slightly lower than Vmin, only needed if Vdist=2, else ignored

    if not stabilized:
        if scan_speed is None or Vmin is None or Vmax is None or steps is None:
            raise ValueError('When stabilized is False, scan_speed, Vmin, Vmax and steps must be provided')

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

    # Update the filenames with the UUID
    tj_name = os.path.join(session_path, tj_name)
    tVG_name = os.path.join(session_path, tVG_name)
    if UUID != '':
        tj_file_name_base, tj_file_name_ext = os.path.splitext(tj_name)
        tj_name = tj_file_name_base + dum_str + tj_file_name_ext 
        tVG_name_base, tVG_name_ext = os.path.splitext(tVG_name)
        tVG_name = tVG_name_base + dum_str + tVG_name_ext
        if varFile != 'none':
            var_file_base, var_file_ext = os.path.splitext(varFile)
            varFile = var_file_base + dum_str + var_file_ext
            varFile = os.path.join(session_path, varFile)

    # Init output_vals rms
    rms = 0.0

    if UseExpData == 1:
        # When fitting to experimental data, create a tVG file where Vext is the same as the voltages in the experimental JV file
        if os.path.exists(os.path.join(session_path, expJV_file)):
            exp_data = read_Exp_JV(session_path, expJV_file)
            V = exp_data.Vext.values
            t = np.zeros(len(V))
            for i in range(1, len(V)):
                t[i] = t[i-1] + abs((V[i]-V[i-1])/scan_speed)
            G = G_frac * np.ones(len(t))
            tVG = pd.DataFrame({'t': t, 'Vext': V, 'G_frac': G})
            tVG.to_csv(tVG_name, sep=' ', index=False, float_format='%.5e')
            result, message = 0, 'Success'
        else:
            result = 1
            message = 'Experimental JV file not found'
    else:
        result, message = create_tVG_sweep(session_path, Vmin, Vmax, scan_speed, direction, steps, G_frac, tVG_name, Vacc=Vacc, Vdist=Vdist,stabilized=stabilized)

    if result == 0:
        # tVG file created
        JV_sweep_args = [{'par':'dev_par_file','val':zimt_device_parameters},
                              {'par':'tVGFile','val':tVG_name},
                              {'par':'tJFile','val':tj_name},
                              {'par':'varFile','val':varFile},
                              {'par':'logFile','val':'log'+dum_str+'.txt'}
                              ]
        
        if turnoff_autoTidy:
            JV_sweep_args.append({'par':'autoTidy','val':'0'})

        if cmd_pars is not None:
            JV_sweep_args = update_cmd_pars(JV_sweep_args, cmd_pars)

        if threadsafe:
            result, message = utils_gen.run_simulation_filesafe('zimt', JV_sweep_args, session_path, run_mode, verbose=verbose)
        else:
            result, message = utils_gen.run_simulation('zimt', JV_sweep_args, session_path, run_mode, verbose=verbose)

        if result == 0 or result == 95:
            if UseExpData == 1:
                rms = Compare_Exp_Sim_JV(session_path, expJV_file, rms_mode, tj_name)
        else:
            message = message
        
        result = result

        # Put all the output values in a dictionary to be returned. 
        # By putting it in a dictionary we can add any number of values without breaking return arguments
        output_vals = {'rms': rms}
    
    return result, message, output_vals

## Running the function as a standalone script
if __name__ == "__main__":
    ## Manual JV sweep input parameters. These are overwritten by command line arguments if provided
    scan_speed = 1e1 # V/s
    direction = 1 # Scan direction: 1 for Vmin-Vmax, -1 for Vmax-Vmin
    G_frac = 1 # amount of suns
    UseExpData = 0 # integer, if 1 read experimental data
    Vmin = 0 # lower voltage boundary
    Vmax = 1.15 # upper voltage boundary
    steps = 200 # Number of voltage steps
    expJV_file = 'exp_jv.txt' # Experimental JV scan file

    # Define folder and file paths
    session_path = os.path.join('../../','SIMsalabim','ZimT')

    zimt_device_parameters = 'simulation_setup.txt'

    tVGFile = 'tVG.txt'
    tJFile = 'tj.dat'
    varFile = 'none'

    # UUID = str(uuid.uuid4()) # Add a UUID to the simulation
    UUID = ''

    # Not user input
    rms_mode = 'log' # lin or log

    ############## Command line arguments  ##############
    ## Notes
    ## - The command line arguments are optional and can be provided in any order
    ## - Each command line argument must be provided in the format -par_name value
    ## - Possible arguments include all SIMsalabim parameters and JV sweep specific parameters as listed before
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
        'zimt_device_parameters': lambda val: {'zimt_device_parameters': val},
        'scan_speed': lambda val: {'scan_speed': float(val)},
        'direction': lambda val: {'direction': int(val)},
        'G_frac': lambda val: {'G_frac': float(val)},
        'UseExpData': lambda val: {'UseExpData': int(val)},
        'Vmin': lambda val: {'Vmin': float(val)},
        'Vmax': lambda val: {'Vmax': float(val)},
        'steps': lambda val: {'steps': int(val)},
        'expJV_file': lambda val: {'expJV_file': val},
        'tVGFile': lambda val: {'tVGFile':  val},
        'tJFile': lambda val: {'tJFile': val},
        'varFile': lambda val: {'varFile': val},
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
    
    if UseExpData == 1:
        result, message, output_vals = JV_sweep(zimt_device_parameters, session_path, UseExpData, scan_speed, direction, G_frac, tVG_name = tVGFile, tj_name = tJFile,
                                             run_mode = False, expJV_file = expJV_file, rms_mode = rms_mode, cmd_pars = cmd_pars, UUID=UUID)
    else:
        result, message, output_vals = JV_sweep(zimt_device_parameters, session_path, UseExpData, scan_speed, direction, G_frac, tVG_name = tVGFile, tj_name = tJFile, 
                                              run_mode = False, Vmin=Vmin, Vmax=Vmax, steps =steps, rms_mode = rms_mode, cmd_pars = cmd_pars, UUID=UUID)
    
    if result == 0 or result == 95:
        if UseExpData == 1:
            print('Rms-value: ', "{:.5f}".format(round(output_vals['rms'], 5)))

        ax = plot_JV_sweep(session_path, tJFile)
        if UseExpData == 1:
            JVExp = read_Exp_JV(session_path, expJV_file)
            ax.scatter(JVExp.Vext, JVExp.Jext, label='Experimental', color='r')
        
        ax.legend()
        plt.show()
    else:
        print(message) #'Convergence issues, no plot is printed')
