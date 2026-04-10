"""Useful helper functions for pySIMsalabim"""
######### Package Imports #########################################################################

import numpy as np
from scipy import stats,constants

## Physics constants
q = constants.value(u'elementary charge')
eps_0 = constants.value(u'electric constant')
kb = constants.value(u'Boltzmann constant in eV/K')

######### Function Definitions ####################################################################
def get_Jsc(Volt,Curr):
    """Get the short-circuit current (Jsc) from solar cell JV-curve by interpolating the current at 0 V

    Parameters
    ----------
    Volt : 1-D sequence of floats
        Array containing the voltages.

    Curr : 1-D sequence of floats
        Array containing the current-densities.

    Returns
    -------
    Jsc : float
        Short-circuit current value
    """
    Jsc_dumb = np.interp(0, Volt, Curr)
    return Jsc_dumb

def get_Voc(Volt,Curr):
    """Get the Open-circuit voltage (Voc) from solar cell JV-curve by interpolating the Voltage when the current is 0

    Parameters
    ----------
    Volt : 1-D sequence of floats
        Array containing the voltages.

    Curr : 1-D sequence of floats
        Array containing the current-densities.

    Returns
    -------
    Voc : float
        Open-circuit voltage value
    """
    Voc_dumb = np.interp(0, Curr, Volt)
    return Voc_dumb

def get_FF(Volt,Curr):
    """Get the fill factor (FF) from solar cell JV-curve by calculating the maximum power point

    Parameters
    ----------
    Volt : 1-D sequence of floats
        Array containing the voltages.

    Curr : 1-D sequence of floats
        Array containing the current-densities.

    Returns
    -------
    FF : float
        Fill factor value
    """
    power = []
    Volt_oc = get_Voc(Volt,Curr)
    Curr_sc = get_Jsc(Volt,Curr)
    for i,j in zip(Volt,Curr):
        if (i < Volt_oc and j > Curr_sc):
            power.append(i*j)
    power_max = min(power)
    FF_dumb = power_max/(Volt_oc*Curr_sc)
    return abs(FF_dumb)

def get_PCE(Volt,Curr,suns=1):
    """Get the power conversion efficiency (PCE) from solar cell JV-curve

    Parameters
    ----------
    Volt : 1-D sequence of floats
        Array containing the voltages.

    Curr : 1-D sequence of floats
        Array containing the current-densities.

    Returns
    -------
    PCE : float
        Power conversion efficiency value.
    """
    Voc_dumb = get_Voc(Volt,Curr)
    Jsc_dumb = get_Jsc(Volt, Curr)
    FF_dumb = get_FF(Volt, Curr)
    PCE_dumb = Voc_dumb*Jsc_dumb*FF_dumb/(10*suns) # to get it in % when Jsc is in A/m2 and Voc in V
    return abs(PCE_dumb)

def get_ideality_factor(suns,Vocs,T=295):
    """Returns ideality factor from suns-Voc data linear fit of Voc = (nIF/Vt)*log(suns) + intercept

    Parameters
    ----------
    suns : 1-D sequence of floats
        Array containing the intensity in sun.

    Vocs : 1-D sequence of floats
        Array containing the open-circuit voltages.
    
    T : float optional
        Temperature in Kelvin (Default = 295 K).

    Returns
    -------
    nIF : float
        Ideality factor value.

    intercept : float
        Intercept of the regression line.

    rvalue : float
        Correlation coefficient.

    pvalue : float
        Two-sided p-value for a hypothesis test whose null hypothesis is
        that the slope is zero, using Wald Test with t-distribution of
        the test statistic.

    stderr : float
        Standard error of the estimated gradient.
    """
    Vt = kb*T
    suns = np.log(suns)
    slope_d, intercept_d, r_value_d, p_value_d, std_err_d = stats.linregress(suns,Vocs)
    nIF = slope_d/Vt
    return nIF,intercept_d, r_value_d**2, p_value_d, std_err_d

# SIMsalabim inspired functions
def Fit_Parabola(x1, x2, x3, y1, y2, y3):   
    """Fits a parabola through [(x1, y1), (x2, y2), (x3,y3)], y = ax^2 + bx + c

    Parameters
    ----------
    x1, x2, x3 : float
        X-coordinates of the three points.
    y1, y2, y3 : float
        Y-coordinates of the three points.

    Returns
    -------
    a : float
        Quadratic coefficient.
    b : float
        Linear coefficient.
    c : float
        Constant term.
    """


    b = ((x3**2 - x1**2) * (y2 - y1)
         - (x2**2 - x1**2) * (y3 - y1)) / (
            (x2 - x1) * (x3**2 - x1**2)
            - (x3 - x1) * (x2**2 - x1**2)
        )

    a = (y3 - y1 - b * (x3 - x1)) / (x3**2 - x1**2)

    c = y1 - a * x1**2 - b * x1

    return a, b, c

def Locate(x, x0, imin, imax):
    """ Simple, slow, (hopefully) robust routine to an index within 
	row x (from imin to imax). x0 is some target we're looking for.
	The resulting index is such that x0 sits between x[i] and x[i+1]
	if x0 is outside the interval determined by x[imin], x[imax] then it 
	returns imin-1 or imax+1.

    Parameters
    ----------
    x : 1D numpy array
        Array of x values (ascending or descending).
    x0 : float
        Target value to locate within x.
    imin : int
        Minimum index to consider.
    imax : int
        Maximum index to consider.
    Returns
    -------
    int
        Index i such that x0 sits between x[i] and x[i+1], or imin-1 or imax+1 if x0 is outside the interval.      
    """
    # check if x is descending or ascending:
    r = np.sign(x[imax] - x[imin])  # so r=1 if ascending, r=-1 if descending
    if r == 0:
        raise ValueError("Error in locate: x array is constant?")

    i = imin # first init i!
    # Check if x0 sits beyond the interval, either left or right:
    if r * (x0 - x[imax]) > 0:
        return imax + 1
    if r * (x0 - x[imin]) < 0:
        return imin - 1
    if np.isclose(x0, x[imax]):
        return imax

    # Search inside interval
    if i == imin:
        while not (r * (x[i] - x0) <= 0 and r * (x[i + 1] - x0) > 0):
            i += 1
    
    return i


def Neville(x0, x, y, n=None):
    """Neville interpolation. 

    Parameters
    ----------
    x0 : float
        x0: x of desired point
    x : 1D numpy array
        Array of x values (ascending or descending).
    y : 1D numpy array
        Array of y values corresponding to x.
    n : int, optional
        Number of points to use (Defaults to len(x)).
    Returns
    -------
    float
        Interpolated y value at x0.
    float
        Estimated error of the interpolation.
    """    
    x = np.asarray(x)
    y = np.asarray(y)

    if len(x) != len(y):
        raise ValueError("x and y must have the same length.")

    if n is None:
        n = len(x)
    elif n > len(x):
        raise ValueError("n cannot exceed length of x and y.")

    # Use only first n points
    x = x[:n]
    Q = y[:n].copy()

    # Ensure x values are distinct
    if len(np.unique(x)) != n:
        raise ValueError("x values must be distinct.")

    # Neville triangular scheme
    for m in range(1, n):
        for i in range(n - m):
            Q[i] = ((x0 - x[i + m]) * Q[i] +
                    (x[i] - x0) * Q[i + 1]) / (x[i] - x[i + m])

        # The last correction term gives error estimate
        if m == n - 1:
            err_estimate = Q[1] - Q[0]

    return Q[0], abs(err_estimate) if n > 1 else 0.0


def InterExtraPolation(x, y, x0, order, extra_index=0):
    """Interpolation / extrapolation routine. This is a wrapper for Neville's algorithm.

    Parameters
    ----------
    x : 1D numpy array
        Array of x values (ascending or descending).
    y : 1D numpy array
        Array of y values corresponding to x.
    x0 : float
        Target value to interpolate or extrapolate.
    order : int
        Order of the interpolation polynomial.
    extra_index : int, optional
        Extrapolation control:  

            0 -> no extrapolation allowed  
            1 -> limited extrapolation  
            2 -> full extrapolation  

        ,by default 0

    Returns
    -------
    tuple
        success (bool), y_estimate (float), err_estimate (float)

    Raises
    ------
    ValueError
        If the interpolation order is invalid.
 
    """    


    x = np.asarray(x)
    y = np.asarray(y)

    N = len(x) - 1  # max index
    
    if order >= N:
        return False, 0.0, 0.0
        # raise ValueError("Not enough points for interpolation order.")
    if order < 1:
        return False, 0.0, 0.0
        # raise ValueError("Order must be at least 1.")

    y_estimate = 0.0
    err_estimate = 0.0

    # check bracketing
    x0_bracketed = (x[0] - x0) * (x[N] - x0) <= 0

    if not (extra_index > 0 or x0_bracketed):
        return False, y_estimate, err_estimate

    # locate index
    try:
        i1 = Locate(x, x0, 0, N)
    except ValueError:
        return False, y_estimate, err_estimate

    # map back to valid interval
    i1 = max(0, min(N, i1))

    # choose stencil
    istart = max(int(np.floor(i1 - 0.5 * order)), 0)
    ifin = order + istart

    if ifin > N:
        ifin = N-1
        istart = ifin - order

    # select points
    x_selected = x[istart:ifin+1]
    y_selected = y[istart:ifin+1]

    # Neville interpolation
    try:
        y_estimate, err_estimate = Neville(x0, x_selected, y_selected, n=order + 1)
    except ValueError:
        return False, y_estimate, err_estimate

    # extrapolation control
    delx = min(abs(x_selected[0] - x0),
               abs(x_selected[-1] - x0))

    avg_spacing = abs(x_selected[0] - x_selected[-1]) / order

    success = (
        extra_index == 2 or
        x0_bracketed or
        delx <= avg_spacing
    )

    return success, y_estimate, err_estimate


def Find_Solar_Cell_Parameters(Volt, Curr, max_interpolation_order=3, threshold_err=0.05):
    """Finds Jsc, Voc, MPP (and thus FF) by interpolating the V-J data points

    Parameters
    ----------
    Volt : 1D numpy array
        Array of voltage values.
    Curr : 1D numpy array
        Array of current values corresponding to Volt.
    max_interpolation_order : int, optional
        Maximum order of the interpolation polynomial, by default 3
    threshold_err : float, optional
        Maximum allowable error for interpolation, by default 0.05

    Returns
    -------
    dict
        Dictionary containing the extracted solar cell parameters.
    """    

    Volt = np.asarray(Volt)
    Curr = np.asarray(Curr)

    # ---- initialize output structure ----
    SCPar = dict(
        Jsc=0.0,
        Vmpp=0.0,
        MPP=0.0,
        FF=0.0,
        Voc=0.0,
        ErrJsc=0.0,
        ErrVmpp=0.0,
        ErrMPP=0.0,
        ErrFF=0.0,
        ErrVoc=0.0,
        calcSC=False,
        calcMPP=False,
        calcFF=False,
        calcOC=False,
    )

    x_dat = Volt
    y_dat = Curr
    Nusable = len(x_dat)

    if Nusable < 2:
        return SCPar

    interpolation_order = min(max_interpolation_order, Nusable - 1)

    # ======================================
    # 1 Short-circuit current (Jsc at V=0)
    # ======================================
    success, val, err = InterExtraPolation(
        x_dat, y_dat, 0.0, interpolation_order, extra_index=2
    )

    SCPar["Jsc"] = val
    SCPar["ErrJsc"] = err
    SCPar["calcSC"] = success and (err < threshold_err * abs(val))

    # ======================================
    # 2 Open-circuit voltage (Voc at J=0)
    # ======================================
    success, val, err = InterExtraPolation(
        y_dat, x_dat, 0.0, interpolation_order, extra_index=0
    )

    SCPar["Voc"] = val
    SCPar["ErrVoc"] = err
    SCPar["calcOC"] = success and (err < threshold_err * abs(val))

    # fallback to linear interpolation if needed
    if not SCPar["calcOC"] and interpolation_order > 1:
        success, val, err = InterExtraPolation(
            y_dat, x_dat, 0.0, 1, extra_index=1
        )
        SCPar["Voc"] = val
        SCPar["ErrVoc"] = err
        SCPar["calcOC"] = success and (err < threshold_err * abs(val))

    # ======================================
    # 3 Maximum Power Point (MPP)
    # ======================================
    power = -x_dat * y_dat  # standard PV sign convention

    i_start = np.argmax(power)

    SCPar["calcMPP"] = False
    SCPar["calcFF"] = False

    # Need at least one point on each side
    if 1 <= i_start <= Nusable - 2:

        # Fit parabola around maximum
        x1 = x_dat[i_start - 1]
        x2 = x_dat[i_start]
        x3 = x_dat[i_start + 1]

        y1 = power[i_start - 1]
        y2 = power[i_start]
        y3 = power[i_start + 1]

        a, b, c = Fit_Parabola(x1, x2, x3, y1, y2, y3)

        # Vmpp (extremum of parabola)
        Vmpp = -b / (2 * a)
        SCPar["Vmpp"] = Vmpp
        SCPar["ErrVmpp"] = 0.25 * abs(x3 - x1)

        # MPP value
        MPP = a * Vmpp**2 + b * Vmpp + c
        SCPar["MPP"] = MPP
        SCPar["ErrMPP"] = 0.25 * (
            abs(power[i_start + 1] - power[i_start]) +
            abs(power[i_start] - power[i_start - 1])
        )

        SCPar["calcMPP"] = True


        if (
            SCPar["calcOC"]
            and SCPar["calcSC"]
            and SCPar["Voc"] != 0
            and SCPar["Jsc"] != 0
        ):
            FF = -MPP / (SCPar["Voc"] * SCPar["Jsc"])
            SCPar["FF"] = FF

            SCPar["calcFF"] = (0 < FF < 1)

            # Error propagation
            SCPar["ErrFF"] = np.sqrt(
                (SCPar["ErrMPP"] / (SCPar["Jsc"] * SCPar["Voc"])) ** 2
                + (SCPar["ErrJsc"] * FF / SCPar["Jsc"]) ** 2
                + (SCPar["ErrVoc"] * FF / SCPar["Voc"]) ** 2
            )

    return SCPar



def get_Voc_SIMsalabim(Volt, Curr, max_interpolation_order=3, threshold_err=0.05):
    """SIMsalabim-style Voc extraction (standalone).

    Parameters
    ----------
    Volt : 1D numpy array
        Array of voltage values.
    Curr : 1D numpy array
        Array of current values corresponding to Volt.
    max_interpolation_order : int, optional
        Maximum order of the interpolation polynomial, by default 3
    threshold_err : float, optional
        Maximum allowable error for interpolation, by default 0.05

    Returns
    -------
    float
        Extracted open-circuit voltage (Voc) value.
    """    

    Volt = np.asarray(Volt)
    Curr = np.asarray(Curr)

    x_dat = Volt
    y_dat = Curr
    Nusable = len(x_dat)

    if Nusable < 2:
        return 0.0

    interpolation_order = min(max_interpolation_order, Nusable - 1)

    success, val, err = InterExtraPolation(
        y_dat, x_dat, 0.0, interpolation_order, extra_index=0
    )

    Voc = val
    calcOC = success and (err < threshold_err * abs(val))

    if not calcOC and interpolation_order > 1:
        success, val, err = InterExtraPolation(
            y_dat, x_dat, 0.0, 1, extra_index=1
        )
        Voc = val
        calcOC = success and (err < threshold_err * abs(val))

    return Voc if calcOC else Voc


def get_Jsc_SIMsalabim(Volt, Curr, max_interpolation_order=3, threshold_err=0.05):
    """SIMsalabim-style Jsc extraction (standalone).

    Parameters
    ----------
    Volt : 1D numpy array
        Array of voltage values.
    Curr : 1D numpy array
        Array of current values corresponding to Volt.
    max_interpolation_order : int, optional
        Maximum order of the interpolation polynomial, by default 3
    threshold_err : float, optional
        Maximum allowable error for interpolation, by default 0.05

    Returns
    -------
    float
        Extracted short-circuit current (Jsc) value.
    """    
     
    Volt = np.asarray(Volt)
    Curr = np.asarray(Curr)

    x_dat = Volt
    y_dat = Curr
    Nusable = len(x_dat)

    if Nusable < 2:
        return 0.0

    interpolation_order = min(max_interpolation_order, Nusable - 1)

    success, val, err = InterExtraPolation(
        x_dat, y_dat, 0.0, interpolation_order, extra_index=2
    )

    Jsc = val
    calcSC = success and (err < threshold_err * abs(val))

    return Jsc if calcSC else Jsc


def get_Vmpp_SIMsalabim(Volt, Curr):
    """SIMsalabim-style Vmpp extraction (standalone).

    Parameters
    ----------
    Volt : 1D numpy array
        Array of voltage values.
    Curr : 1D numpy array
        Array of current values corresponding to Volt.

    Returns
    -------
    float
        Extracted voltage at maximum power point (Vmpp) value.
    """    
      
    Volt = np.asarray(Volt)
    Curr = np.asarray(Curr)

    x_dat = Volt
    y_dat = Curr
    Nusable = len(x_dat)

    if Nusable < 3:
        return 0.0

    power = -x_dat * y_dat
    i_start = np.argmax(power)

    if not (1 <= i_start <= Nusable - 2):
        return 0.0

    x1 = x_dat[i_start - 1]
    x2 = x_dat[i_start]
    x3 = x_dat[i_start + 1]

    y1 = power[i_start - 1]
    y2 = power[i_start]
    y3 = power[i_start + 1]

    a, b, c = Fit_Parabola(x1, x2, x3, y1, y2, y3)
    Vmpp = -b / (2 * a)

    return Vmpp


def get_mpp_SIMsalabim(Volt, Curr):
    """SIMsalabim-style MPP extraction (standalone).

    Parameters
    ----------
    Volt : 1D numpy array
        Array of voltage values.
    Curr : 1D numpy array
        Array of current values corresponding to Volt.

    Returns
    -------
    float
        Extracted maximum power point (MPP) value.
    """    
       
    Volt = np.asarray(Volt)
    Curr = np.asarray(Curr)

    x_dat = Volt
    y_dat = Curr
    Nusable = len(x_dat)

    if Nusable < 3:
        return 0.0

    power = -x_dat * y_dat
    i_start = np.argmax(power)

    if not (1 <= i_start <= Nusable - 2):
        return 0.0

    x1 = x_dat[i_start - 1]
    x2 = x_dat[i_start]
    x3 = x_dat[i_start + 1]

    y1 = power[i_start - 1]
    y2 = power[i_start]
    y3 = power[i_start + 1]

    a, b, c = Fit_Parabola(x1, x2, x3, y1, y2, y3)
    Vmpp = -b / (2 * a)
    MPP = a * Vmpp**2 + b * Vmpp + c

    return MPP


def get_FF_SIMsalabim(Volt, Curr, max_interpolation_order=3, threshold_err=0.05):
    """SIMsalabim-style FF extraction (standalone).

    Parameters
    ----------
    Volt : 1D numpy array
        Array of voltage values.
    Curr : 1D numpy array
        Array of current values corresponding to Volt.
    max_interpolation_order : int, optional
        Maximum order of the interpolation polynomial, by default 3
    threshold_err : float, optional
        Maximum allowable error for interpolation, by default 0.05

    Returns
    -------
    float
        Extracted fill factor (FF) value.
    """    
 
    Volt = np.asarray(Volt)
    Curr = np.asarray(Curr)

    x_dat = Volt
    y_dat = Curr
    Nusable = len(x_dat)

    if Nusable < 3:
        return 0.0

    interpolation_order = min(max_interpolation_order, Nusable - 1)

    # Jsc
    success, val, err = InterExtraPolation(
        x_dat, y_dat, 0.0, interpolation_order, extra_index=2
    )
    Jsc = val
    calcSC = success and (err < threshold_err * abs(val))

    # Voc
    success, val, err = InterExtraPolation(
        y_dat, x_dat, 0.0, interpolation_order, extra_index=0
    )
    Voc = val
    calcOC = success and (err < threshold_err * abs(val))

    if not calcOC and interpolation_order > 1:
        success, val, err = InterExtraPolation(
            y_dat, x_dat, 0.0, 1, extra_index=1
        )
        Voc = val
        calcOC = success and (err < threshold_err * abs(val))

    # MPP
    power = -x_dat * y_dat
    i_start = np.argmax(power)

    if not (1 <= i_start <= Nusable - 2):
        return 0.0

    x1 = x_dat[i_start - 1]
    x2 = x_dat[i_start]
    x3 = x_dat[i_start + 1]

    y1 = power[i_start - 1]
    y2 = power[i_start]
    y3 = power[i_start + 1]

    a, b, c = Fit_Parabola(x1, x2, x3, y1, y2, y3)
    Vmpp = -b / (2 * a)
    MPP = a * Vmpp**2 + b * Vmpp + c

    if not (calcOC and calcSC and Voc != 0 and Jsc != 0):
        return 0.0

    FF = -MPP / (Voc * Jsc)
    return FF


def get_PCE_SIMsalabim(Volt, Curr, suns=1, max_interpolation_order=3, threshold_err=0.05):
    """SIMsalabim-style PCE extraction (standalone).

    Parameters
    ----------
    Volt : 1D numpy array
        Array of voltage values.
    Curr : 1D numpy array
        Array of current values corresponding to Volt.
    suns : int, optional
        Number of suns for illumination, by default 1
    max_interpolation_order : int, optional
        Maximum order of the interpolation polynomial, by default 3
    threshold_err : float, optional
        Maximum allowable error for interpolation, by default 0.05

    Returns
    -------
    float
        Extracted power conversion efficiency (PCE) value.
    """    

    Volt = np.asarray(Volt)
    Curr = np.asarray(Curr)

    x_dat = Volt
    y_dat = Curr
    Nusable = len(x_dat)

    if Nusable < 3:
        return 0.0

    interpolation_order = min(max_interpolation_order, Nusable - 1)

    # Jsc
    success, val, err = InterExtraPolation(
        x_dat, y_dat, 0.0, interpolation_order, extra_index=2
    )
    Jsc = val
    calcSC = success and (err < threshold_err * abs(val))

    # Voc
    success, val, err = InterExtraPolation(
        y_dat, x_dat, 0.0, interpolation_order, extra_index=0
    )
    Voc = val
    calcOC = success and (err < threshold_err * abs(val))

    if not calcOC and interpolation_order > 1:
        success, val, err = InterExtraPolation(
            y_dat, x_dat, 0.0, 1, extra_index=1
        )
        Voc = val
        calcOC = success and (err < threshold_err * abs(val))

    # MPP
    power = -x_dat * y_dat
    i_start = np.argmax(power)

    if not (1 <= i_start <= Nusable - 2):
        return 0.0

    x1 = x_dat[i_start - 1]
    x2 = x_dat[i_start]
    x3 = x_dat[i_start + 1]

    y1 = power[i_start - 1]
    y2 = power[i_start]
    y3 = power[i_start + 1]

    a, b, c = Fit_Parabola(x1, x2, x3, y1, y2, y3)
    Vmpp = -b / (2 * a)
    MPP = a * Vmpp**2 + b * Vmpp + c

    if not (calcOC and calcSC and Voc != 0 and Jsc != 0):
        return 0.0

    FF = -MPP / (Voc * Jsc)
    PCE = abs(Voc * Jsc * FF / (10 * suns)) # to get it in % when Jsc is in A/m2 and Voc in V

    return PCE

