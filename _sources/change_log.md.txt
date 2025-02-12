Change Log
==========
All notable changes to this project will be documented in this file.

v1.01 - 12-02-2025 - SH
-------------------
- Impedance (Version: 2): if the tolerance of the density solver (tolDens) was not strict enough when doing impedance, the calculated spectrum could be wrong/incorrect in some cases due to not high enough accuracy. As a small delta t creates a very large spike in current, we need sufficient accuracy to resolve this, hence the tolerance must be strict enough. We added a function to calculate the tolerance of the density solver to ensure that it is sufficiently strict. It is calculated using tolDens = J(t=∞) - J(t=0) / J_displacement.
- Added internal versioning for experimental scripts, to act as a seperate reference number.

v1 (2024-10-16) 
-------------------
(VMLC-PV)
- Initial release of the project.
- Includes new test and documentation.
- added varFile as an input for the experiment functions.
- added turn_off_autoTidy as a kwargs for the experiment functions to avoid autoTidy when not using threadsafe functions.
- created setup.py and requirements.txt files.