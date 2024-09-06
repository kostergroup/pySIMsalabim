"""Useful helper functions for pySIMsalabim"""
######### Package Imports #########################################################################


######### Function Definitions ####################################################################

def sci_notation(number, sig_fig=2):
    """Make proper scientific notation for graphs

    Parameters
    ----------
    number : float
        Number to put in scientific notation.

    sig_fig : int, optional
        Number of significant digits (Defaults = 2).

    Returns
    -------
    output : str
        String containing the number in scientific notation
    """
    if sig_fig != -1:
        if number == 0:
            output = '0'
        else:
            ret_string = "{0:.{1:d}e}".format(number, sig_fig)
            a,b = ret_string.split("e")
            if int(b) >= 0:
                b = int(b) #removed leading "+" and strips leading zeros too.
                c = ''
            else: 
                b = abs(int(b))
                c = u"\u207B" # superscript minus sign
            SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
            b = str(b).translate(SUP)
            output =a + ' x 10' + c + b
    else:
        if number == 0:
            output = '0'
        else: 
            ret_string = "{0:.{1:d}e}".format(number, 0)
            a,b = ret_string.split("e")
            b = int(b) #removed leading "+" and strips leading zeros too.
            if int(b) >= 0:
                b = int(b) #removed leading "+" and strips leading zeros too.
                c = ''
            else: 
                b = abs(int(b))
                c = u"\u207B" # superscript minus sign
            SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
            #SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
            b = str(b).translate(SUP)
            output = '10' + c + b    
    return output