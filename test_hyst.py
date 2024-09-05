
import pySIMsalabim as sim
import os, uuid
from pySIMsalabim.experiments.hysteresis import *
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from pySIMsalabim.utils.clean_up import clean_all_output

# session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
def run(scan_speed,ID):
    cwd = os.getcwd()
    zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
    session_path = os.path.join(cwd, 'SIMsalabim','ZimT')
    # scan_speed = 0.1
    cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
    direction = -1
    G_frac = 1
    tVG_name = os.path.join(session_path,'tVG.txt')
    Vmin = 0.0
    Vmax = 1.3
    steps = 200
    print('Running')
    Hysteresis_JV(zimt_device_parameters, session_path, 0, scan_speed, direction, G_frac, tVG_name, run_mode=False, Vmin=Vmin, Vmax=Vmax, steps = steps, expJV_Vmin_Vmax='', expJV_Vmax_Vmin='',rms_mode='lin',threadsafe=True,expo_mode = False, Vminexpo = 5e-3, UUID=ID, cmd_pars=cmd_pars)
    

cwd = os.getcwd()
zimt_device_parameters = os.path.join(cwd, 'SIMsalabim','ZimT','simulation_setup.txt')
session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

clean_all_output(session_path)
# ID1 = str(uuid.uuid4())
# ID2 = str(uuid.uuid4())
scan_speeds = np.logspace(-3,3,7)
ID_list = [str(uuid.uuid4()) for i in range(len(scan_speeds))]

df = pd.DataFrame({'ID':ID_list,'scan_speed':scan_speeds})
# save the dataframe to a csv file
df.to_csv(os.path.join(session_path,'scan_speeds.csv'),index=False)
# cmd_pars = [{'par': 'l2.L', 'val': '500e-9'}]
# cmd_pars2 = [{'par': 'l2.L', 'val': '300e-9'}]

# wrap it in joblib to run in parallel

# ID_list = [ID1,ID2]
# cmd_list = [cmd_pars,cmd_pars2]
Parallel(n_jobs=min(len(scan_speeds),10))(delayed(run)(scan_speed,ID) for scan_speed,ID in zip(scan_speeds,ID_list))


# data_tj = pd.read_csv(os.path.join(session_path,'tj.dat'), sep=r'\s+')
    
# fig, ax = plt.subplots()
# pars = {'Jext' : 'Simulation'} #'$J_{ext}$'}
# par_x = 'Vext'
# xlabel = '$V_{ext}$ [V]'
# ylabel = 'Current density [Am$^{-2}$]'
# xscale = 'log'
# yscale = 'log'
# title = 'JV curve'
# plot_type = plt.plot

print('Plotting')
plt.figure()
for ID,speed in zip(ID_list,scan_speeds):
    data_tj = pd.read_csv(os.path.join(session_path,'tj_'+str(ID)+'.dat'), sep=r'\s+')
    pars = {'Jext' : str(speed)} #'$J_{ext}$'}
    plt.plot(data_tj['Vext'],data_tj['Jext'],label=str(speed),marker='o')
    plt.legend()
    # ax = utils_plot_gen.plot_result(data_tj, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type)



# data_tj = pd.read_csv(os.path.join(session_path,'tj_'+str(ID1)+'.dat'), sep=r'\s+')
# ax = utils_plot_gen.plot_result(data_tj, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type)

# data_tj = pd.read_csv(os.path.join(session_path,'tj_'+str(ID2)+'.dat'), sep=r'\s+')
# ax = utils_plot_gen.plot_result(data_tj, pars, list(pars.keys()), par_x, xlabel, ylabel, xscale, yscale, title, ax, plot_type)


plt.show()
