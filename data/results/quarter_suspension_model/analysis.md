# Quarter_suspension_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Damped two-degree quarter-car model

Suspension and tire forces depend on their relative displacement and velocity:

$$
\Delta z_s=z_s-z_u,
\quad \Delta\dot z_s=\dot z_s-\dot z_u,
\qquad
\Delta z_t=z_u-z_r,
\quad \Delta\dot z_t=\dot z_u-\dot z_r,
$$

$$
F_s=k_w\Delta z_s+c_s\Delta\dot z_s,
\qquad
F_t=k_t\Delta z_t+c_t\Delta\dot z_t,
$$

$$
\ddot z_s=-\frac{F_s}{m_s},
\qquad
\ddot z_u=\frac{F_s-F_t}{m_u}.
$$
