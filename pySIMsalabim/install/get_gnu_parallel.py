""" install GNU parallel"""
# Description:
# ------------
# This script contains a function to download SIMsalabim from GitHub and compile it

######### Package Imports ####################################################################

import os,shutil,sys, getpass

######### Function Definitions ################################################################

# def install_parallel_Linux():
#     """ Install GNU Parallel on Linux
#     """   
#     # check if system is Linux
#     if os.name != 'posix':
#         print('This function is only available on Linux systems')
#         sys.exit()
    
#     # check if apt-get is available
#     if shutil.which("apt-get") is None:
#         print('apt-get is not available on this system')
#         sys.exit()

#     # Install GNU Parallel
#     password = getpass('Sudo password:')
#     # run the command sudo apt-get install parallel and enter the password and print the output
#     os.system('echo {} | sudo -S apt-get install parallel'.format(password))

def install_GNU_parallel_Linux(verbose=True):
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
    
    if os.name == 'posix': # Check if we are on Linux
        # check if GNU parallel is installed
        if shutil.which('parallel') == None:
            # Download GNU parallel
            # Requires sudo so we ask if the user has sudo rights
            overwrite = None
            overwrite = input(f'A sudo password is required to install GNU parallel, do you have sudo rights? (y/n): ')
            while overwrite.lower() not in ['y','n','yes','no']:
                print('Please enter y or n')
                overwrite = input(f'A sudo password is required to install GNU parallel, do you have sudo rights? (y/n): ')
            if overwrite.lower() == 'n' or overwrite.lower() =='no':
                raise Exception('GNU parallel could not be installed')

            # try first with sudo apt-get install parallel
            try:
                # check if apt-get is available
                if shutil.which("apt-get") is None:
                    print('apt-get is not available on this system')
                    sys.exit()
                # Install GNU Parallel
                password = getpass('Sudo password:')
                # run the command sudo apt-get install parallel and enter the password and print the output
                os.system('echo {} | sudo -S apt-get install parallel'.format(password))
                # os.system('sudo apt-get install parallel')
                if verbose:
                    print('GNU parallel was installed with apt-get install parallel')
            except:
                # if that doesn't work, download GNU parallel from git
                try:
                    password = getpass('Sudo password:')
                    os.system('wget http://ftp.gnu.org/gnu/parallel/parallel-latest.tar.bz2')
                    os.system('echo {} | sudo -S tar -xjf parallel-latest.tar.bz2'.format(password))
                    os.system('cd parallel-*/')
                    os.system('echo {} | sudo -S ./configure && make'.format(password))
                    os.system('echo {} | sudo -S  sudo make install'.format(password))
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
    
    install_GNU_parallel_Linux(verbose=True)
    

    
             