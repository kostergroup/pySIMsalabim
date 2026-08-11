""" Test the trPL module of pySIMsalabim """

######### Package Imports #########################################################################
import os, sys, uuid 
import pandas as pd
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
try :
    import pySIMsalabim as sim
except ImportError:
    # Add the parent directory to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import pySIMsalabim as sim
from pySIMsalabim.experiments.trPL import *

######### Test Functions #########################################################################
def test_run_trPL_simu():
    """ Test the run_trPL_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')

    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

    # Set the trPL parameters
    lyr_idx = 1
    t_max = 1E-7
    t_step = 1E-9
    t_pulse = 10E-9
    t_scale = 'log'
    FWHM = 3E-9
    ret, mess = run_trPL_simu(zimt_device_parameters, session_path, lyr_idx, t_max, t_scale, t_step, t_pulse, FWHM, output_file = 'trPL.dat', tj_name = 'tj.dat')

    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('trPL',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    assert ret == 0, 'trPL simulation failed'

def test_trPL_parallel():
    """ Test the trPL function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

        def run(T,ID): # function to run the trPL simulation in parallel
            lyr_idx = 1
            t_max = 1E-7
            t_step = 1E-9
            t_pulse = 10E-9
            t_scale = 'log'
            FWHM = 3E-9
            cmd_pars = [{'par': 'T', 'val': str(T)}]
            print('Running')
            ret, mess = run_trPL_simu(zimt_device_parameters, session_path, lyr_idx, t_max, t_scale, t_step, t_pulse, FWHM, run_mode=False, output_file = 'trPL.dat', tj_name = 'tj.dat', UUID = ID, threadsafe=False, cmd_pars=cmd_pars)

        T_list = [ 295, 310]
        ID_list = [str(uuid.uuid4()) for i in range(len(T_list))] # To test parallel execution, we take T as parameters as it does not depend on the layers

        Parallel(n_jobs=min(len(T_list),10))(delayed(run)(T,ID) for T,ID in zip(T_list,ID_list))

        sim.clean_all_output(session_path)
        sim.clean_up_output('trPL',session_path)
        sim.delete_folders('tmp',session_path)
    except Exception as e:
        print('Error:',e)
        raise e


if __name__ == '__main__':
    test_run_trPL_simu()
    test_trPL_parallel()
    print('All trPL tests passed')
