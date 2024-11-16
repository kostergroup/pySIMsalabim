""" Test the impedance module of pySIMsalabim """

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
from pySIMsalabim.experiments.impedance import *

######### Test Functions #########################################################################
def test_run_impedance_simu():
    """ Test the run_impedance_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # Set the impedance parameters
    tVG_name = os.path.join(session_path,'tVG.txt')
    f_min = 1e-1
    f_max = 1e6
    f_steps = 20
    V_0 = 0
    del_V = 0.01
    G_frac = 0
    # Run the impedance simulation
    ret, mess = run_impedance_simu(zimt_device_parameters, session_path,  f_min, f_max, f_steps, V_0, G_frac, del_V, run_mode=False, tVG_name = tVG_name, output_file = 'freqZ.dat', tj_name = 'tj.dat')
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('freqZ',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    assert ret == 0, 'Impedance simulation failed'

def test_impedance_parallel():
    """ Test the impedance_parallel function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

        def run(G_frac,ID): # function to run the impedance simulation in parallel
            cmd_pars = [{'par': 'R_series', 'val': '1e-4'}]
            tVG_name = os.path.join(session_path,'tVG.txt')
            f_min = 1e-1
            f_max = 1e6
            f_steps = 20
            V_0 = 0
            del_V = 0.01
            print('Running')
            ret = run_impedance_simu(zimt_device_parameters, session_path, f_min, f_max, f_steps,  V_0, G_frac, del_V, run_mode=False, tVG_name = tVG_name, output_file = 'freqZ.dat', tj_name = 'tj.dat', UUID = ID,cmd_pars=cmd_pars,threadsafe=True)

        Gfracs = [ 0, 1]
        ID_list = [str(uuid.uuid4()) for i in range(len(Gfracs))]

        Parallel(n_jobs=min(len(Gfracs),10))(delayed(run)(G_frac,ID) for G_frac,ID in zip(Gfracs,ID_list))

        # print('Plotting')
        # plt.figure()
        # for ID,G in zip(ID_list,Gfracs):
        #     data_tj = pd.read_csv(os.path.join(session_path,'freqZ_'+str(ID)+'.dat'), sep=r'\s+')
        #     plt.loglog(data_tj['freq'],data_tj['C']*1e5,label=str(G),marker='o')
        #     plt.legend()
        # plt.show()

        sim.clean_all_output(session_path)
        sim.clean_up_output('freqZ',session_path)
        sim.clean_up_output('Gfracs',session_path)
        sim.delete_folders('tmp',session_path)
    except Exception as e:
        print('Error:',e)
        raise e


if __name__ == '__main__':
    test_run_impedance_simu()
    test_impedance_parallel()
    print('All impedance tests passed')
