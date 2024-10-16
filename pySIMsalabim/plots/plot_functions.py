"""Functions for plotting"""
######### Package Imports #########################################################################

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from pySIMsalabim.plots import plot_def

######### Function Definitions ####################################################################

def plot_result(data, pars, selected, x_key, xlabel, ylabel, xscale, yscale, title, ax, plot_funcs, x_error = [], y_error=[], legend=True, error_fmt='-'):
    """Make a plot for a (sub)set of parameters from a DataFrame. Note: errorbars only work with single x,y functions


    Parameters
    ----------
    data : DataFrame
        Data to plot
    pars : dict
        Dict with all potential parameters to plot. Keys represent the names in the dataFrama, values are the corresponding labels
    selected : list
        List with the names of the selected parameters to plot. Names match the names in the dataFrame. TO use all parameters, set selected to list(pars.keys())
    x_key : string
        Key in the dataframe for the 'x' axis data
    xlabel : string
        Label for the x-axis. Format: parameter [unit]
    ylabel : string
        Label for the y-axis. Format: parameter [unit]
    xscale : string
        Scale of the x-axis. E.g linear or log
    yscale : string
        Scale of the y-axis. E.g linear or log
    title : string
        Title of the plot
    ax : axes
        Axes object for the plot
    plot_funcs : Any
        Type of plot, e.g. standard plot or scatter
    x_error : List, optional
        List with error on the x parameter, by default []
    y_error : List, optional
        List with the error on the y parameter, by default []
    legend : bool, optional
        Toggle between showing the legend in the plot, by default True
    error_fmt : str, optional
        Format of the errorbars, by default '-'
    Returns
    -------
    axes
        Updated Axes object for the plot
    """
    i = 0
    for y_var in selected: # Plot the curve for every parameter specified in pars
        if (sum(data[y_var]) != 0):
            if plot_funcs == plt.errorbar:
                if len(x_error) == 0 and len(y_error) != 0:
                    plot_funcs(data[x_key], data[y_var], label=pars[y_var], yerr = y_error, color=plot_def.color[i], fmt=error_fmt)
                elif len(x_error) != 0 and len(y_error) != 0:
                    plot_funcs(data[x_key], data[y_var], label=pars[y_var], xerr = x_error, color=plot_def.color[i], fmt=error_fmt)
                elif len(x_error) != 0 and len(y_error) != 0:
                    plot_funcs(data[x_key], data[y_var], label=pars[y_var], xerr = x_error, yerr = y_error, color=plot_def.color[i], fmt=error_fmt)
                else:
                    plot_funcs(data[x_key], data[y_var], label=pars[y_var], color=plot_def.color[i], fmt=error_fmt)
            else: 
                 plot_funcs(data[x_key], data[y_var], label=pars[y_var], color=plot_def.color[i])               
        i += 1
    # Set figure and axis properties
    if legend:
        ax.legend()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.set_title(title)
    return ax

def plot_result_colorbar_single(x,y,weight, ax,fig, xlabel, ylabel, weight_label, weight_norm, title, xscale='linear', yscale='linear'):
    """Show a x,y plot but use a colorbar to indicate a third parameter, similar to adding a weight to each point.

    Parameters
    ----------
    x : array
        Array with the x-data to plot
    y : array
        Array with the y data to plot
    weight : array
        Array with the weights for the colorbar
    ax : axes
        Axes object for the plot
    fig : figure
        Figure object for the plot
    xlabel : string
        label for the x-axis
    ylabel : string
        label for the y-axis
    weight_label : string
        label for the weights/colorbar
    weight_norm : string
        the scale for the colorbar, 'linear' or 'log'
    title : string
        Title of the plot
    xscale : str, optional
        set the scale of the x-axis, by default 'linear'
    yscale : str, optional
        set the scale of the y-axis, by default 'linear'

    Returns
    -------
    ax,fig
        return the axes,figure objects
    """

    # Divide the arrays into segments to color each segment individually
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Normalize the array for the colorbar (the weights), use either a log or lin scale
    if weight_norm == 'log':
        norm = matplotlib.colors.LogNorm(weight.min(), weight.max())
    else:
        norm = matplotlib.colors.Normalize(weight.min(), weight.max())

    lc = LineCollection(segments, cmap='plasma', norm=norm)
    lc.set_array(weight)

    # Create a colorbar plot
    line = ax.add_collection(lc)
    fig.colorbar(line, ax=ax, label=weight_label)          

    ax.margins(0.04) # Set some padding around the curve in the figure, because the method used here, puts the edges of the curve on the axis or takes the normalized axes.

    # Set figure properties
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.set_title(title)
    
    return ax, fig
    

def plot_result_twinx(data, pars, selected_1, selected_2, x_key, xlabel, ylabel_1, ylabel_2, xscale, yscale_1, yscale_2, title,ax1,ax2, plot_funcs, 
                        x_error=[], y_error_1 = [], y_error_2 = []):
    """Plot data on two y axis with a shared x axis. DIfferentiate between regular and errorbar plots.

    Parameters
    ----------
    data : DataFrame
        Data to plot
    pars : dict
        Dict with all potential parameters to plot. Keys represent the names in the dataFrama, values are the corresponding labels
    selected_1 : List
        List with the names of the selected parameters to plot on the left y axis.
        Names match the names in the dataFrame. TO use all parameters, set selected to list(pars.keys())
    selected_2 : List
        List with the names of the selected parameters to plot on the right y axis.
        Names match the names in the dataFrame. TO use all parameters, set selected to list(pars.keys())    x_key : _type_
        _description_
    xlabel : string
        Label for the x-axis. Format: parameter [unit]
    ylabel_1 : string
        Label for the left y-axis. Format: parameter [unit]
    ylabel_2 : _type_
        Label for the right y-axis. Format: parameter [unit]
    xscale : string
        Scale of the x-axis. E.g linear or log
    yscale_1 : string
        Scale of the left y-axis. E.g linear or log
    yscale_2 : string
        Scale of the right y-axis. E.g linear or log
    title : string
        Title of the plot
    ax1 : axes
        Axes object for the plot
    ax2 : axes
        Axes object for the plot (right y axis)
    plot_funcs : any
        Type of plot, e.g. standard plot or scatter
    x_error : list, optional
        _description_, by default []
    y_error_1 : list, optional
        List with error on the x parameter, by default []
    y_error_2 : list, optional
        List with error on the x parameter, by default []
    """
    
    # Set the x-axis
    ax1.set_xlabel(xlabel)
    ax1.set_xscale(xscale)

    ax1.set_title(title)

    # Set the left y axis
    ax1.set_ylabel(ylabel_1)
    ax1.set_yscale(yscale_1)

    #LEFT axis
    i = 0
    for y_var in selected_1:
        if (sum(data[y_var]) != 0):
            if plot_funcs == plt.errorbar:
                # Errorbar plot
                ax1.errorbar(data[x_key], data[y_var], yerr=y_error_1, label=pars[y_var],color=plot_def.color[i])
            else:
                if plot_funcs == plt.plot:
                    # Line plot
                    ax1.plot(data[x_key], data[y_var], label=pars[y_var],color=plot_def.color[i])
                elif plot_funcs == plt.scatter:
                    # Scatter plot
                    ax1.scatter(data[x_key], data[y_var], label=pars[y_var],color=plot_def.color[i])
        i += 1
    
    # RIGHT axis

    # Set the right y-axis
    ax2.set_ylabel(ylabel_2,color=plot_def.color[3])
    ax2.tick_params(axis='y', labelcolor=plot_def.color[3])
    ax2.set_yscale(yscale_2)

    i = 0
    for y_var in selected_2:
        if (sum(data[y_var]) != 0):
            if plot_funcs == plt.errorbar:
                # Errorbar plot
                ax2.errorbar(data[x_key], data[y_var], yerr = y_error_2, label=pars[y_var],color=plot_def.color[3],linestyle='dashed')
            else:
                if plot_funcs == plt.plot:
                    # Line plot
                    ax2.plot(data[x_key], data[y_var], label=pars[y_var],color=plot_def.color[3],linestyle='dashed')
                elif plot_funcs == plt.scatter:
                    # Scatter plot
                    ax2.scatter(data[x_key], data[y_var], label=pars[y_var],color=plot_def.color[3],linestyle='dashed')
    i += 1

    # Find the plotted lines and their labels on both axes
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc=0)
    return ax1
