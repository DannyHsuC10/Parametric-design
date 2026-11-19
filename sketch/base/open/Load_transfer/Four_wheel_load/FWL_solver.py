import numpy as np

def four_wheel_load_lsm(ax, ay, F_add, CF_rela, car, check=False):
    """
    Solve four wheel normal loads using the Least Action Principle.

    Parameters
    ----------
    ax : float
        Longitudinal acceleration (m/s²)
    ay : float
        Lateral acceleration (m/s²)
    F_add : array_like(3)
        Additional external force [Fx, Fy, Fz] (N)
    CF_rela : array_like(3)
        Position of external force relative to CG [x, y, z] (m)
    car : object
        Vehicle parameters.
        Required attributes:
            m
            h
            L
            d
            CG_x = [front_ratio, rear_ratio]
            CG_y = [left_ratio, right_ratio]
    check : bool
        Print equilibrium check.

    Returns
    -------
    N : ndarray (4,)
        Wheel loads [FL, FR, RL, RR]
    """

    az = -9.81

    # Wheel positions relative to CG
    x_pos = car.L * np.array([
        car.CG_x[1],
        car.CG_x[1],
        -car.CG_x[0],
        -car.CG_x[0]
    ])

    y_pos = car.d * np.array([
        -car.CG_y[1],
         car.CG_y[0],
        -car.CG_y[1],
         car.CG_y[0]
    ])

    z_pos = np.ones(4)

    # Equilibrium matrix
    A = np.vstack((z_pos, y_pos, x_pos))

    # Right hand side
    b = car.m * np.array([
        az,
        ay * car.h,
        ax * car.h
    ])

    # Additional force
    Mx_add = 0.0
    My_add = 0.0

    if F_add is not None and CF_rela is not None:

        F_add = np.asarray(F_add)
        r = np.asarray(CF_rela)

        Mx_add = r[1] * F_add[2] - r[2] * F_add[1]
        My_add = r[2] * F_add[0] - r[0] * F_add[2]

        b += np.array([
            F_add[2],
            Mx_add,
            My_add
        ])

    # Least action solution
    N = A.T @ np.linalg.solve(A @ A.T, -b)

    if check:

        print("Wheel Loads (N)")
        print(f"FL = {N[0]:.2f}")
        print(f"FR = {N[1]:.2f}")
        print(f"RL = {N[2]:.2f}")
        print(f"RR = {N[3]:.2f}")

        Fz = np.sum(N) + car.m * az
        if F_add is not None:
            Fz += F_add[2]

        print(f"\nForce balance Fz = {Fz:.6f} N")

        Mx = y_pos @ N + car.m * ay * car.h + Mx_add
        My = x_pos @ N + car.m * ax * car.h + My_add

        print(f"Roll moment balance  = {Mx:.6e} Nm")
        print(f"Pitch moment balance = {My:.6e} Nm")

    return N

def four_wheel_load_cg(ax, ay, F_add, CF_rela, car, check=False):
    """
    Four wheel load estimation using CG distribution method.

    Parameters
    ----------
    ax : float
        Longitudinal acceleration (m/s²)
    ay : float
        Lateral acceleration (m/s²)
    F_add : array_like(3) or None
        Additional external force [Fx, Fy, Fz] (N)
    CF_rela : array_like(3) or None
        Position of external force relative to CG [x, y, z] (m)
    car : object
        Vehicle parameters.
        Required attributes:
            m
            h
            L
            d
            CG_x = [front_ratio, rear_ratio]
            CG_y = [left_ratio, right_ratio]
    check : bool
        Print result.

    Returns
    -------
    N : ndarray (4,)
        Wheel loads [FL, FR, RL, RR]
    """

    g = 9.81
    W = car.m * g

    # Longitudinal / lateral load transfer
    dF = car.m * car.h * np.array([
        ax / car.L,
        ay / car.d
    ])

    # Additional force contribution
    if F_add is not None and CF_rela is not None:

        F_add = np.asarray(F_add)
        r = np.asarray(CF_rela)

        # Additional moments
        Mx_add = r[1] * F_add[2] - r[2] * F_add[1]
        My_add = r[2] * F_add[0] - r[0] * F_add[2]

        dF += np.array([
            My_add / car.L,
            Mx_add / car.d
        ])

    # Static wheel loads (2×2 matrix)
    # [[FL, FR],
    #  [RL, RR]]
    Fs = W * np.outer(car.CG_x, car.CG_y)

    # Longitudinal transfer
    F_long = dF[0] * np.vstack((
        -car.CG_y,
         car.CG_y
    ))

    # Lateral transfer
    F_lat = dF[1] * np.column_stack((
         car.CG_x,
        -car.CG_x
    ))

    F = Fs + F_long + F_lat

    # Convert to vector
    N = np.array([
        F[0, 0],  # FL
        F[0, 1],  # FR
        F[1, 0],  # RL
        F[1, 1],  # RR
    ])

    if check:

        print("Wheel Loads (N)")
        print(f"FL = {N[0]:.2f}")
        print(f"FR = {N[1]:.2f}")
        print(f"RL = {N[2]:.2f}")
        print(f"RR = {N[3]:.2f}")

        print(f"\nTotal Load Error = {np.sum(N) - W:.6e} N")

    return N

