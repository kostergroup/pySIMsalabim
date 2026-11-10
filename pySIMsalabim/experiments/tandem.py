"""Perform steady-state JV tandem simulations"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys,os

try :
    import pySIMsalabim as sim
except ImportError:
    # Add the parent directory to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import pySIMsalabim as sim
from pySIMsalabim.utils import general as utils_gen
from pySIMsalabim.utils import device_parameters as utils_devpar
from pySIMsalabim.utils.utils import update_cmd_pars
from pySIMsalabim.plots import plot_def 

def extract_parameter_value(dev_par, section_name, parameter_name):
    """Helper function to extract a numeric parameter value from a section of the parameter object of SIMsalabim (of 1 file).
    
    Parameters:
    ----------
    dev_par : list
        The parameter object of SIMsalabim of 1 file (simuation setup or device parameter file)
    section_name : str
        The name of the section from which to extract the parameter
    parameter_name : str
        The name of the parameter to extract

    Returns:
    -------
    float or None
        The value of the extracted parameter, or None if the parameter is not found
    """
    for section in dev_par:
        if section[0] == section_name:
            for subsection in section[1:]:
                if subsection[1] == parameter_name:
                    return float(subsection[2]) # Return the value as a float, so specific for numeric parameters
    return None

def get_W_F(dev_par_sub, layers, simulationSetupSubcell, subcellIdx):
    """ Get the work function of the recombination contact for the specified subcell as if it would be Ohmic.

    Parameters:
    ----------
    dev_par_sub : dict
        The device parameters dictionary loaded from the main tandem simulation setup.
    layers : list
        A list of layers in the tandem device.
    simulationSetupSubcell : str
        The name of the simulation setup file for the subcell.
    subcellIdx : int
        The index of the subcell for which to get the work function, to determine which work function to calculate

    Returns:
    -------
    float
        The work function value for the specified subcell.
    """

    # Initialize variables for the work function and layer index based on the subcell index
    if subcellIdx == 1:
        W_F_fixed_type = 'W_L'
        W_F_lid = 1
    elif subcellIdx == 2:
        W_F_fixed_type = 'W_R'
        W_F_lid = -1
    
    # Extract the fixed work function value and the conduction and valence band energiesof of either the first or last layer of the subcell, depending on the subcell index
    W_F_fixed_val = extract_parameter_value(dev_par_sub[simulationSetupSubcell], 'Contacts', W_F_fixed_type)
    E_c_start = extract_parameter_value(dev_par_sub[layers[W_F_lid][2]], 'General', 'E_c')
    E_v_sub1 = extract_parameter_value(dev_par_sub[layers[W_F_lid][2]], 'General', 'E_v')

    # Determine whether we are dealing with an ETL or HTL, to properly align the Work function on the other side
    if abs(W_F_fixed_val - E_c_start) < abs(W_F_fixed_val - E_v_sub1):
        typeTL = 'ETL'
    else:
        typeTL = 'HTL'

    # Get the conduction and valence band energies of the layer on the other side of the subcell
    E_c_end = extract_parameter_value(dev_par_sub[layers[-W_F_lid][2]], 'General', 'E_c')
    E_v_end = extract_parameter_value(dev_par_sub[layers[-W_F_lid][2]], 'General', 'E_v')

    # Depending on the type of transport layer, return the work function value as an ohmic contact
    if typeTL == 'ETL':
        W_F = E_v_end
    else:
        W_F = E_c_end

    return W_F

def get_genProf_tandem(sim_setup_tandem, session_path, genProf = 'calc', cleanupFiles=False, JVFile='JV.dat', varFile='none', logFile='log.txt', UUID='', cmd_pars=None):
    """ Get the generation profile for the complete tandem device by running a SIMsalabim simulation with the specified parameters.

    Parameters:
    ----------
    sim_setup_tandem : string
        The path to the simulation setup file for the tandem
    session_path : string
        The path to the session directory where the simulation will be run
    genProf : string, optional
        The generation profile to be used in the simulation, by default 'calc'
    cleanupFiles : bool, optional
        Whether to clean up the generated files after reading the generation profile, by default False
    JVFile : str, optional
        The filename for the JV output file, by default 'JV.dat'.
    varFile : str, optional
        The filename for the Var output file, by default 'none'.
    logFile : str, optional
        The filename for the log output file, by default 'log.txt'.
    UUID : str, optional
        A unique identifier to append to the filenames to avoid overwriting files, by default ''.
    cmd_pars : list of dict, optional
        A list of command line parameters to be passed to the SIMsalabim simulation, by default None.
    
    Returns:
    -------
    int
        The return code from the simulation, 0 indicates success, other values indicate failure
    pandas.DataFrame or None
        A DataFrame containing the filtered generation profile data with columns 'x', 'G_ehp', and 'lid', or None if the simulation failed to produce a valid generation profile
    """

    # We need the Var file to get the generation profile, if the user did not specify a Var file, we will create a temporary one with a unique name based on the UUID if provided
    if varFile == 'none':
        varFile = f'Var_{UUID}.dat' if UUID != '' else 'Var.dat'

    # Force several parameters to ensure that the simulation runs correctly for obtaining the generation profile
    tandemArgs = [{'par':'dev_par_file','val': sim_setup_tandem},
                {'par':'maxItSS','val':'1'}, # We only need one iteration to get the generation profile
                {'par':'genProfile','val': genProf},
                {'par':'VarFile','val': varFile},
                {'par':'JVFile','val': JVFile}, 
                {'par':'logFile','val': logFile}, 
                {'par':'failureMode','val':'1'}, # We dont need convergence to get the generation profile
                {'par':'Vmin','val':'0'}, # We only need one voltage point
                {'par':'Vmax','val':'0'},
                {'par':'Vdist','val':'1'},
                {'par':'outputRatio','val':'1'}, # Fix to 1 to avoid the case where the output is not written due to outputRatio > 1
                ]

    # Add any additional command line parameters provided by the user to the SIMsalabim arguments
    if cmd_pars is not None:
        tandemArgs = update_cmd_pars(tandemArgs, cmd_pars)

    # Run SIMsalabim simulation
    result, message = utils_gen.run_simulation('simss', tandemArgs, session_path)
    returncode = result.returncode # Get the return code from the result object

    if returncode == 0 or returncode == 95 or returncode == 97:
        # Simulation succeeded, as we don't care about convergence
        dataVar = pd.read_csv(os.path.join(session_path, varFile), sep=r'\s+')
        
        if not dataVar.empty:
            # Check if the varFile is not empty, if it is empty, the simulation failed to produce a valid generation profile
            
            # Filter the dataframe to get x, G_ehp and lid columns
            data_Var_filt = dataVar[['x', 'G_ehp', 'lid']]

            # Clean up files
            if cleanupFiles == True:
                if os.path.exists(os.path.join(session_path, varFile)):
                    os.remove(os.path.join(session_path, varFile))
                if os.path.exists(os.path.join(session_path, logFile)):
                    os.remove(os.path.join(session_path, logFile))
                if os.path.exists(os.path.join(session_path, JVFile)):
                    os.remove(os.path.join(session_path, JVFile))

            # Combine successful return code into code 0
            returncode = 0
        else:
            # Despite the simulation returning a success code, the Var file is empty, indicating the simulation failed
            data_Var_filt = None
    else: data_Var_filt = None  # Ensure data_Var_filt is defined even if the simulation fails

    return returncode, data_Var_filt

def split_genProf_tandem(data_Var_filt, lid_sub1_end, lid_sub2_start):
    """ Split the generation profile data into two parts for subcell 1 and subcell 2 based on the provided layer indices.

    Parameters
    ----------
    data_Var_filt : pandas.DataFrame
        A DataFrame containing the filtered generation profile data with columns 'x', 'G_ehp', and 'lid'.
    lid_sub1_end : int
        The layer index where the first subcell ends.
    lid_sub2_start : int
        The layer index where the second subcell starts.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing x, G_ehp, and lid for subcell 1.
    pandas.DataFrame
        A DataFrame containing x, G_ehp, and lid for subcell 2.
    """

    # Split the dataframe from the first value up to data_Var_filt['lid'] == lid_sub1_end for subcell 1
    genProf1 = data_Var_filt[data_Var_filt['lid'] <= lid_sub1_end]

    # Split the dataframe from data_Var_filt['lid'] == lid_sub2_start up to the last value for subcell 2
    genProf2 = data_Var_filt[data_Var_filt['lid'] >= lid_sub2_start]

    # Shift the x values of genProf2 to start at 0
    genProf2.loc[:,'x'] = genProf2['x'] - genProf2['x'].iloc[0]

    return genProf1, genProf2

def write_genProf_subcells(genProf1, genProf2, session_path,filename_sub1='genProf_sub1.txt', filename_sub2='genProf_sub2.txt', UUID=None):
    """ Write the generation profile data for subcell 1 and subcell 2 to text files.
    
    Parameters
    ----------
    genProf1 : pandas.DataFrame
        DataFrame containing x, G_ehp, and lid for subcell 1.
    genProf2 : pandas.DataFrame
        DataFrame containing x, G_ehp, and lid for subcell 2.
    session_path : str
        The path to the session directory where the generation profile files will be saved.
    filename_sub1 : str, optional
        The filename for the generation profile of subcell 1, by default 'genProf_sub1.txt'.
    filename_sub2 : str, optional
        The filename for the generation profile of subcell 2, by default 'genProf_sub2.txt'.
    UUID : str, optional
        A unique identifier to append to the filenames, by default None.

    Returns
    -------
    str
        The filename of the generated generation profile for subcell 1.
    str
        The filename of the generated generation profile for subcell 2.
    
    """

    # Header for the generation profile as defined by SIMsalabim
    header = "x G_ehp\n"
    if UUID is not None:
        sub1_file_name_base, sub1_file_name_ext = os.path.splitext(filename_sub1)
        filename_sub1 = sub1_file_name_base + f"_{UUID}" + sub1_file_name_ext
        sub2_file_name_base, sub2_file_name_ext = os.path.splitext(filename_sub2)
        filename_sub2 = sub2_file_name_base + f"_{UUID}" + sub2_file_name_ext

    # Write x and G_ehp to a text file for the subcells
    genProf1.to_csv(os.path.join(session_path, filename_sub1), columns=['x', 'G_ehp'], sep=' ', index=False, header=header)
    genProf2.to_csv(os.path.join(session_path, filename_sub2), columns=['x', 'G_ehp'], sep=' ', index=False, header=header)

    return filename_sub1, filename_sub2 

def create_simulation_setup_subcell(session_path, sim_setup_tandem, genProf_sub1, genProf_sub2, simulationSetupSub1 = 'simulation_setup_sub1.txt', 
                                    simulationSetupSub2 = 'simulation_setup_sub2.txt', JVFile = 'JV.dat', VarFile = 'Var.dat', logFile = 'log.txt', overwrite_sim_setup_subcells = True):
    """ Create the simulation setup files for subcell 1 and subcell 2 based on the main tandem simulation setup to run them independently.
    
    Parameters
    ----------
    session_path : str
        The path to the session directory where the simulation setup files will be saved.
    sim_setup_tandem : str
        The path to the simulation setup file for the tandem.
    genProf_sub1 : str
        The filename of the generation profile for subcell 1.
    genProf_sub2 : str
        The filename of the generation profile for subcell 2.
    simulationSetupSub1 : str, optional
        The filename for the simulation setup of subcell 1, by default 'simulation_setup_sub1.txt'.
    simulationSetupSub2 : str, optional
        The filename for the simulation setup of subcell 2, by default 'simulation_setup_sub2.txt'.
    JVFile : str, optional
        The filename for the JV output file, by default 'JV.dat'.
    VarFile : str, optional
        The filename for the Var output file, by default 'Var.dat'.
    logFile : str, optional
        The filename for the log output file, by default 'log.txt'.
    overwrite_sim_setup_subcells : bool, optional
        Whether to overwrite existing simulation setup files for the subcells, by default True.

    Returns
    -------
    tuple
        A tuple containing the paths to the simulation setup files for subcell 1 and its respective JV, Var, and log filenames
    tuple
        A tuple containing the paths to the simulation setup files for subcell 2 and its respective JV, Var, and log filenames.
    
    """
    def update_simulation_setup(dev_par, sim_setup_tandem, genProf, layer_slice, contacts_key, var_file, jv_file, log_file):
        """ Update the simulation setup parameters for a subcell based on the provided generation profile and layer slice.
        
        Parameters
        ----------
        dev_par : dict
            The device parameters dictionary loaded from the main tandem simulation setup.
        sim_setup_tandem : str
            The path to the simulation setup file for the tandem.
        genProf : str
            The filename of the generation profile for the subcell.
        layer_slice : list
            A list of layers to be included in the subcell simulation setup.
        contacts_key : str
            The key for the contact type to be used in the subcell simulation setup.
        var_file : str
            The filename for the Var output file for the subcell.
        jv_file : str
            The filename for the JV output file for the subcell.
        log_file : str
            The filename for the log output file for the subcell.

        Returns
        -------
        dict
            The updated device parameters dictionary for the subcell simulation setup.
        """
        # Set the layer slice for the subcell in the device parameters
        dev_par[sim_setup_tandem][2] = layer_slice

        # Update parameters in contacts, optics, and user interface
        for section in dev_par[sim_setup_tandem]:
            if section[0] == 'Contacts':
                for subsection in section[1:]:
                    if subsection[1] == contacts_key:
                        subsection[2] = 'sfb'
            elif section[0] == 'Optics':
                for subsection in section[1:]:
                    if subsection[1] == 'G_frac':
                        subsection[2] = '1'
                    elif subsection[1] == 'genProfile':
                        subsection[2] = genProf
            elif section[0] == 'User interface':
                for subsection in section[1:]:
                    if subsection[1] == 'varFile':
                        subsection[2] = var_file
                    elif subsection[1] == 'JVFile':
                        subsection[2] = jv_file
                    elif subsection[1] == 'logFile':
                        subsection[2] = log_file
        return dev_par

    # Add _sub1, _sub2 to the filenames for the output files to distinguish between subcell 1 and subcell 2
    JVFile_sub1 = '%s_sub1%s' % os.path.splitext(JVFile)
    VarFile_sub1 = '%s_sub1%s' % os.path.splitext(VarFile)
    logFile_sub1 = '%s_sub1%s' % os.path.splitext(logFile)

    # Add _sub2 to the filenames for the output files to distinguish between subcell 1 and subcell 2
    JVFile_sub2 = '%s_sub2%s' % os.path.splitext(JVFile)
    VarFile_sub2 = '%s_sub2%s' % os.path.splitext(VarFile)
    logFile_sub2 = '%s_sub2%s' % os.path.splitext(logFile)

    # Check if the simulation setup file for the subcells already exists, if so, remove it to avoid conflicts
    if os.path.exists(os.path.join(session_path, simulationSetupSub1)):
        # Only create the new simulation setup for subcell 1 if the file either does not exist or if the user wants to overwrite it
        if overwrite_sim_setup_subcells:
            # Create simulation setup for subcell 1
            dev_par_sub1, _ = utils_devpar.load_device_parameters(session_path, sim_setup_tandem)

            # Filter only the layers for subcell 1 based on lid_sub1_end
            layers_sub1 = dev_par_sub1[sim_setup_tandem][2][:lid_sub1_end + 1]

            # Update the simulation setup with several fixed parameters
            dev_par_sub1 = update_simulation_setup(dev_par_sub1, sim_setup_tandem, genProf_sub1, layers_sub1, 'W_R', VarFile_sub1, JVFile_sub1, logFile_sub1)

            par_file = utils_gen.devpar_write_to_txt(dev_par_sub1[sim_setup_tandem])
            with open(os.path.join(session_path, simulationSetupSub1), "w") as f:
                f.write(par_file)

    if os.path.exists(os.path.join(session_path, simulationSetupSub2)):
        # Only create the new simulation setup for subcell 2 if the file either does not exist or if the user wants to overwrite it
        if overwrite_sim_setup_subcells:
            # Create simulation setup for subcell 2
            dev_par_sub2, _ = utils_devpar.load_device_parameters(session_path, sim_setup_tandem)

            # Filter only the layers for subcell 2 based on lid_sub2_start, we need to include the header 'Layers' seperately as required by the object structure
            layers_sub2 = dev_par_sub2[sim_setup_tandem][2][lid_sub2_start:]
            layers_sub2 = ['Layers'] + layers_sub2

            # Shift layer indices for subcell 2 to start from l1 again
            for i, layer in enumerate(layers_sub2[1:], start=1):
                layer[1] = f'l{i}'
            dev_par_sub2[sim_setup_tandem][2] = layers_sub2

            # Update the simulation setup with several fixed parameters
            dev_par_sub2 = update_simulation_setup(dev_par_sub2, sim_setup_tandem, genProf_sub2,layers_sub2, 'W_L', VarFile_sub2, JVFile_sub2, logFile_sub2)
            par_file_2 = utils_gen.devpar_write_to_txt(dev_par_sub2[sim_setup_tandem])
            with open(os.path.join(session_path, simulationSetupSub2), "w") as f:
                f.write(par_file_2)

    return (simulationSetupSub1, JVFile_sub1, VarFile_sub1, logFile_sub1), (simulationSetupSub2, JVFile_sub2, VarFile_sub2, logFile_sub2)

def split_cmd_pars_subcells(cmd_pars, lid_sub2_start):
    """ Split the command line parameters for the tandem simulation into two separate lists for subcell 1 and subcell 2.
    
    Parameters
    ----------
    cmd_pars : list of dict
        The command line parameters for the tandem simulation.
    lid_sub2_start : int
        The layer index where subcell 2 starts.

    Returns
    -------
    list of dict
        The command line parameters for subcell 1.
    list of dict
        The command line parameters for subcell 2.
    """

    cmd_pars_sub1 = []
    cmd_pars_sub2 = []

    for cmd_par in cmd_pars:
        # Split the value associated with the key 'par' on the '.' and check if it starts with 'l'
        if not cmd_par['par'].split('.')[0].startswith('l'):
            cmd_pars_sub1.append(cmd_par) # General parameters that are not layer specific are added to both subcells
            cmd_pars_sub2.append(cmd_par) # General parameters that are not layer specific are added to both subcells
        else:
            lyr_idx = int(cmd_par['par'].split('.')[0][1:]) # Get the layer index from the 'par' value
        # Shift the layer index such that the first index of subcell 2 is 1
            if lyr_idx >= lid_sub2_start:
                new_lyr_idx = lyr_idx - lid_sub2_start + 1
                cmd_par['par'] = f'l{new_lyr_idx}.' + '.'.join(cmd_par['par'].split('.')[1:]) # Update the 'par' value with the new layer index
                cmd_pars_sub2.append(cmd_par) # Add the updated parameter to the subcell 2 command line parameters
            else:
                cmd_pars_sub1.append(cmd_par) # Add the parameter to the subcell 1 command line parameters

    return cmd_pars_sub1, cmd_pars_sub2

def run_subcells(session_path, output_subcell1, output_subcell2, cmd_pars_sub1=None, cmd_pars_sub2=None, UUID=None):
    """ Run the SIMsalabim simulations for subcell 1 and subcell 2 using the provided device parameter files.
    
    Parameters
    ----------
    session_path : str
        The path to the session directory where the simulations will be run.
    output_subcell1 : tuple
        tuple with the paths to the input/output files for subcell 1 (simulation_setup, JVFile, VarFile, logFile).
    output_subcell2 : tuple
        tuple with the paths to the input/output files for subcell 2 (simulation_setup, JVFile, VarFile, logFile).
    cmd_pars_sub1 : list of dict, optional
        The command line parameters for subcell 1, by default None.
    cmd_pars_sub2 : list of dict, optional
        The command line parameters for subcell 2, by default None.
    UUID : str, optional
        A unique identifier to append to the filenames by default None.

    Returns
    -------
    tuple
        A tuple containing the return code, JV output file path, Var output file path, and log output file path for subcell 1.
    tuple
        A tuple containing the return code, JV output file path, Var output file path, and log output file path for subcell 2.
    """

    # Extract the output file paths for each subcell
    simulation_setup_sub1, JVFile_sub1, VarFile_sub1, logFile_sub1 = output_subcell1
    simulation_setup_sub2, JVFile_sub2, VarFile_sub2, logFile_sub2 = output_subcell2

    # Add the UUID to the output file names if provided, to avoid overwriting files
    if UUID is not None:
        JVFile_sub1 = f"{os.path.splitext(JVFile_sub1)[0]}_{UUID}{os.path.splitext(JVFile_sub1)[1]}"
        logFile_sub1 = f"{os.path.splitext(logFile_sub1)[0]}_{UUID}{os.path.splitext(logFile_sub1)[1]}"
        if VarFile_sub1 != 'none':
            VarFile_sub1 = f"{os.path.splitext(VarFile_sub1)[0]}_{UUID}{os.path.splitext(VarFile_sub1)[1]}"

        JVFile_sub2 = f"{os.path.splitext(JVFile_sub2)[0]}_{UUID}{os.path.splitext(JVFile_sub2)[1]}"
        logFile_sub2 = f"{os.path.splitext(logFile_sub2)[0]}_{UUID}{os.path.splitext(logFile_sub2)[1]}"
        if VarFile_sub2 != 'none':
            VarFile_sub2 = f"{os.path.splitext(VarFile_sub2)[0]}_{UUID}{os.path.splitext(VarFile_sub2)[1]}"




    # Run SimSS for subcell 1
    cmd_pars = [{'par':'dev_par_file','val':simulation_setup_sub1},
                {'par':'JVFile','val':JVFile_sub1},
                {'par':'VarFile','val':VarFile_sub1},
                {'par':'logFile','val':logFile_sub1}]

    # Add any additional command line parameters provided by the user to the SIMsalabim arguments
    if cmd_pars_sub1 is not None:
        cmd_pars = update_cmd_pars(cmd_pars, cmd_pars_sub1)

    result_sub1, message_sub1 = utils_gen.run_simulation('simss', cmd_pars, session_path)
    returncode_sub1 = result_sub1.returncode

    # Run SimSS for subcell 2
    cmd_pars = [{'par':'dev_par_file','val':simulation_setup_sub2},
                {'par':'JVFile','val':JVFile_sub2},
                {'par':'VarFile','val':VarFile_sub2},
                {'par':'logFile','val':logFile_sub2}]

    # Add any additional command line parameters provided by the user to the SIMsalabim arguments
    if cmd_pars_sub2 is not None:
        cmd_pars = update_cmd_pars(cmd_pars, cmd_pars_sub2)

    result_sub2, message_sub2 = utils_gen.run_simulation('simss', cmd_pars, session_path)
    returncode_sub2 = result_sub2.returncode

    return (returncode_sub1, JVFile_sub1, VarFile_sub1, logFile_sub1), (returncode_sub2, JVFile_sub2, VarFile_sub2, logFile_sub2)

def get_JV_subcells(session_path, JVFile_sub1, JVFile_sub2):
    """ Get the JV data for subcell 1 and subcell 2 from their respective output files and place into arrays.

    Parameters
    ----------
    session_path : str
        The path to the session directory where the JV output files are located.
    JVFile_sub1 : str
        The filename of the JV output file for subcell 1.
    JVFile_sub2 : str
        The filename of the JV output file for subcell 2.

    Returns
    -------
    numpy.ndarray
        The Vext values for subcell 1.
    numpy.ndarray
        The Jext values for subcell 1.
    numpy.ndarray
        The Vext values for subcell 2.
    numpy.ndarray
        The Jext values for subcell 2.
    """

    if os.path.exists(os.path.join(session_path, JVFile_sub1)) and os.path.exists(os.path.join(session_path, JVFile_sub2)):
        data_JV_sub1 = pd.read_csv(os.path.join(session_path, JVFile_sub1), sep=r'\s+')
        data_JV_sub2 = pd.read_csv(os.path.join(session_path, JVFile_sub2), sep=r'\s+')
    else:
        # Error: The JV file(s) of one or both subcells does not exist
        return None, None, None, None

    # Extract Vext and Jext values for both subcells into numpy arrays
    Vext_sub1 = data_JV_sub1['Vext'].to_numpy()
    Jext_sub1 = data_JV_sub1['Jext'].to_numpy()
    Vext_sub2 = data_JV_sub2['Vext'].to_numpy()
    Jext_sub2 = data_JV_sub2['Jext'].to_numpy()

    return Vext_sub1, Jext_sub1, Vext_sub2, Jext_sub2

def get_range_J(Jext_sub1, Jext_sub2):

    """
    Get the lower and upper limits of J for interpolation.

    Parameters
    ----------
    Jext_sub1 : numpy.ndarray
        The Jext values for subcell 1.
    Jext_sub2 : numpy.ndarray
        The Jext values for subcell 2.

    Returns
    -------
    float
        The lower limit of J for interpolation.
    float
        The upper limit of J for interpolation.
    """

    Jlower = max(Jext_sub1.min(), Jext_sub2.min())
    Jupper = min(Jext_sub1.max(), Jext_sub2.max())

    return Jlower, Jupper

def interpolate_JV(Jext_sub1, Vext_sub1, Jext_sub2, Vext_sub2, Jlower, Jupper, num_points=10000):
    """ Interpolate Vext for both subcells based on a common J range.

    Parameters
    ----------
    Jext_sub1 : numpy.ndarray
        The Jext values for subcell 1.
    Vext_sub1 : numpy.ndarray
        The Vext values for subcell 1.
    Jext_sub2 : numpy.ndarray
        The Jext values for subcell 2.
    Vext_sub2 : numpy.ndarray
        The Vext values for subcell 2.
    Jlower : float
        The lower limit of J for interpolation.
    Jupper : float
        The upper limit of J for interpolation.
    num_points : int, optional
        The number of points to use for interpolation, by default 10000.

    Returns
    -------
    numpy.ndarray
        The interpolated J values.
    numpy.ndarray
        The interpolated Vext values for subcell 1.
    numpy.ndarray
        The interpolated Vext values for subcell 2.
    """

    # Create a linear spaced J range for interpolation
    Jinterp = np.linspace(Jlower, Jupper, num_points)

    # Interpolate Vext for both subcells based on the common J range
    Vext_sub1_interp = np.interp(Jinterp, Jext_sub1, Vext_sub1)
    Vext_sub2_interp = np.interp(Jinterp, Jext_sub2, Vext_sub2)

    return Jinterp, Vext_sub1_interp, Vext_sub2_interp

def get_Vrec(Jinterp, rec_contact_type, Rrec=0, Vp=0.2, Jp=50, plotDiode=False):
    """ Calculate Vrec based on the specified recombination contact type. 
    1) Resistance, 2) Analytical model for a tunnel diode based on Eq. 8.1 in Sze, Physics of Semiconductor Devices.
    
    Parameters
    ----------
    Jinterp : numpy.ndarray
        The interpolated J values.
    rec_contact_type : int
        The type of recombination contact, 1 for Resistance, 2 for Analytical.
    Rrec : float, optional
        The resistance value for the recombination contact, used only if rec_contact_type is 1, by default 0.
    Vp : float, optional
        The peak voltage for the analytical model, used only if rec_contact_type is 2, by default 0.2.
    Jp : float, optional
        The peak current density for the analytical model, used only if rec_contact_type is 2, by default 50.
    plotDiode : bool, optional
        Whether to plot the diode characteristics for the analytical model, used only if rec_contact_type is 2, by default False.

    Returns
    -------
    numpy.ndarray or None
        The calculated Vrec values based on the specified recombination contact type, or None if an invalid type is specified.
    str
        An error message if an invalid recombination contact type is specified, otherwise an empty string.
    """

    message = ''
    if rec_contact_type == 1:
        # Calculate Vrec using Ohm's law: V = I * R
        Vrec = Jinterp * Rrec
    elif rec_contact_type == 2:
        # Calculate Vrec using the analytical model for a tunnel diode based on Eq. 8.1 in Sze, Physics of Semiconductor Devices, 3rd Edition, 2006
        Vupper = Vp
        Vlower = -2*Vp        
        # Vlower = -Vp * np.log(min(Jinterp)*Vp) # Solve for V where J_min = 1/Vp*exp(-V/Vp)

        Vval = np.linspace(Vlower, Vupper, 10000) # Generate 100 points between Vlower and Vupper
        Jval = Jp*(Vval/Vp) * np.exp(1-Vval/Vp) # Calculate J using the reduced formula

        # Plot the diode model JV characteristics
        if plotDiode == True:
            plt.figure()
            plt.plot(Vval, Jval)
            plt.xlabel('V')
            plt.ylabel('J')
            plt.ylim(min(Jinterp), max(Jinterp))
            plt.title('Recombination Contact')

        Vrec = np.interp(Jinterp, Jval, Vval) # Interpolate the calculated J values to the Jinterp and get the corresponding Vrec
        
        # Force the non-relevant J values beyond Jp to have Vrec = max(Vval), as these will not be used anyway
        for i in range(len(Jinterp)):
            if Jinterp[i] > max(Jval):
                Vrec[i] = max(Vval)
    else:
        # Invalid recombination contact type specified, return None and an error message
        Vrec = None
        message = "Error: Invalid recombination contact type. Must be 1 (Resistance) or 2 (Analytical)."

    return Vrec, message, Jp

def maskJV(Vext_sub1, Vext_sub2, Jext_sub1, Jext_sub2, threshold=1000):
    """ Mask the JV data for subcell 1 and subcell 2 where Jext is greater than the specified threshold.
    This prevents later issues with interpolation issues as simulated current range can be up to 1E8 Am^-2, which skews the interpolation and tandem curve.

    Parameters
    ----------
    Vext_sub1 : numpy.ndarray
        The Vext values for subcell 1.
    Vext_sub2 : numpy.ndarray
        The Vext values for subcell 2.
    Jext_sub1 : numpy.ndarray
        The J values for subcell 1.
    Jext_sub2 : numpy.ndarray
        The J values for subcell 2.
    threshold : int, optional
        The threshold value for masking the JV data, by default 1000.

    Returns
    -------
    Vext_sub1 : numpy.ndarray
        The masked Vext values for subcell 1.
    Vext_sub2 : numpy.ndarray
        The masked Vext values for subcell 2.
    Jext_sub1 : numpy.ndarray
        The masked J values for subcell 1.
    Jext_sub2 : numpy.ndarray
        The masked J values for subcell 2.
    """
    

    # Limit the values of sub1 where Jext_sub1 is < threshold
    mask = Jext_sub1 <= threshold
    Vext_sub1 = Vext_sub1[mask]
    Jext_sub1 = Jext_sub1[mask]

    # limit the values of sub2 where Jext_sub2 is < threshold
    mask = Jext_sub2 <= threshold
    Vext_sub2 = Vext_sub2[mask]
    Jext_sub2 = Jext_sub2[mask]

    return Vext_sub1, Vext_sub2, Jext_sub1, Jext_sub2

def get_JV_subcell_ideal(simulationSetupSubcell1, simulationSetupSubcell2, session_path, cmd_pars_sub1=None, cmd_pars_sub2=None, UUID=None, cleanupFiles=True):
    """ Get the JV data for the ideal tandem device by running SIMsalabim simulations for subcell 1 and subcell 2 
    with ohmic contacts/work functions where the recombination contact would be. 
    This represents an ideal device without voltage losses due to the contact or doping of the recombination layer.

    Parameters
    ----------
    simulationSetupSubcell1 : str
        The path to the simulation setup file for subcell 1.
    simulationSetupSubcell2 : str
        The path to the simulation setup file for subcell 2.
    session_path : str
        The path to the session directory where the simulations will be run.
    cmd_pars_sub1 : list, optional
        A list of command line parameters to be passed to the SIMsalabim simulation for subcell 1, by default None.
    cmd_pars_sub2 : list, optional
        A list of command line parameters to be passed to the SIMsalabim simulation for subcell 2, by default None.
    UUID : str, optional
        A unique identifier to append to the filenames, by default None.
    cleanupFiles : bool, optional
        Whether to clean up the generated files after the simulation, by default True.

    Returns
    -------
    numpy.ndarray
        The calculated Vtandem values for the ideal tandem device.
    numpy.ndarray
        The interpolated J values for the ideal tandem device.
    
    """

    # Load device parameters and layers for subcell 1 and subcell 2 and get the work functions at the inner contacts.
    dev_par_sub1, layers = utils_devpar.load_device_parameters(session_path, simulationSetupSubcell1)
    W_R_sub1 = get_W_F(dev_par_sub1, layers, simulationSetupSubcell1, subcellIdx=1)

    dev_par_sub2, layers = utils_devpar.load_device_parameters(session_path, simulationSetupSubcell2)
    W_L_sub2 = get_W_F(dev_par_sub2,layers, simulationSetupSubcell2, subcellIdx=2)

    # Define the JV output filenames for subcell 1 and subcell 2, appending the UUID if provided
    if UUID is not None:
        dum_str = f'_{str(UUID)}'
    else:
        dum_str = ''

    JVFile_sub1 = f'JV_sub1_ideal{dum_str}.dat'
    JVFile_sub2 = f'JV_sub2_ideal{dum_str}.dat'
    logFile = f'log{dum_str}.txt'
    VarFile = f'Var{dum_str}.dat'

    # Run SimSS for subcell 1
    cmd_pars = [{'par':'dev_par_file','val':simulationSetupSubcell1},
                     {'par':'W_R','val':str(W_R_sub1)},
                     {'par':'JVFile','val':JVFile_sub1},
                     {'par':'logFile','val':logFile},
                     {'par':'VarFile','val':VarFile}]

    # Add any additional command line parameters provided by the user to the SIMsalabim arguments
    if cmd_pars_sub1 is not None:
        cmd_pars = update_cmd_pars(cmd_pars, cmd_pars_sub1)

    result_sub1, message_sub1 = utils_gen.run_simulation('simss', cmd_pars, session_path)
    returncode_sub1 = result_sub1.returncode

    # Run SimSS for subcell 2
    cmd_pars = [{'par':'dev_par_file','val':simulationSetupSubcell2},
                     {'par':'W_L','val':str(W_L_sub2)},
                     {'par':'JVFile','val':JVFile_sub2},
                     {'par':'logFile','val':logFile},
                     {'par':'VarFile','val':VarFile}
                     ]

    # Add any additional command line parameters provided by the user to the SIMsalabim arguments
    if cmd_pars_sub2 is not None:
        cmd_pars = update_cmd_pars(cmd_pars, cmd_pars_sub2)
    
    result_sub2, message_sub2 = utils_gen.run_simulation('simss', cmd_pars, session_path)
    returncode_sub2 = result_sub2.returncode

    if returncode_sub1 not in [0, 95] or returncode_sub2 not in [0, 95]:
        print(f"Error: One of the subcell simulations for the ideal tandem case failed with return codes: {returncode_sub1}, {returncode_sub2}. Skipping ideal tandem calculation.")
        return None, None

    # Get the JV data for subcell 1 and subcell 2
    Vext_sub1, Jext_sub1, Vext_sub2, Jext_sub2 = get_JV_subcells(session_path, JVFile_sub1, JVFile_sub2)

    # Mask the JV data for subcell 1 and subcell 2 where Jext is greater than the specified threshold to prevent interpolation issues
    Vext_sub1, Vext_sub2, Jext_sub1, Jext_sub2 = maskJV(Vext_sub1, Vext_sub2, Jext_sub1, Jext_sub2)

    # Get the lower and upper limits of J for interpolation
    Jlower, Jupper = get_range_J(Jext_sub1, Jext_sub2)

    # Interpolate Vext for both subcells based on a common J range
    Jinterp, Vext_sub1_interp, Vext_sub2_interp = interpolate_JV(Jext_sub1, Vext_sub1, Jext_sub2, Vext_sub2, Jlower, Jupper)

    # Calculate Vtandem for the ideal tandem device by summing the interpolated Vext values for subcell 1 and subcell 2
    Vtandem = Vext_sub1_interp + Vext_sub2_interp

    # Write the JV data for the ideal tandem device to a text file
    write_JV(session_path, Jinterp, Vtandem, filename=f'JV_tandem_ideal{dum_str}.dat')

    # Cleanup files
    if cleanupFiles:
        files_to_remove = [JVFile_sub1, JVFile_sub2, logFile, VarFile]
        for file in files_to_remove:
            file_path = os.path.join(session_path, file)
            if os.path.exists(file_path):
                os.remove(file_path) 

    return Vtandem, Jinterp

def write_JV(session_path, Jinterp, Vtandem, filename='JV_tandem.dat'):
    """ Write the JV data for the tandem device to a text file.

    Parameters
    ----------
    session_path : str
        The path to the session directory where the JV output file will be saved.
    Jinterp : numpy.ndarray
        The interpolated J values.
    Vtandem : numpy.ndarray
        The calculated Vtandem values.
    filename : str, optional
        The filename for the JV output file, by default 'JV_tandem.dat'.
    """

    # Create a DataFrame with J and Vtandem values
    df_JV = pd.DataFrame({'J': Jinterp, 'Vtandem': Vtandem})

    # Write the DataFrame to a text file with space as separator and no index
    df_JV.to_csv(os.path.join(session_path, filename), sep=' ', index=False, float_format='%.6e')

def plot_JV_tandem(Vext_sub1, Jext_sub1, Vext_sub2, Jext_sub2, Vtandem, Jinterp, xlim=None, ylim=None, plotPerfectContact=False, Vtandem_perfcontact=None):
    """ Plot the JV curves for subcell 1, subcell 2, and the tandem device.

    Parameters
    ----------
    Vext_sub1 : numpy.ndarray
        The Vext values for subcell 1.
    Jext_sub1 : numpy.ndarray
        The J values for subcell 1.
    Vext_sub2 : numpy.ndarray
        The Vext values for subcell 2.
    Jext_sub2 : numpy.ndarray
        The J values for subcell 2.
    Vtandem : numpy.ndarray
        The calculated Vtandem values.
    Jinterp : numpy.ndarray
        The interpolated J values.
    xlim : tuple, optional
        The x-axis limits for the plot, by default None.
    ylim : tuple, optional
        The y-axis limits for the plot, by default None.
    plotPerfectContact : bool, optional
        Whether to plot the tandem device with perfect contact (R=0), by default False.
    Vtandem_perfcontact : numpy.ndarray, optional
        The calculated Vtandem values for the ideal tandem device with perfect contact (R=0), by default None.
    """

    plt.plot(Vext_sub1, Jext_sub1, label='Subcell 1', color='blue')
    plt.plot(Vext_sub2, Jext_sub2, label='Subcell 2', color='red')
    plt.plot(Vtandem, Jinterp, label='Tandem', color='green')
    if plotPerfectContact:
        plt.plot(Vtandem_perfcontact, Jinterp, label='Tandem (Perfect Contact)', color='orange', linestyle='--')
    plt.xlabel('Voltage [V]')
    plt.ylabel(r'Current Density [A/m$^2$]')
    plt.legend()
    if xlim is not None:
        plt.xlim(xlim)
    if ylim is not None:
        plt.ylim(ylim)
    plt.tight_layout()

def plot_JV_single(Vext, Jext, xlim=None, ylim=None, label='Single Subcell'):
    """ Plot the JV curve for a single subcell.

    Parameters
    ----------
    Vext : numpy.ndarray
        The Vext values.
    Jext : numpy.ndarray
        The J values.
    xlim : tuple, optional
        The x-axis limits for the plot, by default None.
    ylim : tuple, optional
        The y-axis limits for the plot, by default None.
    label : str, optional
        The label for the plot, by default 'Single Subcell'.
    """
    # plt.figure(figsize=(10, 6))
    plt.plot(Vext, Jext, label=label, color='black')
    plt.xlabel('Voltage [V]')
    plt.ylabel(r'Current Density [A/m$^2$]')
    plt.legend()
    if xlim is not None:
        plt.xlim(xlim)
    if ylim is not None:
        plt.ylim(ylim)
    plt.tight_layout()

def run_tandem_simu( sim_setup_tandem, session_path, lid_sub1_end, lid_sub2_start, rec_contact_type, Rrec=0, Vp=0.2, Jp=50, plot_JV=True, 
                    calc_ideal_tandem=False, JV_name = 'JV.dat', varFile='none', log_name='log.txt', cleanup_files=False, **kwargs):
    """ Run a steady state JV simulation for a tandem solar cell. The simulation setup of the full tandem must be provided, 
    along with the layer indices where subcell 1 ends and subcell 2 starts. The function will split the tandem device into two subcells, 
    run the simulations for each subcell, and then combine the results to obtain the JV curve for the tandem device.
    The recombination contact can be modeled either as a resistance, ideal (R=0),
    or using an analytical model for a tunnel diode based on Eq. 8.1 in Sze, Physics of Semiconductor Devices, 3rd Edition, 2006.
    Optionally, it can also calculate the ideal tandem device with perfect ohmic contacts at the recombination layer as a reference.
    
    Parameters
    ----------
    sim_setup_tandem : dict
        The simulation setup for the tandem device.
    session_path : str
        The path to the session directory.
    lid_sub1_end : int
        The layer index where subcell 1 ends.
    lid_sub2_start : int
        The layer index where subcell 2 starts.
    rec_contact_type : int
        The type of recombination contact (1 for resistance, 2 for analytical).
    Rrec : float, optional
        The recombination resistance, by default 0.
    Vp : float, optional
        The photovoltaic voltage, by default 0.2.
    Jp : float, optional
        The photovoltaic current density, by default 50.
    plot_JV : bool, optional
        Whether to plot the JV curves, by default True.
    calc_ideal_tandem : bool, optional
        Whether to calculate the ideal tandem device, by default False.
    JV_name : str, optional
        The filename for the JV output file, by default 'JV.dat'.
    varFile : str, optional
        The filename for the Var output file, by default 'none'.
    log_name : str, optional
        The filename for the log output file, by default 'log.txt'.
    cleanup_files : bool, optional
        Whether to clean up the generated files after the simulation, by default False.

    Returns
    -------
    int
        The return code of the simulation.
    """

    UUID = kwargs.get('UUID', '') # Check if the user wants to add a UUID to the tj file name
    cmd_pars = kwargs.get('cmd_pars', None) # Check if the user wants to add additional command line parameters

    # Prepare the string for the UUID
    if UUID != '':
        dum_str = f'_{UUID}'
    else:
        dum_str = ''

    # Update the filenames with the UUID
    if UUID != '':
        JV_file_name_base, JV_file_name_ext = os.path.splitext(JV_name)
        JV_name = JV_file_name_base + dum_str + JV_file_name_ext 
        log_file_base, log_file_ext = os.path.splitext(log_name)
        log_name = log_file_base + dum_str + log_file_ext
        if varFile != 'none':
            var_file_base, var_file_ext = os.path.splitext(varFile)
            varFile = var_file_base + dum_str + var_file_ext

    # Check the validity of the layer indices, as subcell 1 end index must be less than subcell 2 start index
    if lid_sub1_end >= lid_sub2_start:
        print("Error: Invalid layer indices. Subcell 1 end index must be less than subcell 2 start index.")
        return 1

    # Get the generation profile for the complete tandem device
    returncode, data_Var_filt = get_genProf_tandem(sim_setup_tandem, session_path, genProf = 'none', JVFile=JV_name, varFile=varFile, logFile=log_name, UUID=UUID, cmd_pars=cmd_pars)

    # If calculation of generation profile failed, return error code and exit
    if returncode != 0:
        print("Error: Failed to get generation profile. Return code:", returncode) # Set error message
        sys.exit(1)

    # Validate that lid_sub1_end and lid_sub2_start are actually present in the 'lid' column of the generation profile data
    if data_Var_filt is not None:
        if lid_sub1_end not in data_Var_filt['lid'].values:
            print(f"Error: lid_sub1_end ({lid_sub1_end}) is not a valid value for the defined tandem.")
            sys.exit(1)
        if lid_sub2_start not in data_Var_filt['lid'].values:
            print(f"Error: lid_sub2_start ({lid_sub2_start}) is not a valid value for the defined tandem.")
            sys.exit(1)
    
    # Split the generation profile into two parts for subcell 1 and subcell 2
    genProf1, genProf2 = split_genProf_tandem(data_Var_filt, lid_sub1_end, lid_sub2_start)

    # Save the individual generation profiles for subcell 1 and subcell 2 to text files
    genProf_sub1_filename, genProf_sub2_filename = write_genProf_subcells(genProf1, genProf2, session_path, UUID=UUID)

    # Create the simulation setup files for subcell 1 and subcell 2 based on the main tandem simulation setup to run them independently
    output_subcell1, output_subcell2 = create_simulation_setup_subcell(session_path, sim_setup_tandem, genProf_sub1_filename, genProf_sub2_filename)

    # If cmd_pars are provided, split them into two separate lists for subcell 1 and subcell 2 based on the layer indices.
    # As cmd_pars are provided for the entire tandem, to run the two subcells, the layer indices need to be adjusted for subcell 2 to start from l1 again.
    if cmd_pars is not None:
        cmd_pars_sub1, cmd_pars_sub2 = split_cmd_pars_subcells(cmd_pars, lid_sub2_start)

    # Simulate both subcells individually with perfect ohmic contact to get the maximum possible tandem voltage
    if calc_ideal_tandem:
        Vtandem_ideal, Jinterp_ideal = get_JV_subcell_ideal(output_subcell1[0], output_subcell2[0], session_path, cmd_pars_sub1=cmd_pars_sub1, cmd_pars_sub2=cmd_pars_sub2, UUID=UUID)
    
    # Run subcell 1 and subcell 2 simulations using the generated simulation setup files
    result_sub1, result_sub2 = run_subcells(session_path, output_subcell1 = output_subcell1, output_subcell2 = output_subcell2, cmd_pars_sub1=cmd_pars_sub1, cmd_pars_sub2=cmd_pars_sub2, UUID=UUID)

    if result_sub1[0] not in [0, 95]:
        print(f"Error: Subcell 1 simulation failed with return code: {result_sub1[0]}")
        sys.exit(1)
    elif result_sub2[0] not in [0, 95]:
        print(f"Error: Subcell 2 simulation failed with return code: {result_sub2[0]}")
        sys.exit(1)

    # Get the JV data for subcell 1 and subcell 2 from their respective output files and palce into array
    Vext_sub1, Jext_sub1, Vext_sub2, Jext_sub2 = get_JV_subcells(session_path, result_sub1[1], result_sub2[1])

    if Vext_sub1 is None or Jext_sub1 is None or Vext_sub2 is None or Jext_sub2 is None:
        print("Error: The JV file(s) of one or both subcells does not exist")
        sys.exit(1)

    # Mask the JV data for subcell 1 and subcell 2 where Jext is greater than the specified threshold to prevent interpolation issues
    Vext_sub1, Vext_sub2, Jext_sub1, Jext_sub2 = maskJV(Vext_sub1, Vext_sub2, Jext_sub1, Jext_sub2)

    # Get the lower and upper limits of J for interpolation
    Jlower, Jupper = get_range_J(Jext_sub1, Jext_sub2)

    # Interpolate Vext for both subcells based on a common J range
    Jinterp, Vext_sub1_interp, Vext_sub2_interp = interpolate_JV(Jext_sub1, Vext_sub1, Jext_sub2, Vext_sub2, Jlower, Jupper)

    # Calculate Vrec based on the specified recombination contact type
    Vrec, message, Jp = get_Vrec(Jinterp, rec_contact_type, Rrec, Vp, Jp) # 1) V=IR 2) Analytisch

    # Invalid recombination contact type specified
    if Vrec is None:
        print(message)
        sys.exit(1)

    # Calculate the total voltage for the tandem device by summing the voltages of subcell 1, subcell 2, and the recombination contact
    Vtandem = Vext_sub1_interp + Vext_sub2_interp + Vrec
    Vtandem_perfcontact = Vext_sub1_interp + Vext_sub2_interp # Tandem with perfect contact (Vrec = 0)

    if rec_contact_type == 2:
        # Find the index where Jinterp is smaller or equal to Jp, and limit the Vtandem and Jinterp arrays to this index, as this is the relevant range
        idx_limit = np.where(Jinterp <= Jp)[0][-1]  # Get the last index where Jinterp is smaller or equal to Jp
        Vtandem = Vtandem[:idx_limit + 1]
        Vtandem_perfcontact = Vtandem_perfcontact[:idx_limit + 1]
        Jinterp = Jinterp[:idx_limit + 1]

    # Write JV to file
    write_JV(session_path, Jinterp, Vtandem)

    if plot_JV:
        # Plot the JV curves for subcell 1, subcell 2, and the tandem device
        plt.figure(figsize=(10, 6))
        xlim = [-0.1, max(Vtandem) + 0.1]
        xlim = [-0.1, 2.75]

        ylim = [-300, Jp]
        if calc_ideal_tandem:
            if not Vtandem_ideal is None and not Jinterp_ideal is None:
                plot_JV_single(Vtandem_ideal, Jinterp_ideal, xlim=xlim, ylim=ylim, label='Tandem (Ideal)')
        plot_JV_tandem(Vext_sub1, Jext_sub1, Vext_sub2, Jext_sub2, Vtandem, Jinterp, xlim=xlim, ylim=ylim, plotPerfectContact=True, Vtandem_perfcontact=Vtandem_perfcontact)

        plt.savefig(os.path.join(session_path, 'JV_tandem.png'), dpi=300)
        plt.show()

    if cleanup_files:
        # Cleanup files
        files_to_remove = [genProf_sub1_filename, result_sub1[2], result_sub1[3], genProf_sub2_filename, result_sub2[2], result_sub2[3]] # Do not remove the JV files of the subcells
        for file in files_to_remove:
            file_path = os.path.join(session_path, file)
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    
    lid_sub1_end = 3 # Index of last layer of subcell 1
    lid_sub2_start = 5 # Index of first layer of subcell 2
    rec_contact_type = 1#2 # 1) Resistance 2) Anlytisch

    # Parameters recContact = 1
    Rrec = 1E-3 # Ohm m^2
    # Parameters recContact = 2
    Vp = 0.2 # V
    Jp = 50 # Am^-2

    # SIMsalabim parameters
    sim_setup_tandem = "simulation_setup.txt"
    session_path = os.path.join('../../','SIMsalabim','SimSS')
    JVFile = 'JV.dat'
    varFile = 'none'
    logFile = 'log.txt'

    # UUID = str(uuid.uuid4()) # Add a UUID to the simulation
    UUID = ''

    ############## Command line arguments  ##############
    ## Notes
    ## - The command line arguments are optional and can be provided in any order
    ## - Each command line argument must be provided in the format -par_name value
    ## - Possible arguments include all SIMsalabim parameters and Hysteresis JV specific parameters as listed before
    ## - Special arguments
    ##   - sp : string
    ##     - The session path, i.e. the working directory for the simulation
    ##   - sim_setup_tandem : string
    ##     - The name of the zimt simulation setup parameters file of the complete tandem
    ##   - UUID : string
    ##     - An UUID to add to the simulation (output)

    cmd_pars_dict = {}
    cmd_pars = []

    # Check if any arguments are provided.
    if len(sys.argv) >= 2:
        # Each arguments should be in the format -par val, i.e. in pairs of two. Skip the first argument as this is the script name
        if not len(sys.argv[1:]) % 2 == 0:
            print('Error in command line parameters. Please provide arguments in the format -par_name value -par_name value ...')
            sys.exit(1)
        else:
            input_list = sys.argv[1:]
            # Loop over the input list and put pairs into a dictionary with the first argument as key and the second argument as value
            for i in range(0,len(input_list),2):
                # Check if the key already exists, if not, add it to the cmd_pars_dict
                if str(input_list[i][1:]) in cmd_pars_dict:
                    print(f'Duplicate parameter found in the command line parameters: {str(input_list[i][1:])}')
                    sys.exit(1)
                else:
                    cmd_pars_dict[str(input_list[i][1:])] = str(input_list[i+1])

    # Check and process specific keys/arguments that are not native SIMsalabim arguments
    # Handle the session_path/sp argument separately, as the other parameters depend on this
    if 'sp' in cmd_pars_dict:
        session_path = cmd_pars_dict['sp']
        # remove from cmd_pars
        cmd_pars_dict.pop('sp')

    # Define mappings for keys and variables
    key_action_map = {
        'sim_setup_tandem': lambda val: {'sim_setup_tandem': val},
        'lid_sub1_end': lambda val: {'lid_sub1_end': int(val)},
        'lid_sub2_start': lambda val: {'lid_sub2_start': int(val)},
        'rec_contact_type': lambda val: {'rec_contact_type': int(val)},
        'Rrec': lambda val: {'Rrec': float(val)},
        'Vp': lambda val: {'Vp': float(val)},
        'Jp': lambda val: {'Jp': float(val)},
        'UUID': lambda val: {'UUID': val},
    }

    for key in list(cmd_pars_dict.keys()):  # Use list to avoid modifying the dictionary while iterating
        if key in key_action_map:
            # Apply the corresponding action
            result = key_action_map[key](cmd_pars_dict[key])
            globals().update(result)  # Dynamically update global variables
            cmd_pars_dict.pop(key)

    # Handle remaining keys in `cmd_pars_dict` and add them to the cmd_pars list
    cmd_pars.extend({'par': key, 'val': value} for key, value in cmd_pars_dict.items())

    run_tandem_simu(sim_setup_tandem, session_path, lid_sub1_end, lid_sub2_start, rec_contact_type, Rrec, Vp, Jp, True, False 
                    , JVFile, varFile, logFile, cmd_pars = cmd_pars, UUID=UUID)