import numpy
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import cProfile

def area_to_mach(x_pos, radius_local, radius_throat):
    r"""
        Calculates the local mach number from a given axial position and local area input (in terms of its
        corresponding radius) using quasi-one dimensional (Q1D) gas flow theory.
        This code can be used, for example, to verify nozzle data by comparing simulated results
        with the analytical Q1D flow solution.

        | For more details:
        | [1] Modern Compressible Flow - Chapter 5 "Quasi-One-Dimensional Flow", J.D. Anderson
        | [2] Compressible Flow in a Nozzle, ANSYS Innovation Course.
              courses.ansys.com/index.php/courses/compressible-flow-in-a-nozzle/

        It uses the following mathematical relation, the area mach relation:
        (LateX equation)
        \left( \frac{A}{A^*} \right)^2=\frac{1}{M^2}\left[ \frac{2}{\gamma+1}\left( 1+\frac{\gamma-1}{2}M^2 \right)
        \right]^\frac{\gamma+1}{\gamma-1}

        Output values can be verified using the Appendix A in [1].

        Returns
        a mach number value corresponding to the given local area's radius.
    """
    gamma = 1.4
    tolerance = 0.000001
    lower_limit = 1 - tolerance
    upper_limit = 1 + tolerance
    decimals = 5

    # initial values for the numerical approximation
    mach_no = 1
    step_size = -0.1
    supersonic = False

    # check if the input is valid
    if radius_local < radius_throat:
        raise Exception("Input must be >= than {}".format(radius_throat))

    # check if the local area position is upstream (negative x_pos; subsonic and convergent)
    # or downstream (positive x_pos; supersonic and divergent) from the throat
    # the x axis origin lies on the throat
    if x_pos < 0:
        supersonic = False
    else:
        supersonic = True

    # local area ratio (=squared local radius ratio) is the local area divided by the throat area
    local_area_ratio = (radius_local ** 2) / (radius_throat ** 2)

    # left side "ls" of the area-mach relation equation
    ls = local_area_ratio**2

    # right side "rs" of the area-mach relation equation
    rs = (1 / mach_no ** 2) * (2 * (1 + ((gamma - 1) * mach_no ** 2) / 2) / (gamma + 1)) ** ((gamma + 1)/(gamma - 1))

    i = rs / ls
    # following, a while loop that compares the right side and the left side,
    # when the ratio rs/ls != 1 (within a specified tolerance, e.g. 1%), the mach number mach_no is changed
    # this is iterated until the corresponding mach number is found

    # check if both sides of the equation match within the given tolerance
    # First check the trivial case where the local_area_ratio=1 (at the throat. x_pos=0)
    if i > lower_limit and i < upper_limit:
        #print(mach_no)
        return mach_no

    # second, check if the flow is subsonic, find the corresponding Mach number numerically
    # this method guesses a Mach_number and refines the guess with each iteration.
    elif not supersonic:
        while i < lower_limit or i > upper_limit:
            while i > upper_limit:
                mach_no = mach_no + step_size
                rs = (1 / mach_no ** 2) * (2 * (1 + ((gamma - 1) * mach_no ** 2) / 2) / (gamma + 1)) ** (
                        (gamma + 1) / (gamma - 1))
                i = rs / ls
                if i < lower_limit:
                    step_size = step_size * -0.1
            while i < lower_limit:
                mach_no = mach_no + step_size
                rs = (1 / mach_no ** 2) * (2 * (1 + ((gamma - 1) * mach_no ** 2) / 2) / (gamma + 1)) ** (
                        (gamma + 1) / (gamma - 1))
                i = rs / ls
                if i > upper_limit:
                    step_size = step_size * -0.1

        else:
            mach_no = np.around(mach_no, decimals=5)
            #print(mach_no)
            return mach_no
    elif supersonic:
        step_size = step_size*-1
        while i < lower_limit or i > upper_limit:
            while i < lower_limit:
                mach_no = mach_no + step_size
                rs = (1 / mach_no ** 2) * (2 * (1 + ((gamma - 1) * mach_no ** 2) / 2) / (gamma + 1)) ** (
                        (gamma + 1) / (gamma - 1))
                i = rs / ls
                if i > upper_limit:
                    step_size = step_size * -0.1
            while i > upper_limit:
                mach_no = mach_no + step_size
                rs = (1 / mach_no ** 2) * (2 * (1 + ((gamma - 1) * mach_no ** 2) / 2) / (gamma + 1)) ** (
                        (gamma + 1) / (gamma - 1))
                i = rs / ls
                if i < lower_limit:
                    step_size = step_size * -0.1
        else:
            mach_no = np.around(mach_no, decimals=decimals)
            #print(mach_no)
            return mach_no


def nozzle_contour_to_mach(filename, radius_throat):
    r"""receives a nozzle contour in the form of a csv file (x, y) where x is the local position on the axis and
    y is the local radius, and returns another csv file (x, y, M) with an additional column assigning the
    corresponding mach number according to Quasi 1D compressible flow theory.
    """
    # Read CSV file into DataFrame df
    df = pd.read_csv(filename, index_col=None)

    # Build data arrays
    x_nozzle = df['x_nozzle'].to_numpy()
    y_nozzle = df['y_nozzle'].to_numpy()
    # contour_mach array is a 2D array [(x_i,y_i,M_i),...]
    contour_mach = np.zeros((len(df.index), 3))

    # Process data into the 2d array
    i = 0
    while i < len(df.index):
        local_mach = area_to_mach(df.iloc[i]['x_nozzle'], df.iloc[i]['y_nozzle'], radius_throat)
        contour_mach[i] = (x_nozzle[i], y_nozzle[i],local_mach)
        i = i + 1

    x_mach_array = np.zeros((len(df.index), 2))
    i = 0
    while i < (len(df.index)):
        x_mach_array[i] = (contour_mach[i, 0]/1000, contour_mach[i, 2])
        i = i + 1
    x_mach_columns = ['x', 'mach']
    x_mach_df = pd.DataFrame(data=x_mach_array, columns=x_mach_columns)

    header_xy = '(title "Mach Number")\n(labels "Position" "Mach Number")\n\n((xy/key/label "Q1D")'
    footer_xy = '\n)'
    np.savetxt('nozzle_Q1D_xm.xy', x_mach_df, delimiter="\t", header=header_xy, footer=footer_xy, comments='')


    # build csv file to export/return
    np.savetxt('nozzle_Q1D_xym.csv',
              contour_mach, delimiter=";")


nozzle_contour_to_mach('rao_nozzle.csv', 4.3263)