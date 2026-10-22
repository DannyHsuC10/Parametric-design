# Half_suspension_model（FR 前後）

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Front-rear half-car model with unsprung mass and anti geometry

Suspension force at each axle is computed from sprung-to-unsprung relative motion:

$$
F_{s,i}=k_i(z_{s,i}-z_{u,i})+c_i(\dot z_{s,i}-\dot z_{u,i})+F_{q,i},
\quad i\in\{f,r\}.
$$

The tire-force convention in this model is

$$
F_{t,f}=-k_t(z_{u,f}-z_{r,f})+c_t(\dot z_{u,f}-\dot z_{r,f})+F_{s,f},
$$

$$
F_{t,r}=-k_t(z_{u,r}-z_{r,r})+c_t(\dot z_{u,r}-\dot z_{r,r})+F_{s,r}.
$$

Longitudinal acceleration produces an inertial pitch moment. Anti-dive or anti-squat removes the selected fraction of that moment:

$$
M_{y,inertia}=a_x(2m_c)h_{cg},
\qquad
M_{geo}=\rho_{anti}M_{y,inertia},
$$

Here $\rho_{anti}$ selects the anti-dive or anti-squat ratio according to the sign of $a_x$. The pitch moment and body equations are

$$
M_y=F_{s,r}l_r-F_{s,f}l_f+M_{y,inertia}-M_{geo},
\qquad
\ddot z_b=-\frac{F_{s,f}+F_{s,r}}{2m_s},
\qquad
\ddot\theta=\frac{M_y}{I_y},
$$

$$
\ddot z_{u,f}=\frac{F_{t,f}}{m_u},
\qquad
\ddot z_{u,r}=\frac{F_{t,r}}{m_u}.
$$

Longitudinal wheel forces add axle lever-arm terms to the tire channels: the front receives $F_{x,f}h_{cg}/L$ and the rear receives $-F_{x,r}h_{cg}/L$ under the model's sign convention.
