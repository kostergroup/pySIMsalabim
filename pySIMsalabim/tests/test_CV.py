""" Test the CV module of pySIMsalabim """

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
from pySIMsalabim.experiments.CV import *

######### Test Functions #########################################################################

def test_run_CV_simu():
    """ Test the run_CV_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # Set the CV parameters
    tVG_name = os.path.join(session_path,'tVG.txt')
    freq = 1e4
    V_min = -0.8
    V_max = 1.2
    V_step = 0.1
    del_V = 0.01
    G_frac = 0
    # Run the CV simulation
    ret, mess = run_CV_simu(zimt_device_parameters, session_path, freq, V_min, V_max, V_step ,G_frac, del_V,run_mode=False, tVG_name=tVG_name, output_file = 'CapVol.dat', tj_name = 'tj.dat')
    print(ret,mess)
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('CapVol',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    assert ret == 0, 'CV simulation failed'
    
def test_CV_parallel():
    """ Test the CV_parallel function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

        def run(G_frac,ID): # function to run the CV simulation in parallel
            cmd_pars = [{'par': 'R_series', 'val': '1e-4'},{'par': 'R_shunt', 'val': '1e2'},{'par': 'minAcc', 'val': '1e-1'},{'par': 'maxAcc', 'val': '1e-1'}]
            tVG_name = os.path.join(session_path,'tVG.txt')
            freq = 1e4
            V_min = -0.8
            V_max = 1.2
            V_step = 0.1
            del_V = 0.01
            print('Running')
            ret, mess = run_CV_simu(zimt_device_parameters, session_path, freq, V_min, V_max, V_step ,G_frac, del_V,run_mode=False, tVG_name=tVG_name, output_file = 'CapVol.dat', tj_name = 'tj.dat', UUID = ID,cmd_pars=cmd_pars,threadsafe=True)

        Gfracs = [ 0.1,0.5,1]
        ID_list = [str(uuid.uuid4()) for i in range(len(Gfracs))]

        # run the CV simulation in parallel
        Parallel(n_jobs=min(len(Gfracs),10))(delayed(run)(G_frac,ID) for G_frac,ID in zip(Gfracs,ID_list))

        # print('Plotting')
        # plt.figure()
        # for ID,G in zip(ID_list,Gfracs):
        #     plot_capacitance(session_path, output_file=os.path.join(session_path,os.path.join(session_path,'CapVol_'+str(ID)+'.dat')))
        # plt.show()

        sim.clean_all_output(session_path)
        sim.clean_up_output('CapVol',session_path)
        sim.clean_up_output('Gfracs',session_path)
        sim.delete_folders('tmp',session_path)
        assert True
    except Exception as e:
        print(e)
        assert False, 'CV parallel simulation failed'


if __name__ == "__main__":
    test_run_CV_simu()
    test_CV_parallel()
    print('All CV tests passed')