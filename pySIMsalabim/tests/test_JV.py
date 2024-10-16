""" Test the JV module of pySIMsalabim """

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
from pySIMsalabim.experiments.JV_steady_state import *

######### Test Functions #########################################################################

def test_run_SS_JV():
    """ Test the run_SS_JV function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','SimSS')
    # Set the JV parameters
    Gfracs = [0.1,0.5,1.0]
    UUID = str(uuid.uuid4())
    # Run the JV simulation
    
    ret, mess = run_SS_JV(simss_device_parameters, session_path, JV_file_name = 'JV.dat', G_fracs = Gfracs, parallel = False, max_jobs = 3, run_mode = False, UUID=UUID, cmd_pars=[{'par': 'l2.L', 'val': '500e-9'}])
    print(ret,mess)
    # Check the output
    assert ret == 0, 'JV simulation failed'

def test_SS_JV_parallel():
    """ Test the SS_JV_parallel function """
    try:
        # check if SIMsalabim folder exists in the current directory
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','SimSS')

        def run(G_frac,ID): # function to run the JV simulation in parallel
            cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
            print('Running')
            res = run_SS_JV(simss_device_parameters, session_path, JV_file_name = 'JV.dat', G_fracs = [G_frac], parallel = False, max_jobs = 3, run_mode = False, UUID=ID, cmd_pars=cmd_pars)
            return res

        # Run the JV simulation in parallel
        Gfracs = [0.1,0.5,1.0]
        ID_list = [str(uuid.uuid4()) for i in range(len(Gfracs))]
        res = Parallel(n_jobs=3)(delayed(run)(Gfrac,ID) for Gfrac,ID in zip(Gfracs,ID_list))
        
        # print('Plotting')
        # plt.figure()
        # for Gfrac,UUID in zip(Gfracs,ID_list):
        #     data = pd.read_csv(os.path.join(session_path,f'JV_Gfrac_{Gfrac}_{UUID}.dat'), sep=r'\s+')
        #     plt.plot(data['Vext'],data['Jext'],label=f'Gfrac = {Gfrac}')
        # plt.xlabel('Vext [V]')
        # plt.ylabel('Current density [A/m^2]')
        # plt.legend()
        # plt.show()

        # sim.clean_all_output(session_path)
        # sim.clean_up_output('Gfracs',session_path)
        # sim.delete_folders('tmp',session_path)
        assert True
    except Exception as e:
        print(e)
        assert False, 'JV parallel simulation failed'


if __name__ == '__main__':
    test_run_SS_JV()
    test_SS_JV_parallel()

    cwd = os.path.abspath('../..')
    session_path = os.path.join(cwd, 'SIMsalabim','SimSS')
    sim.clean_all_output(session_path)
    sim.clean_up_output('Gfracs',session_path)
    sim.delete_folders('tmp',session_path)

    print('All JV tests passed')