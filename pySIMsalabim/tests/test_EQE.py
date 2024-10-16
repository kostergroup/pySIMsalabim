""" Test EQE module with pySIMsalabim"""

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
from pySIMsalabim.experiments.EQE import *

######### Test Functions #########################################################################

def test_run_EQE():
    """ Test the run_EQE function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','SimSS')
    spectrum = os.path.join(cwd, 'SIMsalabim','Data','AM15G.txt')
    lambda_min = 300
    lambda_max = 800
    lambda_step = 10
    Vext = 0
    outfile_name = 'EQE.dat'
    sim_type = 'simss'
    # Run the EQE simulation
    ret, mess = run_EQE(simss_device_parameters, session_path, spectrum, lambda_min, lambda_max, lambda_step, Vext, outfile_name = outfile_name, JV_file_name = 'JV.dat', run_mode = False, parallel = False, force_multithreading = False, UUID=str(uuid.uuid4()), cmd_pars=[{'par': 'l2.L', 'val': '50e-9'}],threadsafe=False)
    print(ret,mess)
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('EQE',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    assert ret == 0, 'EQE simulation failed'

def test_EQE_parallel():
    """ Test the EQE_parallel function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        session_path = os.path.join(cwd, 'SIMsalabim','SimSS')

        def run(cmd_pars,ID):
            simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup.txt')
            session_path = os.path.join(cwd, 'SIMsalabim','SimSS')
            spectrum = os.path.join(cwd, 'SIMsalabim','Data','AM15G.txt')
            lambda_min = 300
            lambda_max = 800
            lambda_step = 10
            Vext = 0
            outfile_name = 'EQE.dat'
            print('Running')
            run_EQE(simss_device_parameters, session_path, spectrum, lambda_min, lambda_max, lambda_step, Vext, outfile_name = outfile_name, JV_file_name = 'JV.dat', run_mode = True, parallel = True, force_multithreading = False, UUID=ID, cmd_pars=cmd_pars,max_jobs=4, threadsafe = False)

        ID1 = str(uuid.uuid4())
        ID2 = str(uuid.uuid4())
        cmd_pars = [{'par': 'l2.L', 'val': '50e-9'}]
        cmd_pars2 = [{'par': 'l2.L', 'val': '300e-9'}]

        # wrap it in joblib to run in parallel
        ID_list = [ID1,ID2]
        cmd_list = [cmd_pars,cmd_pars2]
        Parallel(n_jobs=2)(delayed(run)(cmd_list[i],ID_list[i]) for i in range(2))

        # print('Plotting')
        # plt.figure()
        # df = pd.read_csv(os.path.join(session_path,'EQE_'+ID1+'.dat'), sep = r'\s+')
        # plt.plot(df['lambda'],df['EQE'])

        # # plt.figure
        # df2 = pd.read_csv(os.path.join(session_path,'EQE_'+ID2+'.dat'), sep = r'\s+')
        # plt.plot(df2['lambda'],df2['EQE'])
        # plt.show()

        sim.clean_all_output(session_path)
        sim.clean_up_output('EQE',session_path)
        sim.delete_folders('tmp',session_path)
        assert True
    except Exception as e:
        print(e)
        assert False, 'EQE parallel simulation failed'

if __name__ == '__main__':
    test_run_EQE()
    test_EQE_parallel()
    print('All EQE tests passed')

