""" Test the IMPS module of pySIMsalabim """

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
from pySIMsalabim.experiments.imps import *

######### Test Functions #########################################################################

def test_run_IMPS_simu():
    """ Test the run_IMPS_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # Set the IMPS parameters
    tVG_name = os.path.join(session_path,'tVG.txt')
    f_min = 1e2
    f_max = 1e6
    f_steps = 20
    V = 0
    G_frac = 1
    GStep = 0.05
    # Run the IMPS simulation
    ret, mess = run_IMPS_simu(zimt_device_parameters, session_path, f_min, f_max, f_steps, V, G_frac, GStep, run_mode=False, tVG_name =tVG_name, output_file = 'freqY.dat', tj_name = 'tj.dat')
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('freqY',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    assert ret == 0, 'IMPS simulation failed'

def test_IMPS_parallel():
    """ Test the IMPS_parallel function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

        def run(G_frac,ID): # function to run the IMPS simulation in parallel
            cmd_pars = [{'par': 'R_series', 'val': '1e-4'},{'par': 'R_shunt', 'val': '1e2'},{'par': 'minAcc', 'val': '1e-1'},{'par': 'maxAcc', 'val': '1e-1'}]
            tVG_name = os.path.join(session_path,'tVG.txt')
            f_min = 1e2
            f_max = 1e6
            f_steps = 20
            V = 0
            GStep = 0.05
            print('Running')
            ret, mess = run_IMPS_simu(zimt_device_parameters, session_path, f_min, f_max, f_steps, V, G_frac, GStep, run_mode=False, tVG_name =tVG_name, output_file = 'freqY.dat', tj_name = 'tj.dat', UUID = ID,cmd_pars=cmd_pars,threadsafe=True)

        Gfracs = [ 0.1,0.5,1]
        ID_list = [str(uuid.uuid4()) for i in range(len(Gfracs))]
        Parallel(n_jobs=min(len(Gfracs),10))(delayed(run)(G_frac,ID) for G_frac,ID in zip(Gfracs,ID_list))

        # print('Plotting')
        # plt.figure()
        # for ID,G in zip(ID_list,Gfracs):
        #     data_tj = pd.read_csv(os.path.join(session_path,'freqY_'+str(ID)+'.dat'), sep=r'\s+')
        #     # data_tj = pd.read_csv(os.path.join(session_path,'freqZ.dat'), sep=r'\s+')
        #     # pars = {'Jext' : str(speed)} #'$J_{ext}$'}
        #     plt.plot(data_tj['V'],1/(data_tj['C']*1e2)**2,label = str(G),marker='o')
        #     plt.legend()
        # plt.show()

        sim.clean_all_output(session_path)
        sim.clean_up_output('freqY',session_path)
        sim.clean_up_output('Gfracs',session_path)
        sim.delete_folders('tmp',session_path)
        assert True
    except Exception as e:
        print(e)
        assert False, 'IMPS parallel simulation failed'


if __name__ == '__main__':
    test_run_IMPS_simu()
    test_IMPS_parallel()
    print('All IMPS tests passed')