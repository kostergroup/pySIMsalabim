"""Draw the energy band diagram"""
######### Package Imports #########################################################################

import os
import matplotlib.pyplot as plt
import pySIMsalabim
from pySIMsalabim.utils import device_parameters as utils_dev

######### Function Definitions ####################################################################

def create_width_label(x_left, x_right, x_corr, value, y_min, ax, color):
    """ Create the label to display the width of a layer on the width bar

    Parameters
    ----------
    x_left : float
        Left x position of the layer [m]
    x_right : float
        right x position of the layer [m]
    x_corr : float
        Correction factor to place the label in the middle of the layer
    value : float
        Width of the layer [m]
    y_max : float
        Lowest energy level of the device [eV]
    ax : axes
        Axes object for the plot
    color : string
        Color of the label
    """
    ax.text((x_left+x_right)/2-x_corr, y_min-2.0, round(value*1e9), color=color)


def plot_device_widths(ax, y_min, L, L_original):
    """Plot a width bar below the band energy diagram with the thickness of each layer.

    Parameters
    ----------
    ax : axes
        Axes object for the plot
    y_max : float
        Lowest energy level [eV]
    L : float
        Full width of the device [m]
    L_original : List
        List with the layer widths before scaling
    """
    # Horizontal line below the band diagram 
    ax.hlines(y_min-1.4, 0, sum(L), color='k')

    # Add a small vertical line at each boundary/interface between two layers and add a label with the width of the layer
    for i in range(len(L)):
        ax.vlines(sum(L[:i]), y_min-1.2, y_min-1.6, color='k')
        create_width_label(sum(L[:i]), sum(L[:i+1]), 0.02*sum(L), L_original[i], y_min, ax, 'k')
    
    # Add the vertical line at the right most side 
    ax.vlines(sum(L), y_min-1.2, y_min-1.6, color='k')

    # Add label with unit of [nm] to the end of the horizontal label
    ax.text(1.04*sum(L), y_min-2.0, '[nm]', color='k')


def create_energy_label(x_left, x_right, L, y, band_type, position, ax, vert_pos='top', band_level_two_decimals=False):
    """Create and place the label for an energy level (in eV) of a layer

    Parameters
    ----------
    x_left : float
        Left x position of the layer [m]
    x_right : float
        right x position of the layer [m]
    L : float
        Full width of the device [m]
    y : float
        Energy of the band [eV]
    band_type : string
        Type of band (CB, VB, Electrode)
    position : float
        Full length of the device
    ax : axes
        Axes object for the plot
    """

    # Offset of the labels to not overlap with the layers
    if vert_pos == 'top':
        offset = 0.11
    else:
        offset = -0.4

    # If the layer covers over 20% of the figure size, move the label to the x middle of the figure. Else align it to the left side of the layer.
    if (x_right - x_left) > 0.2*position:
        if band_level_two_decimals:
            ax.text((x_left+x_right)/2 + 0.01*L, y+offset, f'{y:.2f}')
        else:
            ax.text((x_left+x_right)/2 + 0.01*L, y+offset, y)
    elif 'WR' in band_type:
        # In case of the right WF, we must align the text to the right of the label
        if band_level_two_decimals:
            ax.text(x_right+ 0.01*L, y+offset, f'{y:.2f}', horizontalalignment='right')
        else:
            ax.text(x_right+ 0.01*L, y+offset, y, horizontalalignment='right')
    else:
        if band_level_two_decimals:
            ax.text(x_left+ 0.01*L, y+offset, f'{y:.2f}')
        else:
            ax.text(x_left+ 0.01*L, y+offset, y)

def get_param_band_diagram(dev_par, layers, dev_par_name, cmd_pars=[], band_level_two_decimals=False):
    """Create and display the band diagram on the UI based on the relevant parameters from the dict object

    Parameters
    ----------
    dev_par : dict
        Dictionary with all data
    layers : List
        List with all the layers in the device
    dev_par_name : string
        Name of the device parameter file
    """
    msg = '' # Init error message string

    # Init arrays for thicknesses and energy levels
    L = []
    E_c = []
    E_v = []

    ### Get the values in the simulation_setup
    # Get the work functions of the electrodes
    for section in dev_par[dev_par_name]:
        if section[0] == 'Contacts':
            for param in section:
                if 'W_L' in param[1]:
                    W_L = -float(param[2])
                    # {'par':'W_L', 'val':W_L}
                elif 'W_R' in param[1]:
                    W_R = -float(param[2])
                    # {'par':'W_R', 'val':W_R}


    # Get the thicknesses and energy levels from the respective layer files
    for layer in layers[1:]:
        for section in dev_par[layer[2]]:
            if section[0] == 'General':
                for param in section:
                    if param[1] in 'L':
                        L.append(float(param[2]))
                    elif param[1] in 'E_c':
                        E_c.append(-float(param[2]))
                    elif param[1] in 'E_v':
                        E_v.append(-float(param[2]))

    

    ### Overwrite values from the simulation_setup, if parameters are defined on the command line
    overrides = {}
    for item in cmd_pars:
        if item['par'] in overrides:
            raise ValueError(f"Duplicate parameter found: {item['par']}")
        overrides[item['par']] = float(item['val'])
        
    # Overwrite electrode work functions (keeping the negative sign)
    if 'W_L' in overrides:
        W_L = -overrides['W_L']
    if 'W_R' in overrides:
        W_R = -overrides['W_R']
    
    # Overwrite layer parameters (l1 -> index 0, l2 -> index 1, etc.)
    for i in range(len(L)):
        prefix = f"l{i + 1}."
        
        if f"{prefix}L" in overrides:
            L[i] = overrides[f"{prefix}L"]
        if f"{prefix}E_c" in overrides:
            E_c[i] = -overrides[f"{prefix}E_c"]
        if f"{prefix}E_v" in overrides:
            E_v[i] = -overrides[f"{prefix}E_v"]
    
    # Create a figure where the band diagram will be plotted
    # Each element from the array is a layer in the device
    fig, ax = plt.subplots(figsize = (15,5))

    E_high = max(E_v) # To properly place the horizontal width bar
    L_total = sum(L) # Total thickness of the device

    L_real = L.copy() # Create a backup of the widths before adjusting for plotting, used for creating the width labels

    # Create acolor list with 25 standard colors. 
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    # Create and plot a color block to indicate the bands of a layer
    for i in range(len(L)):
        # If the layer thickness is less than 9% of the full device thickness, rescale to 9% to remain visible.
        if L[i] < 0.09*L_total:
            L[i] = 0.09*L_total

        ax.fill_between([sum(L[:i]), sum(L[:i+1])], [E_c[i], E_c[i]], y2=[E_v[i], E_v[i]], color=colors[i])
        create_energy_label(sum(L[:i]), sum(L[:i+1]),sum(L), E_c[i], 'CB', L_total, ax, 'top', band_level_two_decimals)
        create_energy_label(sum(L[:i]), sum(L[:i+1]),sum(L), E_v[i], 'VB', L_total, ax, 'bot', band_level_two_decimals)
    
    L_total = sum(L) # update with the corrected values

    # Based on the alignment of W_R/W_L set the proper position of the labels
    if W_L > W_R:
        W_L_pos = 'top'
        W_R_pos = 'bot'
    else:
        W_L_pos = 'bot'
        W_R_pos = 'top'   

    # Left Electrode
    ax.plot([-0.06*L_total, 0], [W_L, W_L], color='k')
    create_energy_label(-0.08*L_total, 0, sum(L), W_L, 'WL', L_total, ax, W_L_pos, band_level_two_decimals)

    # Right Electrode
    ax.plot([L_total, L_total+0.06*L_total], [W_R, W_R], color='k')
    create_energy_label(L_total, L_total+0.08*L_total, sum(L), W_R, 'WR', L_total, ax, W_R_pos, band_level_two_decimals)

    # Hide the figure axis
    ax.axis('off')

    # Add a horizontal bar to the figure width the layer widths for an arbitray number of layers
    plot_device_widths(ax, E_high, L, L_real)

    if msg != '':
        # Error encountered, return message
        return msg
    else:
        return fig

def plot_band_diagram(dev_par_file_name, session_path, cmd_pars=[], band_level_two_decimals=False ):
    """Plot the band diagram of the device based on the device parameter file and the session path

    Parameters
    ----------
    dev_par_file_name : string
        Name of the device parameter file
    session_path : string
        Path to the session folder
    """
    # Load the device parameter file
    dev_par, layers = pySIMsalabim.utils_dev.load_device_parameters(session_path, dev_par_file_name)

    # Create and display the band diagram
    fig = get_param_band_diagram(dev_par, layers, dev_par_file_name, cmd_pars, band_level_two_decimals)
    plt.show()
    return fig
