import sys, os, subprocess, shutil, json, requests, zipfile, io
from packaging import version
from pathlib import Path
from getpass import getpass

######### Parameter Definitions ###################################################################
cwd = Path.cwd()
folder_name = 'kostergroup-SIMsalabim-'
min_fpc_version = '3.2.0'

######### Function Definitions ####################################################################
def cmd_yes_no_question(question, default = "yes"):
    """_summary_

    Parameters
    ----------
    question : str
        question to ask the user
    default : str, optional
        default answer, by default "yes"

    Returns
    -------
    bool
        whether the default answer is valid or not

    Raises
    ------
    ValueError
        If the default answer is not valid
    """    
    # valid answers (yes/no)
    valid = {'yes' : True, 'y': True, 'ye': True, 'no': False, 'n': False}
    # Set the default answer.
    if default is None:
        prompt = " [y/n] "
    elif default == 'yes':
        prompt = " [Y/n] "
    elif default == 'no':
        prompt = " [y/N] "
    else:
        raise ValueError(f"Invalid default answer: {default}\n")
    
    while True:
        # Capture user input
        sys.stdout.write(question + prompt)
        choice = input(question + prompt)
        # convert the input to lowercase
        choice = choice.lower()
        if default is not None and choice == "":
            # Use default value
            return valid[default]
        elif choice in valid:
            # Use user input
            return valid[choice]
        else:
            # Incorrect input
            sys.stdout.write('Please respond with "y" or "n"\n')

def clear_current_working_directory(cwd, folder_name='kostergroup-SIMsalabim-'):
    """_summary_

    Parameters
    ----------
    cwd : string
        Current working directory
    folder_name : string, optional
        Name of the folder to download, by default 'kostergroup-SIMsalabim-'

    Returns
    -------
    bool
        Whether the folder was removed or not

    """    
    # Clear the current working directory
    for dirpath, dirnames, files in os.walk(cwd):
        for dirname in dirnames:
            if dirname.startswith(folder_name):
                result = cmd_yes_no_question(f"Are you sure you want to overwrite the {dirname} folder?")
                if result == True:
                    shutil.rmtree(os.path.join(cwd,dirname))
                    print(f"Found and removed a folder named {dirname}")
                    return True
                elif result is False:
                    print(f"Not allowed to write into folder {dirname}")
                    return False
            else:
                # print(f"No folder found named SIMsalabim, continue.")
                return True

def get_SIMsalabim_source(cwd, folder_name='kostergroup-SIMsalabim-',verbose=False):
    """ Get the latest release from the Kostergroup Github

    Parameters
    ----------
    cwd : string
        Current working directory
    folder_name : string, optional
        Name of the folder to download, by default 'kostergroup-SIMsalabim-'
    verbose : bool, optional
        Print verbose output, by default False

    Returns
    -------
    int

    0 : Success
    2 : Failed
    3 : Failed

    """    
    if verbose:
        print("Getting the latest release from the Kostergroup Github")
    # Get the SIMsalabim source code.
    if os.path.exists(os.path.join(cwd, 'SIMsalabim')):
    # Pop out dialog box to confirm overwriting
        result = cmd_yes_no_question("Are you sure you want to overwrite the 'SIMsalabim' folder?")
        if result == True:
            # Remove folder
            shutil.rmtree(os.path.join(cwd, 'SIMsalabim'))

            # # Get the files from the latest release
            url = 'https://api.github.com/repos/kostergroup/SIMsalabim/zipball'
            response = requests.get(url)

            # Open the zip file
            z = zipfile.ZipFile(io.BytesIO(response.content))

            # Extract all the files
            z.extractall(path=cwd)

            for dirpath, dirnames, files in os.walk(cwd):
                for dirname in dirnames:
                    if dirname.startswith(folder_name):
                        # Rename folder
                        shutil.move(os.path.join(cwd, dirname), os.path.join(cwd, 'SIMsalabim'))
                        print("\nGot the latest release of SIMsalabim")
                        return 0
        else:
            print('We keep the current SIMsalabim version')
            return 0
    else:
        # # Get the files from the latest release
        url = 'https://api.github.com/repos/kostergroup/SIMsalabim/zipball'
        response = requests.get(url)

        # Open the zip file
        z = zipfile.ZipFile(io.BytesIO(response.content))

        # Extract all the files
        z.extractall(path=cwd)

        for dirpath, dirnames, files in os.walk(cwd):
            for dirname in dirnames:
                if dirname.startswith(folder_name):
                    # print(f"Found a folder named {dirname}")
                    # Rename folder
                    shutil.move(os.path.join(cwd, dirname), os.path.join(cwd, 'SIMsalabim'))
                    print("\nGot the latest release of SIMsalabim")
                    return 0

def get_SIMsalabim_assets(cwd,folder_name='kostergroup-SIMsalabim-',verbose=False):
    """ Get the latest compiled binaries from the Kostergroup Github

    Parameters
    ----------
    cwd : string
        Current working directory
    folder_name : string, optional
        Name of the folder to download, by default 'kostergroup-SIMsalabim-'
    verbose : bool, optional
        Print verbose output, by default False

    Returns
    -------
    int

    0 : Success
    1 : Success
    2 : Failed
    3 : Failed

    """    
    
    if verbose:
        print("Getting the latest compiled binaries from the Kostergroup Github")
    # Get the assets from the latest release
    url = "https://api.github.com/repos/kostergroup/SIMsalabim/releases/latest"
    response = requests.get(url)
    data = json.loads(response.text)

    for asset in data["assets"]:
        download_url = asset["browser_download_url"]
        filename = asset["name"]
        response = requests.get(download_url)
        open(os.path.join(cwd,filename), "wb").write(response.content)

    for dirpath, dirnames, files in os.walk(cwd):

        for filename in files:
            if filename.startswith('simss') and os.path.exists(os.path.join(cwd, filename)):
                print(f"Found a folder named {filename}")
                # Rename folder
                shutil.move(os.path.join(cwd, filename), os.path.join(cwd, 'SIMsalabim','SimSS',filename))
            elif filename.startswith('zimt') and os.path.exists(os.path.join(cwd, filename)):
                print(f"Found a folder named {filename}")
                # Rename folder
                shutil.move(os.path.join(cwd, filename), os.path.join(cwd, 'SIMsalabim','ZimT',filename))
            else:
                pass
    return 1

def use_SIMsalabim_source(cwd, folder_name='kostergroup-SIMsalabim-'):
    """ Use the SIMsalabim source code

    Parameters
    ----------
    cwd : string
        Current working directory
    folder_name : string, optional
        Name of the folder to download, by default 'kostergroup-SIMsalabim-'

    Returns
    -------
    int

    0 : Success
    2 : Failed
    3 : Failed

    """    
    # Clear the working directory. TEMP disabled
    # result = clear_current_working_directory(cwd, folder_name)
    result = True
    if result == True:
        result_get = get_SIMsalabim_source(cwd, folder_name)
        return result_get
    elif result == False:
        print('Script terminated manually')
        return 3
    else: 
        print('Failed')
        return 2

def install_SIMsalabim(cwd, folder_name='kostergroup-SIMsalabim-',verbose=False):
    """Install SIMsalabim in the current working directory

    Parameters
    ----------
    cwd : string
        Current working directory
    folder_name : string, optional
        Name of the folder to download, by default 'kostergroup-SIMsalabim-'
    verbose : bool, optional
        Print verbose output, by default False

    Returns
    -------
    int

    0 : Success
    1 : Success
    2 : Failed
    3 : Failed

    """    

    # Check if fpc installed
    if verbose:
        print("Checking for Free Pascal Compiler (fpc) package")
    if shutil.which("fpc") is not None:
        # fpc is installed, check the version and print to stdout.
        result = subprocess.run(["fpc", "-iV"], stdout=subprocess.PIPE, text=True)
        fpc_version = result.stdout

        # remove possible newline character
        if '\n' in fpc_version:
            fpc_version = fpc_version.strip('\n')

        # fpc version must be larger than min_fpc_version
        if version.parse(fpc_version) > version.parse(min_fpc_version):
            if verbose:
                print(f'Free Pascal Compiler (fpc) is installed with version >= {min_fpc_version}\n')
            result_fpc = use_SIMsalabim_source(cwd, folder_name)
            # sys.exit(result_fpc)

            # Compile the programs
            # compile simss with fpc in os.path.join(path2prog,'SimSS')
            os.chdir(os.path.join(cwd,'SIMsalabim','SimSS'))
            os.system('fpc simss.pas')
            os.chdir(cwd)

            # compile zimt with fpc in os.path.join(path2prog,'ZimT')
            cwd = os.getcwd() # Get current working directory
            os.chdir(os.path.join(cwd,'SIMsalabim','ZimT'))
            os.system('fpc zimt.pas')
            os.chdir(cwd)

        if verbose:
            print('SIMsalabim programs have been compiled successfully!')

        else: 
            # fpc version requirement not met
            print(f'Installed Free Pascal Compiler (fpc) version is {fpc_version}, but must be at least 3.2.0\n')
            result = cmd_yes_no_question("Do you want to continue with the pre-compiled binaries (y) or abort and update the Free Pascal Compiler (n) (recommended)", 'no')
            if result is True:
                # download assets
                print("\ndownload assets")
                result_assets = get_SIMsalabim_assets(cwd, verbose)
                sys.exit(result_assets)
            elif result is False:
                # return and exit
                sys.exit(3)
    else:
        # fpc is not installed.
        print("Free Pascal Compiler is not installed.\n")
        result = cmd_yes_no_question("Do you want to continue with the pre-compiled binaries (y) or abort and install the Free Pascal Compiler (n) (recommended)", 'no')
        if result is True:
            # download assets
            print("\ndownload assets")
            result_assets = get_SIMsalabim_assets(cwd, verbose)
            sys.exit(result_assets)
        elif result is False:
            # return and exit
            sys.exit(3)

def install_fpc_Linux():
    """ Install Free Pascal Compiler on Linux
    """   
    # check if system is Linux
    if os.name != 'posix':
        print('This function is only available on Linux systems')
        sys.exit()
    
    # check if apt-get is available
    if shutil.which("apt-get") is None:
        print('apt-get is not available on this system')
        sys.exit()

    # Install Free Pascal Compiler
    password = getpass('Sudo password:')
    # run the command sudo apt-get install fp-compiler and enter the password and print the output
    os.system('echo {} | sudo -S apt-get install fp-compiler'.format(password))

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

# def fpc_prog(cwd,prog_name):
#     """_summary_

#     Parameters
#     ----------
#     cwd : string
#         Current working directory
#     prog_name : string
#         Name of the program to compile

#     """
#     # Check if fpc installed
#     if verbose:
#         print("Checking for Free Pascal Compiler (fpc) package")
#     if shutil.which("fpc") is not None:
#         # fpc is installed, check the version and print to stdout.
#         result = subprocess.run(["fpc", "-iV"], stdout=subprocess.PIPE, text=True)
#         fpc_version = result.stdout

#         # remove possible newline character
#         if '\n' in fpc_version:
#             fpc_version = fpc_version.strip('\n')

#         # fpc version must be larger than min_fpc_version
#         if version.parse(fpc_version) > version.parse(min_fpc_version):
#             if verbose:
#                 print(f'Free Pascal Compiler (fpc) is installed with version >= {min_fpc_version}\n')
#             # Compile the programs
#             os.chdir(os.path.join(cwd,prog_name))
#             os.system(f'fpc {prog_name}.pas')
#             os.chdir(cwd)
#         else:
#             # fpc version requirement not met
#             print(f'Installed Free Pascal Compiler (fpc) version is {fpc_version}, but must be at least 3.2.0\n')
#             result = cmd_yes_no_question("Do you want to continue with the pre-compiled binaries (y) or abort and update the Free Pascal Compiler (n) (recommended)", 'no')
#             if result is True:
#                 # download assets
#                 print("\ndownload assets")
#                 result_assets = get_SIMsalabim_assets(cwd, verbose)
#                 sys.exit(result_assets)
#             elif result is False:
#                 # return and exit
#                 sys.exit(3)
#     else:
#         # fpc is not installed.
#         print("Free Pascal Compiler is not installed.\n")
        
#         sys.exit(3)

def fpc_prog(cwd,prog_name,show_term_output=True,force_fpc=True,verbose=True):
    """Compile program using fpc

    Parameters
    ----------
    cwd : string
        String of the absolute path to the program
    prog_name : string
        Name of the program to compile
    show_term_output : bool, optional
        show terminal output from the compilation, by default True
    force_fpc : bool, optional  
        force recompile with fpc even if compiled program already exists, by default True
    verbose : bool, optional
        print output of the compilation, by default True
    """   

    is_windows = (os.name == 'nt')          # Check if we are on Windows
    cwd = str(cwd)                  # Convert to string

    # check if
    compiled = False
    while not compiled:
        if shutil.which("fpc") is not None:
            # fpc is installed, check the version and print to stdout.
            result = subprocess.run(["fpc", "-iV"], stdout=subprocess.PIPE, text=True)
            fpc_version = result.stdout

            # remove possible newline character
            if '\n' in fpc_version:
                fpc_version = fpc_version.strip('\n')

            # fpc version must be larger than min_fpc_version
            if version.parse(fpc_version) >= version.parse(min_fpc_version):
                if verbose:
                    print(f'Free Pascal Compiler (fpc) is installed with version >= {min_fpc_version}\n') 
                # Check if the program is already compiled
                if (os.path.isfile(os.path.join(cwd,prog_name+'.exe')) and is_windows) or (os.path.isfile(os.path.join(cwd,prog_name)) and not is_windows):
                    if force_fpc:
                        if show_term_output == True:
                            output_direct = None
                        else:
                            output_direct = subprocess.DEVNULL
                        try:
                            subprocess.check_call(['fpc', prog_name.lower()+'.pas'], encoding='utf8', stdout=output_direct, cwd=cwd, shell=is_windows)
                        except subprocess.CalledProcessError:
                            print('Error compiling '+prog_name+' in '+cwd)
                            raise ChildProcessError
                        if verbose:
                            print('\n'+prog_name+' already existed but was recompiled'+'\n')
                    else:
                        if verbose:  
                            print('\n'+prog_name+' already compiled')
                
                else: # Compile the program
                    if show_term_output == True:
                        output_direct = None
                    else:
                        output_direct = subprocess.DEVNULL
                    try:
                        subprocess.check_call(['fpc', prog_name.lower()+'.pas'], encoding='utf8', stdout=output_direct, cwd=cwd, shell=is_windows)
                        if verbose:
                            print('\n'+prog_name+' was not compiled so we did it!'+'\n')
                    except subprocess.CalledProcessError:
                        print('Error compiling '+prog_name+' in '+cwd)
                        raise ChildProcessError 
                compiled = True
            else:
                # fpc version requirement not met
                print(f'Installed Free Pascal Compiler (fpc) version is {fpc_version}, but must be at least 3.2.0\n')
                print('Please update the Free Pascal Compiler to the latest version')
                sys.exit(3)
        else:
            # fpc is not installed.
            print("Free Pascal Compiler is not installed.\n")
            result = cmd_yes_no_question("Do you want to continue and install the Free Pascal Compiler (only works on Linux) (y) or abort (n) (recommended)", 'no')
            if result is True:
                # install fpc
                install_fpc_Linux()
                # sys.exit(0)
            elif result is False:
                # return and exit
                sys.exit(3)

        


  
######### Script ##################################################################################
if __name__ == "__main__":

    install_SIMsalabim(cwd,verbose=True)
    sys.exit(0)