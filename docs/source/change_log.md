Change Log
==========
All notable changes to this project will be documented in this file.

v1.04 - 2025-12-10 - VMLC-PV
------------------------------------
- Removing the limitation for the numpy version in setup.py to allow for more flexibility in the numpy version used. Previously the version was constrained to be >=1.2 and <=2.0.0.

v1.03 - 2025-09-24 - VMLC-PV
------------------------------------
- JV_steady_state.py, hysteresis.py, impedance.py, imps.py, EQE.py, CV.py: Added verbose output option for simulation functions made sure that we only return an integer (return code) and a message (string) from the simulation functions. This is to ensure that the return value is always an integer, never an object.
- general.py: remade the 'error_message' function to provide more informative error messages and implemented an error code 666 when multiple simulations ran in parallel failed with different error messages.
- parallel_sim.py: made the parallel output consitent between linux and windows. Improved error message when error code 91 is returned to make it easier to find which input parameters caused the error.
- JV_sweep.py: added a new experiment to perform single sweep JV simulations using zimt.
- Added a warning for Windows users in the README.md about the maximum path length of 260 characters in Windows and the issues it can cause when running simulations. Recommended to use Linux or WSL2 instead of Windows. Also created the PathChecksWin.py file to handle long paths in Windows by adding the \\?\ prefix to paths longer than 260 characters, which might help in some cases.
- Fixed some bug in the test files for the EQE simulations.

v1.02 - 2025-04-28 - VMLC-PV, SH, FE
------------------------------------
- general.py: Modified the construct_cmd to work on Windows by adding "" around the parameter names and values.
- Impedance.py: Let the function 'run_impedance_simu' return a result and message. With this update, 'result' is always a number, never an object. Handle failed to converge Voc simulation.
- Hysteresis.py: removed np.trapezoid and replaced it with scipy.integrate.trapezoid, small update to the message output.
- addons.py: Added some very simple functions to calculate the performance metrics of the solar cell. 
- get_SIMsalabim.py: fix some indentation issues.
- Removed redundant SIMsalabim folder.
- update docs.


v1.01 - 18-02-2025 - SH
------------------------
- Impedance.py: If the tolerance of the density solver (tolDens) was not strict enough when doing impedance, the calculated spectrum could be wrong/incorrect in some cases due to not high enough accuracy. As a small delta t creates a very large spike in current, we need sufficient accuracy to resolve this, hence the tolerance must be strict enough. We added a function to calculate the tolerance of the density solver to ensure that it is sufficiently strict. It is calculated using tolDens = J(t=∞) - J(t=0) / J_displacement.
- Impedance.py: Added the option to calculate impedance at open-circuit voltage (Set applied voltage *V<sub>0</sub>* to 'oc'). When set, first the Voc is calculated by SIMsalabim, after which the just calculated Voc is then used as the applied voltage for the impedance calculation.
- Hysteresis.py: Included the calculation of the hysteresis index (HI). The HI is defined as the area between the forward and backward scan normalised over the spanned area of the curves.


v1 - 2024-10-16 - VMLC-PV
--------------------------
- Initial release of the project.
- Includes new test and documentation.
- added varFile as an input for the experiment functions.
- added turn_off_autoTidy as a kwargs for the experiment functions to avoid autoTidy when not using threadsafe functions.
- created setup.py and requirements.txt files.