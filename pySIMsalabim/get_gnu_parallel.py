#############################################################################################
################################### install GNU parallel ####################################
#############################################################################################

# Description:
# ------------
# This script contains a function to download SIMsalabim from GitHub and compile it

######### Package Imports ####################################################################

import os,platform,shutil

######### Function Definitions ################################################################

def get_GNU_parallel(verbose=True):
    """Download GNU parallel if on Linux and install it if possible (requires sudo)

    Parameters
    ----------
    verbose : bool, optional
        Print the download progress, by default False


    Returns
    -------
    None

    Raises
    ------
    Exception
        If GNU parallel could not be installed

    """ 
    
    # Check if we are on Linux 
    System = platform.system()                  # Operating system
    is_linux = (System == 'Linux')              # Check if we are on Linux

    if is_linux:
        # check if GNU parallel is installed
        if shutil.which('parallel') == None:
            # Download GNU parallel
            # Requires sudo so we ask if the user has sudo rights
            overwrite = None
            overwrite = input(f'A sudo password is required to install GNU parallel, do you have sudo rights? (y/n): ')
            while overwrite not in ['y','n']:
                print('Please enter y or n')
                overwrite = input(f'A sudo password is required to install GNU parallel, do you have sudo rights? (y/n): ')
            if overwrite == 'n':
                raise Exception('GNU parallel could not be installed')

            # try first with sudo apt-get install parallel
            try:
                os.system('sudo apt-get install parallel')
                if verbose:
                    print('GNU parallel was installed with apt-get install parallel')
            except:
                # if that doesn't work, download GNU parallel from git
                try:
                    os.system('wget http://ftp.gnu.org/gnu/parallel/parallel-latest.tar.bz2')
                    os.system('sudo tar -xjf parallel-latest.tar.bz2')
                    os.system('cd parallel-*/')
                    os.system('sudo ./configure && make')
                    os.system('sudo make install')
                    os.system('rm -rf parallel-*/')
                    os.system('rm parallel-latest.tar.bz2')
                    if verbose:
                        print('GNU parallel was downloaded from git and installed')
                except:
                    print('GNU parallel could not be installed')
                    raise Exception('GNU parallel could not be installed')
        else:
            if verbose:
                print('GNU parallel is already installed')
    else:
        if verbose:
            print('GNU parallel is not installed because you are not on Linux')

            



if __name__ == '__main__':
    
    get_GNU_parallel(verbose=True)
    

    
             