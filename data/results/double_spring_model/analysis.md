# Double_spring_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Two-spring, undamped quarter-car model

The sprung mass is connected to the unsprung mass by the wheel suspension rate $k_w$; the tire rate $k_t$ connects the unsprung mass to the road:

$$
F_s=k_w(z_s-z_u),
\qquad F_t=k_t(z_u-z_r),
$$

$$
\ddot z_s=-\frac{F_s}{m_s},
\qquad \ddot z_u=\frac{F_s-F_t}{m_u}.
$$

This model has separate sprung and unsprung vertical degrees of freedom and no damper terms.
