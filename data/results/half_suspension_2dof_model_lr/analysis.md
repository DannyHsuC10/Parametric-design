# Half_suspension_2DOF_model（LR 左右）

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Left-right two-degree half-car body model

Suspension modal forces use sprung displacement relative to road. The corner forces and rigid-body equations are

$$
F_{s,l}=\frac{F_h-F_\phi}{2}+F_{q,l},
\qquad
F_{s,r}=\frac{F_h+F_\phi}{2}+F_{q,r},
$$

$$
F_z=F_{s,l}+F_{s,r},
\qquad
M_x=(F_{s,r}-F_{s,l})\frac{t}{2}+a_y(2m_c)h_{cg},
$$

$$
\ddot z_b=-\frac{F_z}{2m_s},
\qquad \ddot\phi=\frac{M_x}{I_x},
$$

$$
\ddot z_{s,l}=\ddot z_b+\frac{t}{2}\ddot\phi,
\qquad
\ddot z_{s,r}=\ddot z_b-\frac{t}{2}\ddot\phi.
$$

This reduced model has no independent unsprung states. Corner accelerations follow the rigid-body motion; its tire-force channel records the corresponding suspension corner force.
