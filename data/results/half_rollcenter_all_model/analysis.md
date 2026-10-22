# Half_rollcenter_all_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Left-right half-car model with compliant frame force transfer

The body and direct roll-center moment follow the left-right half-car formulation. The roll-center force command drives a compliant frame state:

$$
M_{x,rc}=-a_y(2m_c)h_{rc},
\qquad F_{frame,cmd}=\frac{M_{x,rc}}{t},
$$

$$
F_{frame}=k_{frame}d_{frame}+c_{frame}\dot d_{frame},
\qquad
\ddot d_{frame}=\frac{F_{frame,cmd}-F_{frame}}{m_{frame}}.
$$

The frame force, rather than the instantaneous roll-center force command, acts on the unsprung masses:

$$
\ddot z_{u,l}=\frac{F_{s,l}-F_{t,l}-F_{frame}}{m_u},
\qquad
\ddot z_{u,r}=\frac{F_{s,r}-F_{t,r}+F_{frame}}{m_u}.
$$

The body moment remains $M_x=(F_{s,r}-F_{s,l})t/2+a_y(2m_c)h_{cg}+M_{x,rc}$, with $\ddot z_b=-(F_{s,l}+F_{s,r})/(2m_s)$ and $\ddot\phi=M_x/I_x$. The frame displacement and velocity are integrated alongside the corner states.
