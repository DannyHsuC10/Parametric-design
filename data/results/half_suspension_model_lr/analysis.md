# Half_suspension_model（LR 左右）

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Left-right half-car model with direct roll-center force transfer

The suspension and tire equations use sprung-to-unsprung and unsprung-to-road relative motion. The lateral inertial moment at the roll center and the corresponding left-right force transfer are

$$
M_{x,rc}=-a_y(2m_s)h_{rc},
\qquad \Delta F_{rc}=\frac{M_{x,rc}}{t}.
$$

The body heave and roll equations are

$$
F_z=F_{s,l}+F_{s,r},
\qquad
M_x=(F_{s,r}-F_{s,l})\frac{t}{2}+a_y(2m_s)h_{cg}+M_{x,rc},
$$

$$
\ddot z_b=-\frac{F_z}{2m_s},
\qquad \ddot\phi=\frac{M_x}{I_x},
$$

$$
\ddot z_{s,l}=\ddot z_b+\frac{t}{2}\ddot\phi,
\qquad
\ddot z_{s,r}=\ddot z_b-\frac{t}{2}\ddot\phi,
$$

while the unsprung equations receive opposite roll-center forces:

$$
\ddot z_{u,l}=\frac{F_{s,l}-F_{t,l}-\Delta F_{rc}}{m_u},
\qquad
\ddot z_{u,r}=\frac{F_{s,r}-F_{t,r}+\Delta F_{rc}}{m_u}.
$$
