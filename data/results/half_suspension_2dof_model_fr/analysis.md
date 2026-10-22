# Half_suspension_2DOF_model（FR 前後）

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Front-rear two-degree half-car body model

Front and rear suspension forces use sprung displacement relative to road. The implementation distributes each modal axle force across the body equation as follows:

$$
F_{s,f}=\frac{k_f(z_{s,f}-z_{r,f})+c_f(\dot z_{s,f}-\dot z_{r,f})}{2}+F_{q,f},
$$

$$
F_{s,r}=\frac{k_r(z_{s,r}-z_{r,r})+c_r(\dot z_{s,r}-\dot z_{r,r})}{2}+F_{q,r}.
$$

Spring and longitudinal-acceleration moments are

$$
M_{y,spring}=F_{s,r}l_r-F_{s,f}l_f,
\qquad M_{y,inertia}=a_x(2m_c)h_{cg},
$$

$$
F_z=F_{s,f}+F_{s,r},
\qquad M_y=M_{y,spring}+M_{y,inertia},
$$

$$
\ddot z_b=-\frac{F_z}{2m_s},
\qquad \ddot\theta=\frac{M_y}{I_y},
$$

$$
\ddot z_{s,f}=\ddot z_b+l_f\ddot\theta,
\qquad
\ddot z_{s,r}=\ddot z_b-l_r\ddot\theta.
$$

There are no independent unsprung states in this reduced model; axle acceleration follows the corresponding rigid-body point.
