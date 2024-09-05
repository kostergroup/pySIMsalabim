import pySIMsalabim as sim
import os, uuid
from pySIMsalabim.experiments.JV_steady_state import *
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from pySIMsalabim.utils.clean_up import clean_all_output

cwd = os.getcwd()
simss_device_parameters = os.path.join(cwd, 'SIMsalabim','SimSS','simulation_setup.txt')
session_path = os.path.join(cwd, 'SIMsalabim','SimSS')

Gfracs = [0.1,0.5,1.0]
UUID = str(uuid.uuid4())
clean_all_output(session_path)
res = run_SS_JV(simss_device_parameters, session_path, JV_file_name = 'JV.dat', G_fracs = Gfracs, parallel = False, max_jobs = 3, run_mode = False, UUID=UUID, cmd_pars=[{'par': 'l2.L', 'val': '500e-9'}])

# plt.figure()
# for Gfrac in Gfracs:
#     data = pd.read_csv(os.path.join(session_path,f'JV_Gfrac_{Gfrac}_{UUID}.dat'), sep=r'\s+')
#     plt.plot(data['Vext'],data['Jext'],label=f'Gfrac = {Gfrac}')

# plt.xlabel('Vext [V]')
# plt.ylabel('Current density [A/m^2]')
# plt.legend()
plt.show()