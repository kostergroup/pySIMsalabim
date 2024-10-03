
import pySIMsalabim as sim
import os
from pySIMsalabim.experiments.EQE import *
import uuid
from pySIMsalabim.utils.clean_up import clean_all_output,clean_up_output,delete_folders
# get current directory
cwd = os.getcwd()
max_jobs = 4
ID = str(uuid.uuid4())
simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup.txt')
session_path = os.path.join(cwd, 'SIMsalabim','SimSS')
spectrum = os.path.join(cwd, 'SIMsalabim','Data','AM15G.txt')
lambda_min = 300
lambda_max = 800
lambda_step = 10
Vext = 0
outfile_name = 'EQE_'+ID+'.dat'
sim_type = 'simss'

def run(cmd_pars,ID):
    simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','SimSS')
    spectrum = os.path.join(cwd, 'SIMsalabim','Data','AM15G.txt')
    lambda_min = 300
    lambda_max = 800
    lambda_step = 10
    Vext = 0
    outfile_name = 'EQE.dat'
    sim_type = 'simss'

    run_EQE(simss_device_parameters, session_path, spectrum, lambda_min, lambda_max, lambda_step, Vext, outfile_name, JV_file_name = 'JV.dat', run_mode = True, parallel = True, force_multithreading = False, UUID=ID, cmd_pars=cmd_pars,max_jobs=max_jobs, threadsafe = False)

ID1 = str(uuid.uuid4())
ID2 = str(uuid.uuid4())
cmd_pars = [{'par': 'l2.L', 'val': '50e-9'}]
cmd_pars2 = [{'par': 'l2.L', 'val': '300e-9'}]

# wrap it in joblib to run in parallel
from joblib import Parallel, delayed
ID_list = [ID1,ID2]
cmd_list = [cmd_pars,cmd_pars2]
Parallel(n_jobs=2)(delayed(run)(cmd_list[i],ID_list[i]) for i in range(2))



# import pandas as pd
plt.figure()
df = pd.read_csv(os.path.join(session_path,'EQE_'+ID1+'.dat'), sep = r'\s+')
plt.plot(df['lambda'],df['EQE'])

# plt.figure()
df2 = pd.read_csv(os.path.join(session_path,'EQE_'+ID2+'.dat'), sep = r'\s+')
plt.plot(df2['lambda'],df2['EQE'])
plt.show()


clean_all_output(session_path)
clean_up_output('EQE',session_path)
clean_up_output('Gfracs',session_path)
delete_folders('tmp',session_path)