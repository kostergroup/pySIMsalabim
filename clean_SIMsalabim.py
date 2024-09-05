import pySIMsalabim as sim
import os, uuid
from pySIMsalabim.experiments.JV_steady_state import *
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from pySIMsalabim.utils.clean_up import clean_all_output,clean_up_output,delete_folders

cwd = os.getcwd()
session_path = os.path.join(cwd, 'SIMsalabim','SimSS')

clean_all_output(session_path)
delete_folders('tmp',session_path)

cwd = os.getcwd()
session_path = os.path.join(cwd, 'SIMsalabim','ZimT')

clean_all_output(session_path)
delete_folders('tmp',session_path)
clean_up_output('scan_speeds',session_path)
clean_up_output('Gfracs',session_path)
clean_up_output('freqZ',session_path)
clean_up_output('CapVol',session_path)
clean_up_output('freqY',session_path)
clean_up_output('tmp',session_path)