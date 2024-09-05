"""Functions for page: Simulation_results"""
######### Package Imports #########################################################################

import matplotlib.pyplot as plt
import streamlit as st
from pySIMsalabim.plots import plot_functions_gen as utils_plot_gen

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

def plot_result_JV(data, choice_voltage, plot_funcs, ax, exp, data_exp=''):
    """Make a plot of the JV curve based on the 'JV.dat" file

    Parameters
    ----------
    data : DataFrame
        All output data from the JV.dat file
    choice_voltage : float
        The Vext potential for which the data in Var.dat is shown
    plot_funcs : Any
        Type of plot    # Set figure and axis properti
    ax : axes
        Axes object for the plot
    exp : boolean
        True if experimental JV curve needs to be plotted.
    data_exp : DataFrame
        Optional argument when an experimental JV curve is supplied
    Returns
    -------
    axes
        Updated Axes object for the plot
    """
    # We only need one label when making the line and scatter plot.
    if plot_funcs == plt.plot:
        plot_funcs(data['Vext'], data['Jext'], label='Simulated')
    else:
        plot_funcs(data['Vext'], data['Jext'])

    # Vertical line to show the selected voltage (Vext)    
    ax.axvline(choice_voltage, color='k', linestyle='--')

    # Configure plot
    ax.set_xlabel('$V_{ext}$ [V]')
    ax.set_ylabel('$J_{ext}$ [Am$^{-2}$]')
    ax.set_title('Current-voltage characteristic')

    # Add an experimental curve to the plot when needed. Add a legend because we have two different curves.
    if exp is True:
        if plot_funcs == plt.plot:
            plot_funcs(data_exp['Vext'], data_exp['Jext'], label='Experimental')
        else:
            plot_funcs(data_exp['Vext'], data_exp['Jext'])
        ax.legend()

    # Without experimental data, there is no need for a legend. It is just a single JV curve.
    if exp is False:
        legend = ax.legend()
        legend.remove()

    # Indicate the x,y axis
    ax.axhline(y=0, color='gray', linewidth=0.5)
    ax.axvline(x=0, color='gray', linewidth=0.5)

    return ax

def get_nonzero_parameters(pars, data, choice_voltage):
    """Check if a parameter is not equal to zero for a certain voltage. 
    If so, remove it from the options to plot, because it will not show up anyway.

    Parameters
    ----------
    pars : dict
        Dictionary with parameter names and labels
    data : DataFrame
        All output data from the 'Var' file
    choice_voltage : float
        The Vext potential for which to show the data

    Returns
    -------
    dict
        Updtaed dictionary with parameter names and labels
    """
    for par in list(pars.keys()):
        if sum(data[data['Vext'] == choice_voltage][par]) == 0:
            pars.pop(par)
    
    return pars

def create_UI_component_plot(data_org, pars, x_key, xlabel, ylabel, title, plot_no, fig, ax, plot_type,
                             cols, choice_voltage = 0, source_type = '', show_plot_param=True, show_yscale=True, yscale_init=0, xscale_init=0, 
                             show_xscale=False, weight_key = '', weight_label = '', weight_norm = 'linear', error_x = '', error_y='', show_legend=True,error_fmt='-'):
    """Create a plot for the provided data and place it into a column structure. 
    Add the plot options to the right of the plot when needed. 
    When plotting a 'Var' type file, plot only for the selected voltage

    Parameters
    ----------
    data_org : DataFrame
        Unfiltered data to plot
    pars : dict
        Dict with all potential parameters to plot. Keys represent the names in the dataFrama, values are the corresponding labels
    x_key : string
        Key in the dataframe for the 'x' axis data
    xlabel : string
        Label for the x-axis. Format: parameter [unit]
    ylabel : string
        Label for the y-axis. Format: parameter [unit]
    title : string
        Title of the plot
    plot_no : integer
        Plot number, used as unique identifier
    fig : Figure
        The figure object
    ax : axes
        Axes object for the plot
    plot_type : Any
        Type of plot, e.g. standard plot or scatter
    cols : List
        List with columns to plot figure in (Streamlit specific)
    choice_voltage : float, optional
        The Vext potential for which to show the data. Only relevant when plotting from a 'Var' file
    source_type : string, optional
        From what file type originates the data. Only relevant when equal to 'Var'
    show_plot_param : bool, optional
        Show the multiselectbox to select which parameters to plot, by default True
    show_yscale : bool, optional
        Show a radio toggle to switch between a linear or log y scale, by default true
    yscale_init : int, optional
        Initial scale of the y-axis, used in yscale_options, by default 0
    xscale_init : int, optional
        Initial scale of the x-axis, used in xscale_options, by default 0
    show_xscale : bool, optional
        Show a radio toggle to switch between a linear or log x scale, by default true
    weight_key : string, optional
        Key in the dataframe for the colorbar data, ignored if empty string, by default ''
    weight_label : string, optional
        Label for the colorbar. Format: parameter [unit]
    weight_norm : string, optional
        Scale of the colorbar, 'linear' or 'log', by defailt 'linear'
    error_x : string, optional
        Dataframe key of the column with the error in x, by default ''
    error_y : string, optional
        Dataframe key of the column with the error in y, by default ''
    show_legend : bool, optional
        Toggle between showing the legend in the plot, by default True
    error_fmt : str, optional
        Format of the errorbars, by default '-'

    Returns
    -------
    Figure
        Updated Figure object
    Axes
        Updated Axes object 
    """
    
    scale_options = ['linear', 'log']
    error_options = [True, False]

    if source_type == 'Var':
        # Remove parameters that are 'zero' over the full 'x' range
        pars = get_nonzero_parameters(pars, data_org, choice_voltage)
        data = data_org[data_org['Vext'] == choice_voltage] # Plot the data for the chosen voltage
    else:
        data = data_org

    with cols[2]:
        if show_plot_param or show_yscale or show_xscale:
            # Figure options
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<hr>', unsafe_allow_html=True)

        with st.expander('Figure options', expanded=False):
            # Select which parameters to plot
            if show_plot_param:
                options = st.multiselect('Parameters to plot:', list(pars.keys()), list(pars.keys()), key = str(plot_no) + '-par-options')
                st.markdown('<br>', unsafe_allow_html=True)
                st.markdown('<br>', unsafe_allow_html=True)
            else:
                options =  list(pars.keys())

            # Select the y-scale
            if show_yscale:
                yscale = st.radio('y-scale', scale_options, index = yscale_init, key = str(plot_no) + '-y-scale')
            else:
                yscale = scale_options[yscale_init]

            # Select the x-scale
            if show_xscale:
                xscale = st.radio('x-scale', scale_options, index = xscale_init, key = str(plot_no) + '-x-scale')
            else:
                xscale = scale_options[xscale_init]

            # Show the error margin on y1 axis
            if plot_type == plt.errorbar:
                xyerror = st.radio('Show error margins', error_options, index = 0, key = str(1) + '-error_margin')
            else:
                xyerror = error_options[0]

    with cols[1]:
        # Create plot
        fig, ax = plt.subplots()
        if weight_key != '':
            ax,fig = utils_plot_gen.plot_result_colorbar_single( data[x_key],data[options[0]],data[weight_key], ax,fig, xlabel, 
                                                                ylabel, weight_label,weight_norm, title,xscale, yscale,)
        else:
            if xyerror and plot_type == plt.errorbar:
                if error_x == '' and  error_y != '':
                    # Only y errorbar
                    ax = utils_plot_gen.plot_result(data, pars, options, x_key, xlabel, ylabel,xscale, yscale, title, ax, plot_type, y_error=data[error_y],legend=show_legend,error_fmt=error_fmt)
                elif error_x != '' and error_y == '':
                    # only x errorbar
                    ax = utils_plot_gen.plot_result(data, pars, options, x_key, xlabel, ylabel,xscale, yscale, title, ax, plot_type, x_error = data[error_x],legend=show_legend,error_fmt=error_fmt)
                elif error_x != '' and not error_y != '':
                    # both x and y errorbars
                    ax = utils_plot_gen.plot_result(data, pars, options, x_key, xlabel, ylabel,xscale, yscale, title, ax, plot_type, x_error = data[error_x], y_error=data[error_y],legend=show_legend,error_fmt=error_fmt)
                else:
                    # no errorbars
                    ax = utils_plot_gen.plot_result(data, pars, options, x_key, xlabel, ylabel,xscale, yscale, title, ax, plot_type,legend=show_legend,error_fmt=error_fmt)

            else:
                ax = utils_plot_gen.plot_result(data, pars, options, x_key, xlabel, ylabel,xscale, yscale, title, ax, plt.plot,legend=show_legend)
        
        return fig,ax

def create_UI_component_plot_twinx(data_org, pars, selected_1, selected_2, x_key, xlabel, ylabel_1, ylabel_2, title, fig, ax_1, ax_2, 
                             cols, show_plot_param=True, show_yscale_1=True, show_yscale_2 = True, 
                              yscale_init_1 = 0, yscale_init_2 = 0, show_errors=True, yerror_1 = [], yerror_2 = []):
    """_summary_

    Parameters
    ----------
    data_org : DataFrame
        Unfiltered data to plot
    pars : dict
        Dict with all potential parameters to plot. Keys represent the names in the dataFrama, values are the corresponding labels
    selected_1 : List
        Name of selected parameter to plot on the left y-axis
    selected_2 : List
        Name of selected parameter to plot on the right y-axis
    x_key : string
        Key in the dataframe for the 'x' axis data
    xlabel : string
        Label for the x-axis. Format: parameter [unit]
    ylabel_1 : string
        Label for the left y-axis. Format: parameter [unit]
    ylabel_2 : string
        Label for the left y-axis. Format: parameter [unit]
    title : string
        Title of the plot
    fig : Figure
        Figure object
    ax_1 : axes
        Axes object for the plot (left)
    ax_2 : axes
        Axes object for the plot (right)
    cols : List
        List with columns to plot figure in (Streamlit specific)
    show_plot_param : bool, optional
        Show the multiselectbox to select which parameters to plot, by default True
    show_yscale_1 : bool, optional
        Show a radio toggle to switch between a linear or log y scale (left), by default true
    show_yscale_2 : bool, optional
        Show a radio toggle to switch between a linear or log y scale (right), by default true
    yscale_init_1 : int, optional
        Initial scale of the left y-axis, used in yscale_options, by default 0
    yscale_init_2 : int, optional
        Initial scale of the right y-axis, used in yscale_options, by default 0
    show_errors : bool, optional
        Toggle between showing errors, by default True
    yerror_1 : List, optional
        List with error values for the left axis
    yerror_2 : List, optional
        List with error values for the right axis    
    """
    #Only support for impedance plot currently
    
    scale_options = ['linear', 'log']
    error_options = [True, False]

    with cols[2]:
        if show_plot_param or show_yscale_1 or show_yscale_2:
            # Figure options
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<hr>', unsafe_allow_html=True)

        with st.expander('Figure options', expanded=False):
            # Select which parameters to plot
            if show_plot_param:
                options = st.multiselect('Parameters to plot:', list(pars.keys()), list(pars.keys()), key = str(1) + '-par-options' + str(selected_1))
                st.markdown('<br>', unsafe_allow_html=True)
                st.markdown('<br>', unsafe_allow_html=True)
            else:
                options =  list(pars.keys())

            # Select the y1-scale
            if show_yscale_1:
                yscale_1 = st.radio('y-scale (Left)', scale_options, index = yscale_init_1, key = str(1) + '-y1-scale' + str(selected_1))
            else:
                yscale_1 = scale_options[yscale_init_1]

            # Select the y2-scale
            if show_yscale_2:
                yscale_2 = st.radio('y-scale (Right)', scale_options, index = yscale_init_2, key = str(1) + '-y2-scale' + str(selected_1))
            else:
                yscale_2 = scale_options[yscale_init_2]

            # Show the error margin on y1 axis
            if show_errors:
                yerror = st.radio('Show error margins', error_options, index = 0, key = str(1) + '-y-error' + str(selected_1))
            else:
                yerror = error_options[1]

    with cols[1]:
        # Create plot
        if yerror:
            ax = utils_plot_gen.plot_result_twinx(data_org, pars, selected_1, selected_2, x_key, xlabel, ylabel_1, ylabel_2, 'log', yscale_1, yscale_2, title,ax_1,ax_2, 
                                        plt.errorbar,y_error_1 = yerror_1, y_error_2 = yerror_2)   
        else:
            ax = utils_plot_gen.plot_result_twinx(data_org, pars, selected_1, selected_2, x_key, xlabel, ylabel_1, ylabel_2, 'log', yscale_1, yscale_2, title,ax_1,ax_2, 
                                        plt.plot)
        st.pyplot(fig, format='png')
