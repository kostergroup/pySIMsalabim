Installation
================================

With pip
**********************
To install pySIMsalabim with pip you have two options:
1. Install pySIMsalabim using the `PyPI repository <https://pypi.org/project/pySIMsalabim />`_

.. code-block:: bash

    pip install pySIMsalabim 


2. Install pySIMsalabim using the GitHub repository
First, you need to clone the repository and install the requirements. The requirements can be installed with the following command:

.. code-block:: bash

    pip install -r requirements.txt

Similarly to the conda installation, if you plan on using the BoTorch/Ax optimizer you need to use the requirements_torch_CPU.txt file or install pytorch with the correct version for your system with the requirements.txt file.


With conda
**********************
To install the pySIMsalabim, you need to clone the repository and install the requirements. The requirements can be installed with the following command:

.. code-block:: bash

    conda create -n pySIMsalabim 
    conda activate pySIMsalabim
    conda install --file requirements.txt

if you want you can also clone your base environment by replacing the first line with:

.. code-block:: bash

    conda create -n pySIMsalabim --clone base



Additional necessary installs for the drift-diffusion software
===============================================================
SIMsalabim
***********************
The drift-diffusion simulations are ran using the `SIMsalabim <https://github.com/kostergroup/SIMsalabim>`_ package.
Therefore you need to install SIMsalabim prior to running any simulations.

All the details to install SIMsalabim are detailed in the `GitHub repository <https://github.com/kostergroup/SIMsalabim>`_. To make sure that you are running the latest version of SIMsalabim, check regularly the repository.
You can also install SIMsalabim by running the following python script:

.. code-block:: python

    import os
    import pySIMsalabim
    from pySIMsalabim.install.get_SIMsalabim import *

    cwd = os.getcwd()
    install_SIMsalabim(cwd)

Free Pascal Compiler
***********************
SIMsalabim needs the Free Pascal Compiler to compile the Pascal code, in the previous step up you have the option to use the precompiled binaries from the SIMsalabim repository (for Windows and Linux). If you want to compile the code yourself, you need to install the Free Pascal Compiler. The Free Pascal Compiler can be installed on Linux by running the following command:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install fp-compiler

Running the install_SIMsalabim function will also install the Free Pascal Compiler for you if you are on Linux.  
For Windows, you can download the Free Pascal Compiler from the `Free Pascal website <https://www.freepascal.org/download.html>`_.

You can test if the installation worked by running the following command in the terminal:

.. code-block:: bash

    fpc -iV

Which should return the version of the Free Pascal Compiler. Note that the version of the Free Pascal Compiler should be 3.2.2 or higher.

Parallel simulations
***********************
On Linux, you have the option to run the simulations in using the `GNU parallel <https://www.gnu.org/software/parallel/>`_ package instead of the default threading or multiprocessing from python.
To install on linux run in the terminal:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install parallel

You can also use `Anaconda <https://anaconda.org/>`_:

.. code-block:: bash

    conda install -c conda-forge parallel

To test is the installation worked by using by running the following command in the terminal:

.. code-block:: bash

    parallel --help

Alternatively you can run the following python script to install GNU parallel:

.. code-block:: python

    import os
    import pySIMsalabim
    from pySIMsalabim.install.get_gnu_parallel import *

    install_GNU_parallel_Linux()

If you are on Windows, pySIMsalabim will use the default threading or multiprocessing from python.

Testing
================================
The physics and implementation of the drift-diffusion simulator are tested in the main SIMsalabim repository. The tests in pySIMsalabim are mainly focused on the interface between SIMsalabim and Python. The tests can be run using the following command:

.. code-block:: bash

    pytest pySIMsalabim

Note that pytest needs to be installed to run the tests. You can install pytest by running the following command:

.. code-block:: bash

    pip install pytest

Disclaimer
================================
This repository is still under development. If you find any bugs or have any questions, please contact us.