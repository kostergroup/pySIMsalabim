""" Test the hysteresis module of pySIMsalabim """

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
from pySIMsalabim.experiments.hysteresis import *

######### Test Functions #########################################################################

def test_run_hysteresis_simu():
    """ Test the run_hysteresis_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # Set the hysteresis parameters
    scan_speed = 0.1
    cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
    direction = -1
    G_frac = 1
    tVG_name = os.path.join(session_path,'tVG.txt')
    Vmin = 0.0
    Vmax = 1.3
    steps = 200
    # Run the hysteresis simulation
    ret, mess, rms = Hysteresis_JV(zimt_device_parameters, session_path, 0, scan_speed, direction, G_frac, tVG_name, run_mode=False, Vmin=Vmin, Vmax=Vmax, steps = steps, expJV_Vmin_Vmax='', expJV_Vmax_Vmin='',rms_mode='lin',threadsafe=False,expo_mode = False, Vminexpo = 5e-3, UUID=str(uuid.uuid4()), cmd_pars=cmd_pars)
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('hysteresis',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    # print(ret)
    assert ret == 0, 'Hysteresis simulation failed'

def test_hysteresis_parallel():
    """ Test the hysteresis_parallel function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

        def run(scan_speed,ID): # function to run the hysteresis simulation in parallel
            cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
            direction = -1
            G_frac = 1
            tVG_name = os.path.join(session_path,'tVG.txt')
            Vmin = 0.0
            Vmax = 1.3
            steps = 200
            print('Running')
            ret, mess, rms = Hysteresis_JV(zimt_device_parameters, session_path, 0, scan_speed, direction, G_frac, tVG_name, run_mode=False, Vmin=Vmin, Vmax=Vmax, steps = steps, expJV_Vmin_Vmax='', expJV_Vmax_Vmin='',rms_mode='lin',threadsafe=True,expo_mode = False, Vminexpo = 5e-3, UUID=ID, cmd_pars=cmd_pars)

        scan_speeds = np.logspace(-3,3,7)
        ID_list = [str(uuid.uuid4()) for i in range(len(scan_speeds))]

        Parallel(n_jobs=min(len(scan_speeds),10))(delayed(run)(scan_speed,ID) for scan_speed,ID in zip(scan_speeds,ID_list))

        # print('Plotting')
        # plt.figure()
        # for ID,speed in zip(ID_list,scan_speeds):
        #     data_tj = pd.read_csv(os.path.join(session_path,'tj_'+str(ID)+'.dat'), sep=r'\s+')
        #     plt.plot(data_tj['Vext'],data_tj['Jext'],label=str(speed),marker='o')
        #     plt.legend()
        # plt.show()

        sim.clean_all_output(session_path)
        sim.clean_up_output('hysteresis',session_path)
        sim.delete_folders('tmp',session_path)
        assert True
    except Exception as e:
        print(e)
        assert False, 'Hysteresis parallel simulation failed'


if __name__ == '__main__':
    test_run_hysteresis_simu()
    test_hysteresis_parallel()
    print('All hysteresis tests passed')
