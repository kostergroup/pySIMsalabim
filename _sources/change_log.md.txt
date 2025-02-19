Change Log
==========
All notable changes to this project will be documented in this file.

v1.01 - 18-02-2025 - SH
-------------------
- Impedance.py: If the tolerance of the density solver (tolDens) was not strict enough when doing impedance, the calculated spectrum could be wrong/incorrect in some cases due to not high enough accuracy. As a small delta t creates a very large spike in current, we need sufficient accuracy to resolve this, hence the tolerance must be strict enough. We added a function to calculate the tolerance of the density solver to ensure that it is sufficiently strict. It is calculated using tolDens = J(t=∞) - J(t=0) / J_displacement.
- Impedance.py: Added the option to calculate impedance at open-circuit voltage (Set applied voltage *V<sub>0</sub>* to 'oc'). When set, first the Voc is calculated by SIMsalabim, after which the just calculated Voc is then used as the applied voltage for the impedance calculation.
- Hysteresis.py: Included the calculation of the hysteresis index (HI). THe HI is defined as the area between the forward and backward scan normalised over the spanned area of the curves.


v1 (2024-10-16) 
-------------------
(VMLC-PV)
- Initial release of the project.
- Includes new test and documentation.
- added varFile as an input for the experiment functions.
- added turn_off_autoTidy as a kwargs for the experiment functions to avoid autoTidy when not using threadsafe functions.
- created setup.py and requirements.txt files.