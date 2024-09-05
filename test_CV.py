import pySIMsalabim as sim
import os, uuid
import pandas as pd
from pySIMsalabim.experiments.CV import *
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from pySIMsalabim.utils.clean_up import clean_all_output,clean_up_output

cwd = os.getcwd()
zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

# clean_all_output(session_path)

def run(G_frac,ID):
    cwd = os.getcwd()
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # scan_speed = 0.1
    cmd_pars = [{'par': 'R_series', 'val': '1e-4'},{'par': 'R_shunt', 'val': '1e2'},{'par': 'minAcc', 'val': '1e-1'},{'par': 'maxAcc', 'val': '1e-1'}]
    direction = -1
    # G_frac = 0
    tVG_name = os.path.join(session_path,'tVG.txt')
    freq = 1e4
    V_min = -0.8
    V_max = 1.2
    V_step = 0.1
    del_V = 0.01
    # G_frac = 1
    print('Running')
    res = run_CV_simu(zimt_device_parameters, session_path, tVG_name, freq, V_min, V_max, del_V, V_step ,G_frac, run_mode=False, output_file = 'CapVol.dat', tj_name = 'tj.dat', UUID = ID,cmd_pars=cmd_pars,threadsafe=True)

G_frac = 0
tVG_name = os.path.join(session_path,'tVG.txt')
f_min = 1e-1
f_max = 1e6
f_steps = 20
V_0 = 0
del_V = 0.01
Gfracs = [ 0.1,0.5,1]
ID_list = [str(uuid.uuid4()) for i in range(len(Gfracs))]

df = pd.DataFrame({'ID':ID_list,'G_frac':Gfracs})
# save the dataframe to a csv file
# df.to_csv(os.path.join(session_path,'Gfracs.csv'),index=False)

# res = run_impedance_simu(zimt_device_parameters, session_path, tVG_name, f_min, f_max, f_steps, V_0, del_V, G_frac, run_mode=False, output_file = 'freqZ.dat', tj_name = 'tj.dat')#, UUID = ID_list[0])
# print(res)
Parallel(n_jobs=min(len(Gfracs),10))(delayed(run)(G_frac,ID) for G_frac,ID in zip(Gfracs,ID_list))

# data_tj = pd.read_csv(os.path.join(session_path,'tj.dat'), sep=r'\s+')




print('Plotting')
plt.figure()
for ID,G in zip(ID_list,Gfracs):
    data_tj = pd.read_csv(os.path.join(session_path,'CapVol_'+str(ID)+'.dat'), sep=r'\s+')
    # data_tj = pd.read_csv(os.path.join(session_path,'freqZ.dat'), sep=r'\s+')
    # pars = {'Jext' : str(speed)} #'$J_{ext}$'}
    # plt.plot(data_tj['V'],1/(data_tj['C']*1e2)**2,label=str(G),marker='o')
    # plt.legend()
    plot_capacitance(session_path, output_file=os.path.join(session_path,os.path.join(session_path,'CapVol_'+str(ID)+'.dat')))
    # plot_impedance(session_path, output_file=os.path.join(session_path,'freqZ.dat'))
    # ax = utils_plot_gen.plot_result(data_tj, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type)
plt.show()

# print('freqZ_'+str(ID)+'.dat')

clean_all_output(session_path)
clean_up_output('CapVol',session_path)
clean_up_output('Gfracs',session_path)