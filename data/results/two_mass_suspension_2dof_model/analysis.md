# two_mass_suspension_2DOF_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Left-right two-mass modal model

Each corner's sprung displacement is measured relative to its road input. The heave and roll coordinates use sums and differences, as implemented:

$$
q_h=\Delta z_l+\Delta z_r,
\qquad q_\phi=\Delta z_r-\Delta z_l,
$$

$$
F_h=k_hq_h+c_h\dot q_h,
\qquad F_\phi=k_\phi q_\phi+c_\phi\dot q_\phi,
$$

$$
F_{s,l}=F_h-F_\phi+F_{q,l},
\qquad F_{s,r}=F_h+F_\phi+F_{q,r},
$$

where $F_{q,i}=k_{q,i}\Delta z_i+c_{q,i}\Delta\dot z_i$. The model maps modal force to corner acceleration without an independent unsprung-mass state:

$$
\ddot z_{s,i}=-\frac{F_{s,i}}{m_c},
\qquad F_{t,i}=F_{s,i},
\qquad \ddot z_{u,i}=\ddot z_{s,i},
\quad i\in\{l,r\}.
$$
