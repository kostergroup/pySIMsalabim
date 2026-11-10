""" Test the tandem module of pySIMsalabim """

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
from pySIMsalabim.experiments.tandem import *

######### Test Functions #########################################################################
def test_run_tandem_simu():
    """ Test the run_tandem_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')

    simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup_tandem_test.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','SimSS')

    # Set the tandem simulation parameters
    lid_sub1_end = 3
    lid_sub2_start = 4
    rec_contact_type = 1

    ret, mess = run_tandem_simu(simss_device_parameters, session_path, lid_sub1_end, lid_sub2_start, rec_contact_type, plot_JV=False)
    
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.delete_folders('tmp',session_path)

    # If present, remove files that contain 'sub1', or 'sub2'
    for file in os.listdir(session_path):
        if 'sub1' in file or 'sub2' in file:
            if os.path.isfile(os.path.join(session_path, file)):
                os.remove(os.path.join(session_path, file))

    # Check the output
    assert ret == 0, 'tandem simulation failed'

def test_tandem_parallel():
    """ Test the parallel tandem function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup_tandem_test.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','SimSS')

        def run(T,ID): # function to run the tandem simulation in parallel
            # Set the tandem simulation parameters
            lid_sub1_end = 3
            lid_sub2_start = 4
            rec_contact_type = 1
            cmd_pars = [{'par': 'T', 'val': str(T)}]
            print('Running')
            ret, mess = run_tandem_simu(simss_device_parameters, session_path, lid_sub1_end, lid_sub2_start, rec_contact_type,cmd_pars=cmd_pars, UUID=ID, plot_JV = False)

        T_list = [ 295, 310]
        ID_list = [str(uuid.uuid4()) for i in range(len(T_list))] # To test parallel execution, we take T as parameters as it does not depend on the layers

        Parallel(n_jobs=min(len(T_list),10))(delayed(run)(T,ID) for T,ID in zip(T_list,ID_list))

        sim.clean_all_output(session_path)
        sim.delete_folders('tmp',session_path)

        # If present, remove files that contain 'sub1', or 'sub2'
        for file in os.listdir(session_path):
            if 'sub1' in file or 'sub2' in file:
                if os.path.isfile(os.path.join(session_path, file)):
                    os.remove(os.path.join(session_path, file))

    except Exception as e:
        print('Error:',e)
        raise e

if __name__ == '__main__':
    from sim_inputs_setup import prepare_test_inputs, cleanup_test_inputs
    prepare_test_inputs()
    try:
        test_run_tandem_simu()
        test_tandem_parallel()
        print('All tandem tests passed')
    finally:
        cleanup_test_inputs()
