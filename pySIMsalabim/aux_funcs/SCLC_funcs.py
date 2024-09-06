###################################################
############### Useful function ###################
###################################################
# by Vincent M. Le Corre
# Package import
import subprocess,shutil,os,glob,sys,warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats,optimize,constants
from lmfit import Model
# Don't show warnings
warnings.filterwarnings("ignore")
## Physics constants
q = constants.value(u'elementary charge')
eps_0 = constants.value(u'electric constant')
kb = constants.value(u'Boltzmann constant in eV/K')
k = constants.value(u'Boltzmann constant')
#############################################################
################ SCLC analysis functions ####################
#############################################################

def MottGurney(V,mu,eps_r,Vbi,L):
    """Mott-Gurney equation typically used to fit single carrier devices JVs to get the mobility.

    J = (9/8)*eps_0*eps_r*mu*((V-Vbi)**2)/(L**3)

    Refs:
    Mott N F and Gurney R W 1940 Electronic Processes in Ionic Crystals (Oxford: Oxford University Press)
    Nice paper to read on MG ==> J. Phys.: Condens. Matter 30 (2018) 105901

    Parameters
    ----------
    V : 1-D sequence of floats
        Array containing the voltages (V)
    mu : float
        Mobility (m^2/(Vs))
    eps_r : float
        Relative dielectric constant
    Vbi : float
        Built-in voltage (V)
    L : float
        Thickness (m)

    Returns
    -------
    1-D sequence of floats
        Array containing the current-density (A m^-2)
    """    
    return (9/8)*eps_0*eps_r*mu*((V-Vbi)**2)/(L**3)


def fit_MottGurney(V,J,mu,eps_r,Vbi,L,var2fit=['mu']):
    """Fit the Mott-Gurney equation to the data

    Parameters
    ----------
    V : 1-D sequence of floats
        Array containing the voltages (V)
    J : 1-D sequence of floats
        Array containing the current-density (A m^-2)
    mu : float
        Mobility (m^2/(Vs))
    eps_r : float
        Relative dielectric constant
    Vbi : float
        Built-in voltage (V)
    L : float
        Thickness (m)
    var2fit : list, optional
        Chose variable to fit (can be multiple), by default ['mu']

    Returns
    -------
    list
        list of the fitted values in the same order than var2fit
    """    
    fixed_var = ['V','mu','eps_r','Vbi','L']
    for i in var2fit:
        if i in fixed_var:
            fixed_var.remove(i)
    
    Mod_MottGurney = Model(MottGurney, independent_vars=fixed_var)
    result = Mod_MottGurney.fit(J, V=V,mu=mu,eps_r=eps_r,Vbi=Vbi,L=L)
   
    best_fit = []
    for i in var2fit:
        best_fit.append(result.params[i].value)
    return best_fit

def deriv(x,y):
    """Get the derivative of input data dy/dx

    Parameters
    ----------
    x : 1-D sequence of floats
        x-axis data
    y : 1-D sequence of floats
        y-axis data

    Returns
    -------
    1-D sequence of floats
        dy/dx
    """    
    dy = np.diff(y)/np.diff(x)
    dum = (y[-1] - y[-2])/(x[-1] - x[-2]) 
    dy = np.append(dy,[dum])
    # dum = (y[1] - y[0])/(x[1] - x[0]) 
    # dy = np.append([dum],dy)
    return list(dy)

def log_slope(x,y):
    """Get the slope of the logarithmic data

    Parameters
    ----------
    x : 1-D sequence of floats
        x-axis data
    y : 1-D sequence of floats
        y-axis data

    Returns
    -------
    1-D sequence of floats
        slope of the logarithmic data
    """ 
    # Convert data into np.arrays
    x = np.asarray(x)
    y = np.asarray(y)   
    # remove V = 0V before getting log
    if 0 in x:
        idx_0 = x.index(0)
        x = x.pop(idx_0)
        y = y.pop(idx_0)
    log_xf = np.log(x)
    log_yf = np.log(y)
    # Take derivative of data
    slopef = deriv(log_xf,log_yf)
    return np.asarray(slopef)

def calc_Vsat(L,Nc,phi,eps_r,T):
    """ Calculate Vsat for SCLC measurement 
    as defined in equation (15) in https://doi.org/10.1021/acsenergylett.0c02599

    Vsat = (8/9) * ((q*Nc*L**2)/(eps_0*eps_r))*exp(-q*phi/k*T)

    Parameters
    ----------
    L : float
        Thickness (m)
    Nc : float
        Effective density of states (m^-3)
    phi : float
        Injection barrier (V)
    eps_r : float
        Relative dielectric constant
    T : float
        Temperature (K)

    Returns
    -------
    float
        returns Vsat as defined in 
    """    
    Vsat = (8/9) * ((q*Nc*L**2)/(eps_0*eps_r))*np.exp(-(q*phi)/(k*T))
    return Vsat

def calc_Vtfl(traps,L,eps_r):
    """Calculate VTFL for SCLC measurement 
    as defined in equation (2) in ACS Energy Lett. 2021, 6, 3, 1087–1094
    https://doi.org/10.1021/acsenergylett.0c02599

    Vnet = q * n_traps * L**2 /( 2 * eps_0 * eps_r) 

    Parameters
    ----------
    traps : float
        Trap density (m^-3)
    L : float
        Thickness (m)
    eps_r : float
        Relative dielectric constant

    Returns
    -------
    float
        returns vnet as defined in 
    """    
    vtfl = q * (traps) * L**2 /( 2 * eps_0 * eps_r)
    return vtfl

def calc_trap_charge(Vnet,L,eps_r):
    """Calculate the trap charges for SCLC measurement
    as defined in equation (2) in ACS Energy Lett. 2021, 6, 3, 1087–1094
    https://doi.org/10.1021/acsenergylett.0c02599

    Vnet = q * n_trap * L**2 /( 2 * eps_0 * eps_r) 

    Note that if there are not ions or dopant n_net = traps

    Parameters
    ----------
    Vtfl : float
        Vtfl see ref
    L : float
        Thickness (m)
    eps_r : float
        Relative dielectric constant

    Returns
    -------
    float
        trapped charges in the bulk
    """    
    n_trap = Vtfl * ( 2 * eps_0 * eps_r)/ (q * L**2)
    return n_trap # m^-3

def calc_Vnet_with_ions(ions,traps,L,eps_r):
    """Calculate Vnet for SCLC measurement in the presence of Ions
    as defined in equation (4) in ACS Energy Lett. 2021, 6, 3, 1087–1094
    https://doi.org/10.1021/acsenergylett.0c02599

    Vnet = q * n_net * L**2 /( 2 * eps_0 * eps_r) = q * (traps-ions) * L**2 /( 2 * eps_0 * eps_r)

    Parameters
    ----------
    ions : float
        Ion density (m^-3)
    traps : float
        Trap density (m^-3)
    L : float
        Thickness (m)
    eps_r : float
        Relative dielectric constant

    Returns
    -------
    float
        returns vnet as defined in 
    """    
    vnet = q * (traps-ions) * L**2 /( 2 * eps_0 * eps_r)
    return vnet

def calc_net_charge(Vnet,L,eps_r):
    """Calculate the net charge for SCLC measurement
    as defined in equation (4) in ACS Energy Lett. 2021, 6, 3, 1087–1094
    https://doi.org/10.1021/acsenergylett.0c02599

    Vnet = q * n_net * L**2 /( 2 * eps_0 * eps_r) 

    Note that if there are not ions or dopant n_net = traps

    Parameters
    ----------
    Vnet : float
        Vnet see ref
    L : float
        Thickness (m)
    eps_r : float
        Relative dielectric constant

    Returns
    -------
    float
        net-charge in the bulk
    """    
    net_charge= Vnet * ( 2 * eps_0 * eps_r)/ (q * L**2)
    return net_charge # m^-3

def calc_nt_min(L,eps_r,T):
    """Calculate the minimum appearant trap density for SCLC measurement
    as defined in equation (3) in ACS Energy Lett. 2021, 6, 3, 1087–1094
    https://doi.org/10.1021/acsenergylett.0c02599

    Ntmin = 4*np.Pi()**2*((k*T)/(q**2))*((eps_0*eps_r)/(L**2))

    Parameters
    ----------
    L : float
        Thickness (m)
    eps_r : float
        Relative dielectric constant
    T : float
        Temperature (K)

    Returns
    -------
    float
        minimum appearant trap density
    """    
    Ntmin = 4*np.pi**2*((k*T)/(q**2))*((eps_0*eps_r)/(L**2))
    return Ntmin # m^-3


def SCLC_get_data_plot(volt,curr):
    """Get the data for the SCLC plot

    Parameters
    ----------
    volt : 1-D sequence of floats
        Voltage data
    curr : 1-D sequence of floats
        Current data

    Returns
    -------
    V_slopef : 1-D sequence of floats
        Voltage data after filtering
    J_slopef : 1-D sequence of floats
        Current data after filtering
    slopesf : 1-D sequence of floats
        logarithmic slopes of the JV after filtering
    get_tangentf : bool
        True if tangents are calculated i.e. if max(slopef) > 2, False if not
    idx_maxf : int
        index of the max slope of the JV after filtering
    max_slopesf : float
        max slope of the JV after filtering
    tang_val_V1f : 1-D sequence of floats
        tangent values of the JV after filtering for the first tangent point. Typically crossing between the ohmic and Trap filled limited regime.
    tang_val_V2f : 1-D sequence of floats
        tangent values of the JV after filtering for the second tangent point (here the inflexion point)
    tang_val_V3f : 1-D sequence of floats
        tangent values of the JV after filtering for the third tangent point. Typically crossing between the Trap filled limited regime and the Mott-Gurney regime.
    V1f : float
        Voltage value of the first crossing point
    J1f : float
        current value of the first crossing point
    V2f : float
        Voltage value of the second crossing point
    J2f : float
        current value of the second crossing point
    Vinf : float
        Voltage value of the inflexion point
    Jinf : float
        current value of the inflexion point
        
    """    
    
    volt = np.asarray(volt)
    curr = np.asarray(curr)

    # remove volt = 0V before getting log
    if 0 in volt:
        idx_0 = np.where(volt == 0)[0][0]
        volt = np.delete(volt,idx_0)
        curr = np.delete(curr,idx_0)
    
    # if we get a 0 or negative value in volt or curr raise an error
    if 0 in volt or 0 in curr:
        raise ValueError('We got a 0 value in the voltage or current data, please check your input data')
    if any(i < 0 for i in volt) or any(i < 0 for i in curr):
        raise ValueError('We got a negative value in the voltage or current data, please check your input data')

    # remove first offset_noise points in case it is noisy
    # offset_noise = 0
    # volt = volt[offset_noise:]
    # curr = curr[offset_noise:]

    slopesf = log_slope(volt,curr)
    V_slopef = np.asarray(volt)
    J_slopef = np.asarray(curr)

    # Get max slope if max slopes > 2.2
    idx_maxf = np.argmax(slopesf) 
    max_slopesf = slopesf[idx_maxf]

    if max_slopesf>2.0:
        get_tangentf = 1
    else: get_tangentf = 0


    # Calculate tangent and crossing point
    tang_val_V1f,tang_val_V2f,tang_val_V3f,V1f,J1f,V2f,J2f,Vinf,Jinf = [],[],[],[],[],[],[],[],[]
    if get_tangentf == 1:
            tang_val_V1f = np.exp(np.log(J_slopef[0])+slopesf[0]*(np.log(V_slopef)-np.log(V_slopef[0])))
            tang_val_V2f = np.exp(np.log(J_slopef[idx_maxf])+max_slopesf*(np.log(V_slopef)-np.log(V_slopef[idx_maxf])))
            tang_val_V3f = np.exp(np.log(J_slopef[-1])+slopesf[-1]*(np.log(V_slopef)-np.log(V_slopef[-1])))
            V1f = np.exp((1/(slopesf[0]-max_slopesf)*np.log((J_slopef[idx_maxf]*(V_slopef[0]**slopesf[0]))/(J_slopef[0]*(V_slopef[idx_maxf]**max_slopesf)))))
            J1f = np.exp(np.log(J_slopef[0])+slopesf[0]*(np.log(V1f)-np.log(V_slopef[0])))
            V2f = np.exp((1/(slopesf[-1]-max_slopesf)*np.log((J_slopef[idx_maxf]*(V_slopef[-1]**slopesf[-1]))/(J_slopef[-1]*(V_slopef[idx_maxf]**max_slopesf)))))
            J2f = np.exp(np.log(J_slopef[-1])+slopesf[-1]*(np.log(V2f)-np.log(V_slopef[-1])))
            Vinf = V_slopef[idx_maxf]
            Jinf = J_slopef[idx_maxf]

    # print(calc_net_charge(V1,thick))
    # print(calc_net_charge(V2,thick))
   
    return V_slopef,J_slopef,slopesf,get_tangentf,idx_maxf,max_slopesf,tang_val_V1f,tang_val_V2f,tang_val_V3f,V1f,J1f,V2f,J2f,Vinf,Jinf

def Make_SCLC_plot(ax,data_JV,x='Vext',y=['Jext'],show_tangent=[1,2,3],xlimits=[],ylimits=[],plot_type=0,labels='',colors='b',line_type = ['-'],mark='',legend=True,plot_jvexp=False,data_JVexp=pd.DataFrame(),save_yes=False,pic_save_name='JV.jpg'):
    """ Make typical plot for SCLC measurement analysis for SIMsalabim  
    
    Parameters
    ----------
    num_fig : int
        number of the fig to plot JV

    data_JV : DataFrame
        Panda DataFrame containing JV_file

    x : str, optional
        xaxis data  (default = 'Vext'), by default 'Vext'

    y : list of str, optional
        yaxis data can be multiple like ['Jext','Jbimo']  (default = ['Jext']), by default ['Jext']
    
    show_tangent : list of int, optional
        show tangent line at V1,Vinf,V2  (default = [1,2,3]), by default [1,2,3]

    xlimits : list, optional
        x axis limits if = [] it lets python chose limits, by default []

    ylimits : list, optional
        y axis limits if = [] it lets python chose limits, by default []

    plot_type : int, optional
        type of plot 1 = logx, 2 = logy, 3 = loglog else linlin (default = linlin), by default 0

    labels : str, optional
        label of the JV, by default ''

    colors : str, optional
        color for the JV line, by default 'b'

    line_type : list, optional
        type of line for simulated data plot
        size line_type need to be = size(y), by default ['-']

    mark : str, optional
        type of Marker for the JV, by default ''

    legend : bool, optional
        Display legend or not, by default True

    plot_jvexp : bool, optional
        plot an experimental JV or not, by default False

    data_JVexp : [type], optional
        Panda DataFrame containing experimental JV_file with 'V' the voltage and 'J' the current, by default pd.DataFrame()

    save_yes : bool, optional
        If True, save JV as an image with the  file name defined by "pic_save_name", by default False

    pic_save_name : str, optional
        name of the file where the figure is saved, by default 'JV.jpg'
    
    Returns
    -------
    Vslopef : list
        list of of the Voltage values after filtering
    Jslopef : list
        list of of the current values after filtering
    slopesf : list
        list of logarithmic slopes of the JV after filtering
    get_tangentf : bool
        True if tangents are calculated i.e. if max(slopef) > 2, False if not
    idx_maxf : int
        index of the max slope of the JV after filtering
    max_slopesf : float
        max slope of the JV after filtering
    tang_val_V1f : list
        list of the tangent values of the JV after filtering for the first tangent point. Typically crossing between the ohmic and Trap filled limited regime.
    tang_val_V2f : list
        list of the tangent values of the JV after filtering for the second tangent point (here the inflexion point)
    tang_val_V3f : list
        list of the tangent values of the JV after filtering for the third tangent point. Typically crossing between the Trap filled limited regime and the Mott-Gurney regime.
    V1f : float
        Voltage value of the first crossing point
    J1f : float
        current value of the first crossing point
    V2f : float
        Voltage value of the second crossing point
    J2f : float
        current value of the second crossing point
    Vinf : float
        Voltage value of the inflexion point
    Jinf : float
        current value of the inflexion point

    """    

    # Filter data for V < 0 and J < 0
    print('In Make_SCLC_plot')
    print('Filtering data for V < 0 and J < 0')
    print('If you want to plot JV with V < 0, you need to change modify your input first')
    data_JV = data_JV[data_JV.Vext > 0]
    data_JV = data_JV[data_JV.Jext > 0]

    # Get tangent and crossing point data
    if show_tangent != []:
        V_slopef,J_slopef,slopesf,get_tangentf,idx_maxf,max_slopesf,tang_val_V1f,tang_val_V2f,tang_val_V3f,V1f,J1f,V2f,J2f,Vinf,Jinf = SCLC_get_data_plot(np.asarray(data_JV['Vext']),np.asarray(data_JV['Jext']))
    else :
        get_tangentf = False                
    if len(y) > len(line_type):
        print('Invalid line_type list, we meed len(y) == len(line_type)')
        print('We will use default line type instead')
        line_type = []
        for counter, value in enumerate(y):
            line_type.append('-')

    # plt.figure(num_fig)
    # ax_JVs_plot = plt.axes()
    ax_JVs_plot = ax
    for i,line in zip(y,line_type):
        if plot_type == 1:
            ax_JVs_plot.semilogx(data_JV['Vext'],data_JV[i]/10,color=colors,label=labels,linestyle=line,marker=mark,markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)
            if plot_jvexp:
                ax_JVs_plot.semilogx(data_JVexp['V'],data_JVexp['J']/10,'o',markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)
            
        
        elif plot_type == 2:
            ax_JVs_plot.semilogy(data_JV['Vext'],data_JV[i]/10,color=colors,label=labels,linestyle=line,marker=mark,markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)   
            if plot_jvexp:
                ax_JVs_plot.semilogy(data_JVexp['V'],data_JVexp['J']/10,'o',markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)
            
        elif plot_type == 3:
            ax_JVs_plot.loglog(data_JV['Vext'],data_JV[i]/10,color=colors,label=labels,linestyle=line,marker=mark,markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)
            if plot_jvexp:
                ax_JVs_plot.loglog(data_JVexp['V'],data_JVexp['J']/10,'o',markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)
            
            if get_tangentf and show_tangent != []:
                print('Plotting tangents and crossing points')
                if 1 in show_tangent:
                    ax_JVs_plot.loglog(V_slopef,tang_val_V1f/10,color=colors,linestyle=line)
                if 2 in show_tangent:
                    ax_JVs_plot.loglog(V_slopef,tang_val_V2f/10,color=colors,linestyle=line)
                if 3 in show_tangent:
                    ax_JVs_plot.loglog(V_slopef,tang_val_V3f/10,color=colors,linestyle=line)
                if 1 in show_tangent and 2 in show_tangent:
                    ax_JVs_plot.loglog(V1f,J1f/10,'rs',markersize=15)
                if 2 in show_tangent and 3 in show_tangent:
                    ax_JVs_plot.loglog(V2f,J2f/10,'m^',markersize=15)
                if 2 in show_tangent:
                    ax_JVs_plot.loglog(Vinf,Jinf/10,'bo',markersize=15)
            
        else:
            ax_JVs_plot.plot(data_JV['Vext'],data_JV[i]/10,color=colors,label=labels,linestyle=line,marker=mark,markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)
            if plot_jvexp:
                ax_JVs_plot.plot(data_JVexp['V'],data_JVexp['J']/10,'o',markeredgecolor=colors,markersize=15,markerfacecolor='None',markeredgewidth = 3)
        
    
    # legend
    if legend == True:
        plt.legend(loc='best',ncol=2,frameon=False)#,fontsize = 30)
    if xlimits != []:
        plt.xlim(xlimits)
    if ylimits != []:
        plt.ylim(ylimits)
    plt.grid(b=True,which='both')
    plt.xlabel('Applied Voltage [V]')
    plt.ylabel('Current Density [mA cm$^{-2}$]')
    plt.tight_layout()
    if save_yes:
        plt.savefig(pic_save_name,dpi=100,transparent=True)
    
    if show_tangent != []:
        return ax,V_slopef,J_slopef,slopesf,get_tangentf,idx_maxf,max_slopesf,tang_val_V1f,tang_val_V2f,tang_val_V3f,V1f,J1f,V2f,J2f,Vinf,Jinf


