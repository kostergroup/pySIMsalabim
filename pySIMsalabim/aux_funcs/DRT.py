"""Find System Lifetimes using Distribution of Relaxation Times (DRT) Fitting in the Time Domain"""
######### Package Imports #########################################################################

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
# from pySIMsalabim.utils import device_parameters as utils_dev
import argparse
import sys
import os
import traceback
import pickle
import pandas as pd
import numpy as np
import osqp
from scipy.sparse import csc_matrix
from sklearn.metrics import mean_squared_error, r2_score
try:
    import pySIMsalabim as sim
except ImportError: # add parent directory to sys.path if pySIMsalabim is not installed
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import pySIMsalabim as sim
from pySIMsalabim.plots import plot_functions


DRT_VERSION = "0.8"


######### References ##############################################################################

# [1] M. Schönleber, D. Klotz, and E. Ivers-Tiffée, ‘A Method for Improving the Robustness of linear 
# Kramers-Kronig Validity Tests’, Electrochimica Acta, vol. 131, pp. 20–27, June 2014, 
# doi: 10.1016/j.electacta.2014.01.034.

# [2] B. Stellato, G. Banjac, P. Goulart, A. Bemporad, and S. Boyd, ‘OSQP: an operator splitting solver 
# for quadratic programs’, Math. Prog. Comp., vol. 12, no. 4, pp. 637–672, Dec. 2020, 
# doi: 10.1007/s12532-020-00179-2.


######### Class Definitions #######################################################################


class DRT_Fit_Result:
    """ A class that bundles together all results from fitting a predict_y_model curve to data

    Attributes
    ----------
    U : numpy.ndarray, shape (m,)
        Fitted coefficients [U_1, U_2, ..., U_m]
    tau : numpy.ndarray, shape (m,)
        Fitted lifetimes [tau_1, tau_2, ..., tau_m]
    y_inf : float
        y_inf of the steady state of the fitted signal from 0
    m : int
        Number of lifetimes/coefficients used in predict_y_model, given by the length of U/tau
    y_model : {None, numpy.ndarray}
        Model given by
            y_model = U_1*exp(-t/tau_1) + U_2*exp(-t/tau_2)... + U_m*exp(-t/tau_m) + y_inf
    U_norm : {None, numpy.ndarray with shape (m,)}
        Fitted coefficients normalised by np.sum(self.U)
    MSE : float 
        Mean square error between the model (self.y) and the fitted signal
    R_2 : float 
        R^2 error between the model (self.y) and the fitted signal

        
    Methods
    -------
    predict_y_model(t)
        Calculates predict_y_model(t) using the object's attributes (self.U, self.tau, self.y_inf)
        and sets self.predict_y_model equal to the result 
    set_U_norm()
        Sets self.U_norm to U/np.sum(U)
    """
    def __init__(self, time, tau, U, y_inf, y=None, MSE=None, R_2=None):
        self.time = time
        self.U = U
        self.tau = tau 
        self.y_inf = y_inf 
        self.m = len(self.tau)
        self.y_model = None
        self.MSE = MSE
        self.R_2 = R_2
        self.U_norm = None


    def set_y_model(self, t):
        """ Sets self.predict_y_model = predict_y_model(t) using the objects attributes

        Parameters
        ----------
        t : float or list/numpy.ndarray, shape (n,)
            Time values to calculate the predict_y_model curve
        backend : {'numpy', 'torch'} (optional)
            Determines whether matrix operations are done with numpy or pytorch. Default numpy. 
        device : torch.device (optional)
            Determines what device is used for matrix ops if backend='torch'.
        
        Returns
        -------
        None
        """
        self.y_model = predict_y_model(t, self.U, self.tau, self.y_inf)


    def set_U_norm(self):
        """
        Set self.U_norm equal to self.U/np.sum(self.U)
        """
        self.U_norm = self.U/np.sum(self.U)


    def plot_U(self, normalised=False, tau_analytic=None, U_analytic=None, xaxis_label='$\\tau$ [s]', 
           yaxis_label='Auto', U_model_label='Model', U_label='Analytic', plot_title='DRT', return_ax=False):
        """
        Plot the fitted DRT against an optional analytic DRT
        
        Parameters
        ----------
        normalised : bool (optional)
            Determines whether self.U (False) or self.U_norm (Ture) is plotted. Default (False)
        tau_analytic : {None, numpy.ndarray shape (l,)} (optional)
            Array of tau values use to generate the analytic curve, if known. This is mostly for 
            comparision if fitting to a known DRT for testing purposes. Default None.
        U_analytic : {None, numpy.ndarray shape (l,)} (optional)
            Array of U values used in the analytic curve, if known. This is mostly for 
            comparision if fitting to a known DRT for testing purposes. Default None.
        xaxis_label : str (optional)
            Label for the x axis of the output plot. '$\\tau$ [s]' by default.
        yaxis_label : str (optional)
            Label for the y axis of the output plot. 'U' by default.
        U_model_label : str (optional)
            Label for the curve U_model in the output plot legend. 'Model' by default.
        U_label : str (optional)
            Label for the U_analytic curve in the output plot legend. 'Analytic' by default.
        plot_title : str (optional)
            Title of the output plot. 'DRT' by default.
        return_ax : bool (optional)
            Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
            Default False.

        Returns
        -------
        ax : matplotlib.axes.Axes (optional)
            Returned axes object if return_ax is True.
        """
        
        U = self.U_norm if normalised else self.U

        if yaxis_label == 'Auto':
            if normalised:
                yaxis_label = '$U_{\\text{norm}}$'
            else: 
                yaxis_label = '$U$'
        else: 
            yaxis_label = yaxis_label

        ax = plot_U(self.tau, U, tau_analytic=tau_analytic, U_analytic=U_analytic, xaxis_label=xaxis_label, 
                yaxis_label=yaxis_label, U_model_label=U_model_label, U_label=U_label, 
                plot_title=plot_title, return_ax=return_ax)
        
        if isinstance(ax, Axes):
            return ax
        

    def plot_cumulative_U(self, normalised=False, tau_analytic=None, U_analytic=None, xaxis_label='$\\tau$ [s]', 
                      yaxis_label='Auto', U_model_label='Model', U_label='Analytic', 
                      plot_title='Cumulative DRT', return_ax=False):
        """
        Plot the cumulative sum of self.U or self.U_norm, optionally against a known analytical form.
        
        Parameters
        ----------
        normalised : bool (optional)
            Determines whether self.U (False) or self.U_norm (Ture) is plotted. Default (False)
        tau_analytic : {None, numpy.ndarray shape (l,)} (optional)
            Array of tau values use to generate the analytic curve, if known. This is mostly for 
            comparision if fitting to a known DRT for testing purposes. Default None.
        U_analytic : {None, numpy.ndarray shape (l,)} (optional)
            Array of U values used in the analytic curve, if known. This is mostly for 
            comparision if fitting to a known DRT for testing purposes. Default None.
        xaxis_label : str (optional)
            Label for the x axis of the output plot. '$\\tau$ [s]' by default.
        yaxis_label : str (optional)
            Label for the y axis of the output plot. 'Cumulative U' by default.
        U_model_label : str (optional)
            Label for the curve U_model in the output plot legend. 'Model' by default.
        U_label : str (optional)
            Label for the U_analytic curve in the output plot legend. 'Analytic' by default.
        plot_title : str (optional)
            Title of the output plot. 'Cumulative DRT' by default.
        return_ax : bool (optional)
            Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
            Default False.

        Returns
        -------
        ax : matplotlib.axes.Axes (optional)
            Returned axes object if return_ax is True.
        """

        U = self.U_norm if normalised else self.U 

        if yaxis_label == 'Auto':
            if normalised:
                yaxis_label = '$\\text{Cumulative} \\,\\, U_{\\text{norm}}$'
            else: 
                yaxis_label = '$\\text{Cumulative} \\,\\, U$'
        else: 
            yaxis_label = yaxis_label

        ax = plot_cumulative_U(self.tau, U, tau_analytic=tau_analytic, U_analytic=U_analytic, xaxis_label=xaxis_label, 
                          yaxis_label=yaxis_label, U_model_label=U_model_label, U_label=U_label, 
                          plot_title=plot_title, return_ax=return_ax)
        
        if isinstance(ax, Axes):
            return ax
    

    def plot_y_model(self, time, y_data=None, xaxis_label='Time [s]', yaxis_label='y(t)', 
           y_data_plot_label='Data', y_model_plot_label='Model', plot_title='DRT Fit', return_ax=False):
        """
        Plot the fitted model agains the data
        
        Parameters
        ----------
        time : numpy.ndarray, shape (n,)
            The time values over which the simulated experiment took place
        y_data : {None, numpy.ndarray shape (n,)} (optional)
            The data the model was fitted to. Either y_model or y must not be None. y is None by default.
        xaxis_label : str (optional)
            Label for the x axis of the output plot. 'Time [s]' by default.
        yaxis_label : str (optional)
            Label for the y axis of the output plot. 'y(t)' by default.
        y_data_plot_label : str (optional)
            Label for the curve y in the output plot legend. 'Data' by default.
        y_model_plot_label : str (optional)
            Label for the y_model curve in the output plot legend. 'Model' by default.
        plot_title : str (optional)
            Title of the output plot. 'DRT Fit' by default.
        return_ax : bool (optional)
            Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
            Default False.

        Returns
        -------
        ax : matplotlib.axes.Axes (optional)
            Returned axes object if return_ax is True.
        """
        ax = plot_y(time, self.y_model, y_data, xaxis_label, yaxis_label, y_data_plot_label, 
               y_model_plot_label, plot_title, return_ax)
        
        if isinstance(ax, Axes):
            return ax   


class FitError(Exception):
    """Custom fit error"""
    pass

######### Function Definitions ####################################################################


# Utility Functions #####################################


def predict_y_model(time, U, tau, y_inf=0):
    """Calculate the function 
        predict_y_model(t) = U_1*exp(-t/tau_1) + U_2*exp(-t/tau_2) + ... + U_m*exp(-t/tau_m) + y_inf
    
    Parameters
    ----------
    time : numpy.ndarray, shape (n,)
        The time values over which the simulated impedance-adjacent experiment takes place
    U : numpy.ndarray with shape (m,)
        Coefficients for the exponential decay functions such that U[i] is the coefficient of 
        exp(-t/tau[i])
    tau : numpy.ndarray with shape (m,)
        The relaxation times used in the model as above.
    y_inf : float (optional)
        The amplitude of the steady state signal in y_data i.e. y(infinity)
    
    Returns 
    -------
    y_model : numpy.ndarray with shape (n,)
        predict y_model at all time values in t
    """
    # Calculate predict_y_model(t) for all values in t
    y_model = (U @ np.exp(-np.outer(1/tau, time))) + y_inf

    return y_model


def calculate_tau(time):
    """
    Generate a range of tau values for DRT fitting based off an observation window
    over time values 'time'
    
    Parameters
    ----------
    time : arraylike, shape (n,)
        Time values data is observed over

    Returns
    -------
    tau_values : arraylike, shape (m,)
    """
    # Find the smallest time interval in the array
    d_time = [time[i+1] - time[i] for i in range(len(time)-1)]
    d_time_min = np.min(d_time)
    d_T = time[-1]-time[0]

    # Set max and min tau
    tau_min = d_time_min/np.pi
    tau_max = d_T/(2*np.pi)

    # If the number of points in the time array is less than 150,
    # set m = n, else set M = 150
    m = len(time) if len(time) < 150 else 150

    tau_values = np.geomspace(tau_min, tau_max, m)

    return tau_values


# Fitting Functions #####################################


def linear_fit(time, y_data, tau='Auto', y_inf='Auto', bounds=None, scaling=True):
    """
    Performs a linear fit of 
        y_model = U_1*exp(-t/tau_1) + U_2*exp(-t/tau_2)... + U_m*exp(-t/tau_m) + y_inf
    to the data (y_data)

    Converts the linear fit problem to a convex quadratic program and minimises using 
    the Operator Splitting Quadratic Program (OSQP) package solver [2]. Using a QP solver 
    was inspired by ADD REFERENCE
    
    Parameters
    ----------
    time : numpy.ndarray, shape (n,)
        Time values over which the simulated experiment took place
    y_data : numpy.ndarray, shape (n,)
        Data for model fitting
    tau: {'Auto', (tau_min, tau_max, m), array_like of shape (m,)} (optional)
        The tau values used in the model 
            y_model = U_1*exp(-t/tau_1) + U_2*exp(-t/tau_2)... + U_m*exp(-t/tau_m) + y_inf
        'Auto' will use the 'calculate_tau' method to determine lifetimes for fitting. 
        Passing a tuple in the form (tau_min, tau_max, m) will generate a logarithmic array of m values between 
        tau_min and tau_max. 
        Any passed array_like that isn't a tuple of length 3 will be used for all tau values. 
        Default 'Auto'.
    y_inf : REMOVE THIS
    bounds : {None, (lower, upper)} (optional)
        Sets the bounds for the fitted coeffs. U. Use np.inf for unbounded limit. Default None.
    scaling : bool (optional)
        Determines whether minmax scaling is applied to the data before fitting 
        (the data is scaled back post fit). Would recomend leaving at default value. 
        Default True.

    Results
    -------
    fit : DRT_Fit_Result
        Fit object containing fit data.
    """
    # Record y_inf from y=0
    y_inf = y_data[-1] if y_inf == 'Auto' else y_inf

    # Determine tau 
    if isinstance(tau, str): # Check if tau is set to 'Auto' by verifying it's a string
        tau = calculate_tau(time)
    elif isinstance(tau, tuple) and len(tau) == 3:
        tau = np.geomspace(tau[0], tau[1], tau[3])
    else:
        tau = tau

    # Step 0: Scale the signal and remove scaled y_inf
    scale_factor = 1
    if scaling:
        y_data_max = y_data.max()
        y_data_min = y_data.min()
        scale_factor = y_data_max-y_data_min
        y_data = (y_data - y_data_min)/scale_factor
        y_data = y_data - y_data[-1]
    
    # Step 1: Convert the DRT function form into the form Y = R@U
    m = len(tau)
    R = np.exp(-np.outer(1/tau, time)).T 
    
    # Step 2: Convert the least squares problem into a quadratic program
    P = 2*R.T@R 
    P = csc_matrix((1/2)*(P.T + P))
    q = -2*R.T@y_data
    
    # Step 3: Set the constraints matrices
    A = csc_matrix(np.identity(m))
    ones = np.ones((m, 1))
    l = bounds[0]*ones if bounds is not None else -np.inf*ones
    u = bounds[1]*ones if bounds is not None else np.inf*ones
    
    # Step 4: Solve 
    osqp_model = osqp.OSQP()
    osqp_model.setup(P, q, A, l, u, verbose=False)
    osqp_result = osqp_model.solve()
    
    # Step 5: Rescale results
    U = scale_factor*osqp_result.x
    y_model = R@U + y_inf
    y_data = y_data*scale_factor + y_inf

    # Step 6: Calculate errors
    MSE = mean_squared_error(y_data, y_model)
    R_2 = r2_score(y_data, y_model)

    # Step 7: Package results in DRT_Fit_result
    fit = DRT_Fit_Result(time, tau, U, y_inf, MSE=MSE, R_2=R_2)
    fit.y_model = y_model
    fit.set_U_norm()
    
    return fit


def checkerboard_fit(time, y_data, tau='Auto', y_inf='Auto', checkerboard_iters=50, fit_scaling=True):
    """
    Performs a 'checkerboard' DRT fit by iteratively fitting capacitive and inductive effects in supplied data (y)
    
    time : numpy.ndarray, shape (n,)
        Time values over which the simulated experiment took place
    y_data : numpy.ndarray, shape (n,)
        Data for model fitting
    tau: {'Auto', tuple(tau_min, tau_max, m), array_like of shape (m,)} (optional)
        The tau values used in the model 
            y_model = U_1*exp(-t/tau_1) + U_2*exp(-t/tau_2)... + U_m*exp(-t/tau_m) + y_inf
        'Auto' will use the 'calculate_tau' method to determine lifetimes for fitting. 
        Passing a tuple in the form (tau_min, tau_max, m) will generate a logarithmic array of m values between 
        tau_min and tau_max. 
        Any passed array_like that isn't a tuple of length 3 will be used for all tau values. 
        Default 'Auto'.
    y_inf:  {'Auto', float} (optional)
        Amplitude of steady state signal, assumed to be at y(infinity) when set to 'Auto'. (Default 'Auto')
    checkerboard_iters : int (optional)
        The number of iterations to perform using the checkerboard fitting method
    fit_scaling : bool
        Determines whether minmax scaling is used during each call of the 'linear_fit' method. 
        Can impact the smoothness of the MSE and R^2 over many iterations. Default True.

    Returns
    -------
    fits : arraylike(DRT_Fit_Results), shape (checkerboard_iters,)
        An array of fit objects corresponding to each iteration of the checkerboard procedure.
    """

    # Determine tau
    if isinstance(tau, str):
        tau = calculate_tau(time)
    elif isinstance(tau, tuple) and len(tau) == 3:
        tau = np.geomspace(tau[0], tau[1], tau[3])
    else:
        tau = tau

    # Validate input data 
    if len(time) != len(y_data):
        raise FitError("Invalid input: input time and input data (y_data) have mismatch lengths")
    
    if (isinstance(tau, str) and tau != 'Auto') or (isinstance(tau, tuple) and len(tau) != 3):
        raise FitError("Invalid input: 'tau' must be either 'Auto', a tuple of length 3, or an array-like of length n")
    
    if y_inf != 'Auto' and not isinstance(tau, float):
        raise FitError("Invalid input: 'y_inf' must be either 'Auto' or a float")
    
    # Step 1: Prep the signal for fitting by removing y_inf and scaling
    y_inf = y_data[-1] if y_inf == 'Auto' else y_inf
    y_data_max = y_data.max()
    y_data_min = y_data.min()
    scale_factor = y_data_max-y_data_min
    y_data_scaled = (y_data - y_data_min)/scale_factor
    y_data_scaled = y_data_scaled - y_data_scaled[-1]

    # Step 2: Set initial values
    U_values = np.zeros(len(tau))
    
    y_model_cap = y_data_scaled

    cap_U_values = np.zeros(len(tau))
    ind_U_values = np.zeros(len(tau))

    cap_y_inf = 0
    ind_y_inf = 0

    fits = []
    
    # NOTE: we probably want to set the y_inf and scale factor guesses ourselves
    for i in range(checkerboard_iters):
        
        # Set scale params for capacitive effects and fit
        cap_fit = linear_fit(time, y_model_cap, tau=tau, y_inf=cap_y_inf, scaling=fit_scaling, bounds=(0, np.inf))
        
        # Add the fit to U_values
        cap_U_values = cap_fit.U
        
        # Remove the capacitive effects from y
        y_model_ind = y_data_scaled - cap_fit.y_model
        ind_y_inf = y_model_ind[-1]
        
        # Set the inductive scale params and fit by doing a capacitive fit on an inverted function
        ind_fit = linear_fit(time, -y_model_ind, tau=tau, y_inf=ind_y_inf, scaling=fit_scaling, bounds=(0, np.inf))
        
        # Add the fit to U_values 
        ind_U_values = -ind_fit.U

        # Remove the inductive effects from the curve for the next iteration
        y_model_cap = y_data_scaled + ind_fit.y_model
        cap_y_inf = y_model_cap[-1]
        
        # Once the fit is done, return a fit object with the results and a dummy cost of 0
        U_values = cap_U_values + ind_U_values

        # Rescale and package results
        U_values = scale_factor*U_values
        y_model = predict_y_model(time, U_values, tau, y_inf=y_inf)
        MSE = mean_squared_error(y_data, y_model)
        R_2 = r2_score(y_data, y_model)

        fit = DRT_Fit_Result(time, tau, U_values, y_inf, MSE=MSE, R_2=R_2)
        fit.y_model = y_model
        fit.set_U_norm()
        fits.append(fit)
        
    return fits


######### Plotting Functions #######################################################################


def plot_y(time, y_model=None, y_data=None, xaxis_label='Time [s]', yaxis_label='y(t)', 
           y_data_plot_label='Data', y_model_plot_label='Model', plot_title='DRT Fit', return_ax=False):
    """
    Plot the fitted model agains the data
    
    Parameters
    ----------
    time : numpy.ndarray, shape (n,)
        The time values over which the simulated experiment took place
    y_model : {None, numpy.ndarray shape (n,)} (optional)
        The model predicted curve. Either y_model or y must not be None. y_model is None by default.
    y_data : {None, numpy.ndarray shape (n,)} (optional)
        The data the model was fitted to. Either y_model or y must not be None. y is None by default.
    xaxis_label : str (optional)
        Label for the x axis of the output plot. 'Time [s]' by default.
    yaxis_label : str (optional)
        Label for the y axis of the output plot. 'y(t)' by default.
    y_plot_label : str (optional)
        Label for the curve y in the output plot legend. 'Data' by default.
    y_model_plot_label : str (optional)
        Label for the y_model curve in the output plot legend. 'Model' by default.
    plot_title : str (optional)
        Title of the output plot. 'DRT Fit' by default.
    return_ax : bool (optional)
        Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
        Default False.

    Returns
    -------
    ax : matplotlib.axes.Axes (optional)
        Returned axes object if return_ax is True.
    """
    ax = plot_functions.plot_2x_2y(
        time, y_model, xaxis_label, yaxis_label, plot_title, 
        y1_plot_label=y_model_plot_label, y2=y_data, 
        y2_plot_label=y_data_plot_label,xscale="log", 
        order=("y2","y1"), legend=True
    )
    
    if return_ax:
        return ax 
    else:
        plt.show()


def plot_U(tau_model, U_model, tau_analytic=None, U_analytic=None, xaxis_label='$\\tau$ [s]', 
           yaxis_label='U', U_model_label='Model', U_label='Analytic', plot_title='DRT', return_ax=False):
    """
    Plot the fitted DRT against an optional analytic DRT
    
    Parameters
    ----------
    tau_model : numpy.ndarray, shape (m,)
        The tau values used in the model
    U_model : numpy.ndarray shape (m,)
        The coeffs from the DRT fit, given by U in 
            y_model = U_1*exp(-t/tau_1) + U_2*exp(-t/tau_2)... + U_m*exp(-t/tau_m) + y_inf
    tau_analytic : {None, numpy.ndarray shape (l,)} (optional)
        Array of tau values use to generate the analytic curve, if known. This is mostly for 
        comparision if fitting to a known DRT for testing purposes. Default None.
    U_analytic : {None, numpy.ndarray shape (l,)} (optional)
        Array of U values used in the analytic curve, if known. This is mostly for 
        comparision if fitting to a known DRT for testing purposes. Default None.
    xaxis_label : str (optional)
        Label for the x axis of the output plot. '$\\tau$ [s]' by default.
    yaxis_label : str (optional)
        Label for the y axis of the output plot. 'U' by default.
    U_model_label : str (optional)
        Label for the curve U_model in the output plot legend. 'Model' by default.
    U_label : str (optional)
        Label for the U_analytic curve in the output plot legend. 'Analytic' by default.
    plot_title : str (optional)
        Title of the output plot. 'DRT' by default.
    return_ax : bool (optional)
        Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
        Default False.

    Returns
    -------
    ax : matplotlib.axes.Axes (optional)
        Returned axes object if return_ax is True.
    """
    ax = plot_functions.plot_2x_2y(
        tau_model, U_model, xaxis_label, yaxis_label, plot_title, y1_plot_label=U_model_label,
        x2=tau_analytic, y2=U_analytic, y2_plot_label=U_label, xscale='log', order=("y2", "y1"), legend=True
    )

    # Return axis if called for, otherwise show the figure
    if return_ax:
        return ax 
    else: 
        plt.show()


def plot_cumulative_U(tau_model, U_model, tau_analytic=None, U_analytic=None, xaxis_label='$\\tau$ [s]', 
                      yaxis_label='Cumulative U', U_model_label='Model', U_label='Analytic', 
                      plot_title='Cumulative DRT', return_ax=False):
    """
    Plot the fitted DRT against an optional analytic DRT
    
    Parameters
    ----------
    tau_model : numpy.ndarray, shape (m,)
        The tau values used in the model
    U_model : numpy.ndarray shape (m,)
        The coeffs from the DRT fit, given by U in 
            y_model = U_1*exp(-t/tau_1) + U_2*exp(-t/tau_2)... + U_m*exp(-t/tau_m) + y_inf
    tau_analytic : {None, numpy.ndarray shape (l,)} (optional)
        Array of tau values use to generate the analytic curve, if known. This is mostly for 
        comparision if fitting to a known DRT for testing purposes. Default None.
    U_analytic : {None, numpy.ndarray shape (l,)} (optional)
        Array of U values used in the analytic curve, if known. This is mostly for 
        comparision if fitting to a known DRT for testing purposes. Default None.
    xaxis_label : str (optional)
        Label for the x axis of the output plot. '$\\tau$ [s]' by default.
    yaxis_label : str (optional)
        Label for the y axis of the output plot. 'Cumulative U' by default.
    U_model_label : str (optional)
        Label for the curve U_model in the output plot legend. 'Model' by default.
    U_label : str (optional)
        Label for the U_analytic curve in the output plot legend. 'Analytic' by default.
    plot_title : str (optional)
        Title of the output plot. 'Cumulative DRT' by default.
    return_ax : bool (optional)
        Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
        Default False.

    Returns
    -------
    ax : matplotlib.axes.Axes (optional)
        Returned axes object if return_ax is True.
    """

    # Calculate the cumulative U values
    cumulative_U_model = [np.sum(U_model[:i]) for i in range(len(U_model))]
    if tau_analytic is not None and U_analytic is not None:
        cumulative_U_analytic = [np.sum(U_analytic[:i]) for i in range(len(U_analytic))]
    else: 
        cumulative_U_analytic = None
    
    ax = plot_functions.plot_2x_2y(
        tau_model, cumulative_U_model, xaxis_label, yaxis_label, plot_title, U_model_label, 
        x2=tau_analytic, y2=cumulative_U_analytic, y2_plot_label=U_label, xscale='log', 
        order=("y2", "y1"), legend=True
    )

    # Return axis if called for, otherwise show the figure
    if return_ax:
        return ax 
    else: 
        plt.show()


def plot_MSE(error_array, xaxis_label='Iteration', yaxis_label='MSE', plot_title='MSE per Fit Iteration', 
             return_ax=False):
    """
    Plots the mean square error. Useful for checking how the MSE varies with iteration 
    during checkerboard fit.
    
    Parameters
    ----------
    error_array : {array_like(DRT_Fit_Result) of shape (i,), arraylike(float)}
        An iterable conatining EITHER DRT_Fit_Result objects from which the MSE values are taken 
        OR float values which are considered to be the MSE values
    xaxis_label : str (optional)
        Label for the x axis of the output plot. 'Iteration' by default.
    yaxis_label : str (optional)
        Label for the y axis of the ouput plot. 'MSE' by default.
    plot_title : str (optional)
        Title for the output plot. 'MSE per Fit Iteration' by default.
    return_ax : bool (optional)
        Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
        Default False.
        
    Returns
    -------
    ax : matplotlib.axes.Axes (optional)
        Returned axes object if return_ax is True.
    """
    
    if isinstance(error_array[0], DRT_Fit_Result):
        MSE_values = [fit.MSE for fit in error_array]
    else: 
        MSE_values = error_array

    ax = plot_functions.plot_2x_2y(
        range(1, len(MSE_values)+1), MSE_values, xaxis_label, yaxis_label, plot_title
    )

    if return_ax:
        return ax
    else:
        plt.show()


def plot_R_2(error_array, ylim=(0, 1.1), xaxis_label='Iteration', yaxis_label='$R^2$', plot_title='$R^2$ per fit Iteration', 
             return_ax=False):
    """
    Plots the R^2 error. Useful for checking how R^2 varies with iteration 
    during checkerboard fit.
    
    Parameters
    ----------
    fit_array : array_like(DRT_Fit_Result), shape (i,)
        An iterable conatining DRT_Fit_Result objects from which the R^2 values are taken
    ylim : tuple, (2,) (optional)
        Set the ylimits of the plot. ylim[0] gives the lower bound, y[1] the upper. Default (0, 1.1)
    xaxis_label : str (optional)
        Label for the x axis of the output plot. 'Iteration' by default.
    yaxis_label : str (optional)
        Label for the y axis of the ouput plot. '$R^2$' by default.
    plot_title : str (optional)
        Title for the output plot. '$R^2$ per fit Iteration'.
    return_ax : bool (optional)
        Determines whether the matplotlib.axes.Axes object is returned (True) or plotted (False). 
        Default False.
        
    Returns
    -------
    ax : matplotlib.axes.Axes (optional)
        Returned axes object if return_ax is True.
    """
    
    if isinstance(error_array[0], DRT_Fit_Result):
        R_2_values = [fit.R_2 for fit in error_array]
    else:
        R_2_values = error_array

    ax = plot_functions.plot_2x_2y(
        range(1, len(R_2_values)+1), R_2_values, xaxis_label, yaxis_label, plot_title, ylim=ylim
    )
    if return_ax:
        return ax
    else:
        plt.show()


######### Data Saving and Reading ####################################################################


def save_models_to_txt(path, fits, float_format='%.5e'):
    """
    Save the tau and U values from a collection of DRT_Fit_Result objects to a txt file.

    Parameters
    ----------
    path : str
        File path of save file
    fits : arraylike(DRT_Fit_Result)
        Array like object of fit results 
    float_format: str (optional)
        Controls how float values are save to file

    Returns
    -------
    None
    """
    tau = fits[0].tau # All iterations in a checkerboard fit will have the same tau
    y_inf = fits[0].y_inf # All iterations in a checkerboard fit will have the same y_inf
    DRT_data = {'tau' : tau}
    for i in range(len(fits)):
        DRT_data[f'U_iter_{i+1}'] = fits[i].U
    DRT_data = pd.DataFrame(DRT_data)
    pd.DataFrame(DRT_data).to_csv(path, sep=' ', float_format=float_format, index=False, )


def save_model_predictions_to_txt(path, fits, float_format='%.5e'):
    """
    Save the y_model values from a collection of DRT_Fit_Result objects to a txt file.

    Parameters
    ----------
    path : str
        File path of save file
    fits : arraylike(DRT_Fit_Result)
        Array like object of fit results 
    time : numpy.ndarray
        Time values over which each fit was made
    float_format: str (optional)
        Controls how float values are save to file

    Returns
    -------
    None
    """
    model_predictions = {'t' : fits[0].time} ###FIX THIS 
    for i in range(len(fits)):
        model_predictions[f'y_model_iter_{i+1}'] = fits[i].y_model
    model_predictions = pd.DataFrame(model_predictions)
    model_predictions.to_csv(path, sep=' ', float_format=float_format, index=False)


def save_model_errors_to_txt(path, fits, float_format='%.5e'):
    """
    Save the MSE and R_2 values from a collection of DRT_Fit_Result objects to a txt file.

    Parameters
    ----------
    path : str
        File path of save file
    fits : arraylike(DRT_Fit_Result)
        Array like object of fit results 
    float_format: str (optional)
        Controls how float values are save to file

    Returns
    -------
    None
    """
    MSE = [fit.MSE for fit in fits]
    R_2 = [fit.R_2 for fit in fits]
    model_errors = pd.DataFrame({'MSE' : MSE, "R_2" : R_2})
    model_errors.to_csv(path, sep=' ', float_format=float_format, index=False)


def save_to_txt(directory_path, fits, float_format='%.5e'):
    """
    Save tau, U, y, MSE, and R_2 values from a collection of fit objects to text files.

    Parameters
    ----------
    directory_path : str
        All save files are saved to this directory
    fits : arraylike(DRT_Fit_Result)
        Array like object of fit results 
    time : numpy.ndarray
        Time values over which each fit was made
    float_format: str (optional)
        Controls how float values are save to file

    Returns
    -------
    None
    """
    # Check the directory exists and make it if not
    try: 
        os.makedirs(directory_path)
    except FileExistsError:
        pass
    
    # Define file names
    models_filename = os.path.join(directory_path, "DRTModels.txt")
    model_predictions_filename = os.path.join(directory_path, "modelOutputs.txt")
    output_errors_filename = os.path.join(directory_path, "outputErrors.txt")
    
    # Save data
    save_models_to_txt(models_filename, fits, float_format=float_format)
    save_model_predictions_to_txt(model_predictions_filename, fits, float_format=float_format)
    save_model_errors_to_txt(output_errors_filename, fits, float_format=float_format)


######### Scripting Functionality ####################################################################

def parse_arguments(argv=None):
    """ Parses command line arguments into an ArgumentParser object
    
    Parameters 
    ----------
    argv : {[str] or Dict[str, str]} (optional)
        List or dictrionary of strings containing command line args and flags. If list, must be in the
        format [dataFile_path, '-flag1', argument1, '-flag2', argument2, ...]. If dict,
        must be in the format {'dataFile' : dataFile_path, 'flag1' : argument1, ...}
        If none, parses sys.argv[1:] instead.
        
    Returns
    -------
    args : argparse.ArgumentParser

    Example
    -------
    # Parses sys.argv[1:]
    args1 = parse_arguments()

    # Parses a list 
    args2 = parse_arguments(['dataFile.txt', '-timeCol', 'time', '-iters', '20'])

    # Parses a dictionary
    args3 = parse_arguments(['dataFile' : 'dataFile.txt', 'timeCol' : 'time', 'iters' : '20'])
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("dataFile", 
                        help="path to data file containing time and function values for fit")
    parser.add_argument("-DRTDirectory", default='DRT_Saves', 
                        help="path to directory for DRT save files (default: DRT_Saves)")
    parser.add_argument("-timeCol", default= 't', 
                        help="heading of the time column in dataFile (default: 't')")
    parser.add_argument("-funcCol", default = 'Jext', 
                        help="heading of the function column in dataFile (default: 'Jext')")
    parser.add_argument("-iters", type=int, default=50, 
                        help="number of iterations in checkerboard fit (default: 50)")
    parser.add_argument("-saveFormat", default="txt", choices=["txt", "pkl"],
                        help="saved data file format (default: txt)")
    parser.add_argument("-UUID", default="", 
                        help="Identifier tag added to save directory name i.e. DRTDirectory -> DRTDirectory_UUID ")
    
    # Add mutually exclusive group for slicing passed data 
    slice_group = parser.add_mutually_exclusive_group()
    slice_group.add_argument("-startIndex", type=int, help="Slices data from given index")
    slice_group.add_argument("-startTime", type=float, help="Slices data from given time")
    
    # IF argv is a dictionary, parse it into a list
    if isinstance(argv, dict):
        commands_and_args = []
        commands_and_args.append(argv['dataFile'])
        argv.pop('dataFile')

        for key, value in argv.items():
            key = "-" + key
            commands_and_args.append(key)
            commands_and_args.append(value)
        
        argv = commands_and_args
    
    if isinstance(argv, list):
        args = parser.parse_args(args=argv)
    elif argv is None:
        args = parser.parse_args(args=argv) 
    else:
        raise ValueError("argv must be of type None, list[str], or Dict[str, str]")

    return args

def main(argv=None):
    """ Script entry point for running a checkerboard fit. 
    
    Parameters
    ----------
    argv : [str] (optional)
        List of strings containing command line args and flags. Default None
    
    Returns
    -------
    EXIT_CODE : int
        0 on a success
        1 on a failure 
        2 on a failure due to a usage error
    """
    # Define exit codes 
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1
    EXIT_USAGE_ERROR = 2

    # Parse command line arguments
    args = parse_arguments(argv)

    # Read data
    try:
        dataFile = pd.read_csv(args.dataFile, sep=r"\s+")
    except FileNotFoundError:
        print(f"Error: dataFile not found. Check file path.")
        return EXIT_USAGE_ERROR
  
    try: 
        time = np.array(dataFile[args.timeCol])
    except KeyError:
        print(f"Error: column '{args.timeCol}' not found in '{args.dataFile}'")
        return EXIT_USAGE_ERROR

    try: 
        y_data = np.array(dataFile[args.funcCol])
    except KeyError:
        print(f"Error: column '{args.funcCol}' not found in '{args.dataFile}'")
        return EXIT_USAGE_ERROR
    
    # Set data slice if start index or start time is passed
    try:
        if args.startIndex is not None:
            time = time[args.startIndex:]
            y_data = y_data[args.startIndex:]

        if args.startTime is not None:
            filter = np.where(time >= args.startTime)
            time = time[filter]
            y_data = y_data[filter]

        # Check to make sure the slice hasn't removed all values from the array 
        if len(time) == 0:
            raise ValueError
        
    except ValueError as e:
        print(f"Error: no read data. Check dataFile is not empty, and make sure -startIndex/-startTime is in the data range if used")
        return EXIT_USAGE_ERROR

    # Update the passed directory name with the UUID if it exists
    DRT_directory = args.DRTDirectory + "_" + args.UUID if args.UUID != "" else args.DRTDirectory

    # Check whether DRTDirectory exists and, if not, create it
    try: 
        os.makedirs(DRT_directory)

    except FileExistsError:
        pass

    except PermissionError:
        print(f"Error: DRT.py lacks the neccessary permissions to create {DRT_directory}. Try manually creating {args.DRTDirectory} instead.")
        return EXIT_USAGE_ERROR
    
    except Exception as error:
        print(f"Unexpected File Saving Error: {error}")
        return EXIT_FAILURE
    
    # Run checkerboard fit 
    try:
        fits = checkerboard_fit(time, y_data, tau='Auto', y_inf='Auto', checkerboard_iters=args.iters)
        # Save DRT data to file
        if args.saveFormat == "txt":
            save_to_txt(DRT_directory, fits)
        elif args.saveFormat == "pkl":
            save_to_pickle(DRT_directory + "/models.pkl", fits)
        return EXIT_SUCCESS

    except Exception as error:
        print(f"Unexpected error: {error}")
        print(traceback.print_exc())
        return EXIT_FAILURE


if __name__ == '__main__':
    sys.exit(main())