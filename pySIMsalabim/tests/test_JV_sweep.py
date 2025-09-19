""" Test the JV_sweep module of pySIMsalabim """

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
from pySIMsalabim.experiments.JV_sweep import *

######### Test Functions #########################################################################

def test_run_JV_sweep_simu():
    """ Test the run_JV_sweep_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # Set the JV_sweep parameters
    scan_speed = 0.1
    cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
    direction = -1
    G_frac = 1
    tVG_name = os.path.join(session_path,'tVG.txt')
    Vmin = 0.0
    Vmax = 1.3
    steps = 200
    # Run the JV_sweep simulation
    ret, mess, rms = JV_sweep(zimt_device_parameters, session_path, 0, scan_speed, direction, G_frac, tVG_name, run_mode=False, Vmin=Vmin, Vmax=Vmax, steps = steps, expJV_Vmin_Vmax='', expJV_Vmax_Vmin='',rms_mode='lin',threadsafe=False,expo_mode = False, Vminexpo = 5e-3, UUID=str(uuid.uuid4()), cmd_pars=cmd_pars)
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('JV_sweep',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    # print(ret)
    assert ret == 0, 'JV_sweep simulation failed'

def test_run_JV_sweep_logstep_simu():
    """ Test the test_run_JV_sweep_logstep_simu function """
    # Set the path to the simulation setup file
    if os.path.exists('SIMsalabim'):
        cwd = os.path.abspath('.')
    else:
        cwd = os.path.abspath('../..')
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # Set the JV_sweep parameters
    scan_speed = 0.1
    cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
    direction = -1
    G_frac = 1
    tVG_name = os.path.join(session_path,'tVG.txt')
    Vmin = 0.0
    Vmax = 1.3
    steps = 200
    Vdist = 2
    Vacc = -1e-2
    # Run the JV_sweep simulation
    ret, mess, rms = JV_sweep(zimt_device_parameters, session_path, 0, scan_speed, direction, G_frac, tVG_name, run_mode=False, Vmin=Vmin, Vmax=Vmax, steps = steps, expJV_Vmin_Vmax='', expJV_Vmax_Vmin='',rms_mode='lin',threadsafe=False,expo_mode = False, Vminexpo = 5e-3, UUID=str(uuid.uuid4()), cmd_pars=cmd_pars, Vdist=Vdist, Vacc=Vacc)
    # Clean up the output
    sim.clean_all_output(session_path)
    sim.clean_up_output('JV_sweep',session_path)
    sim.delete_folders('tmp',session_path)
    # Check the output
    # print(ret)
    assert ret == 0, 'JV_sweep with logarithmic voltage steps simulation failed'

def test_JV_sweep_parallel():
    """ Test the JV_sweep_parallel function """
    try:
        if os.path.exists('SIMsalabim'):
            cwd = os.path.abspath('.')
        else:
            cwd = os.path.abspath('../..')
        zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
        session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

        def run(scan_speed,ID): # function to run the JV_sweep simulation in parallel
            cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
            direction = -1
            G_frac = 1
            tVG_name = os.path.join(session_path,'tVG.txt')
            Vmin = 0.0
            Vmax = 1.3
            steps = 200
            print('Running')
            ret, mess, rms = JV_sweep(zimt_device_parameters, session_path, 0, scan_speed, direction, G_frac, tVG_name, run_mode=False, Vmin=Vmin, Vmax=Vmax, steps = steps, expJV_Vmin_Vmax='', expJV_Vmax_Vmin='',rms_mode='lin',threadsafe=True,expo_mode = False, Vminexpo = 5e-3, UUID=ID, cmd_pars=cmd_pars)

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
        sim.clean_up_output('JV_sweep',session_path)
        sim.delete_folders('tmp',session_path)
        assert True
    except Exception as e:
        print(e)
        assert False, 'JV_sweep parallel simulation failed'


if __name__ == '__main__':
    test_run_JV_sweep_simu()
    test_JV_sweep_parallel()
    test_run_JV_sweep_logstep_simu()
    print('All JV_sweep tests passed')
