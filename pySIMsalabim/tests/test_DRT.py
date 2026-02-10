######### Package Imports #########################################################################

import os, sys, uuid 
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from joblib import Parallel, delayed
try :
    import pySIMsalabim as sim
except ImportError:
    # Add the parent directory to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import pySIMsalabim as sim
from pySIMsalabim.aux_funcs import DRT as drt

######### Test Functions #########################################################################

# Test checkerboard fit runs, calling the module from main 
def test_DRT_main():
    """Test the main function in the DRT module"""
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT','tmp')


    ### Generate and save test data ###
    # Define a function to give a gaussian distribution of lifetimes about a central lifetime tau on a logarithmic scale
    def log_gaussian(tau, mu, sig):
        return 1/(sig*np.sqrt(2*np.pi))*np.exp(-(np.log10(tau/mu))**2/(2*sig**2))
    
    # Generate test data
    t_min = 1e-10
    t_max = 1e2
    time = np.geomspace(t_min, t_max, 140)

    # Generate array of tau values of length M such that tau_ppd ~ time_ppd (ppd - points per decade)
    d_t = [time[i+1] - time[i] for i in range(len(time)-1)]
    d_t_min = np.min(d_t)
    d_T = time[-1] - time[0]
    tau_min = d_t_min/np.pi   # Selected based on Nyquist spacing
    tau_max = d_T/(2*np.pi)   # Selected based on Nyquist spacing
    tau_values = np.geomspace(tau_min, tau_max, len(time))

    # Generate the analytic curve
    gaussian_coeffs = [5, -3, 2]
    gaussian_peaks = [1e-6, 1e-4, 1e-1] # These now correspond to when decay events begin
    analytic_U = np.sum([gaussian_coeffs[i]*log_gaussian(tau_values, gaussian_peaks[i], 0.2) for i in range(len(gaussian_coeffs))], axis=0)
    analytic_y = drt.predict_y_model(time, analytic_U, tau_values) + 20

    # Save y(t) to a datafile called temp_tj.dat 
    temporary_data = {'t' : time, 'Jext': analytic_y}
    dataFile = os.path.join(session_path, 'tj.dat')

    try: 
        os.makedirs(session_path)
    except FileExistsError:
        pass

    pd.DataFrame(temporary_data).to_csv(dataFile, sep=' ', float_format='%.5e', index=False)
    ### END ###


    ### Run DRT ###
    DRT_commands_and_args_dict = {
    'dataFile': dataFile, 
    'DRTDirectory': os.path.join(session_path, 'DRT_Saves'),
    'timeCol': 't',
    'funcCol': 'Jext',
    'iters': '50',
    'saveFormat': 'txt',
    'UUID': 'tag'
    }   

    EXIT_CODE = drt.main(argv = DRT_commands_and_args_dict)

    sim.delete_folders('tmp',session_path)

    assert EXIT_CODE == 0, 'DRT test failed'
