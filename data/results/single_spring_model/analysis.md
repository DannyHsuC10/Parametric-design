# single_spring_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Single-spring equivalent model

The suspension and tire compliance are represented by the equivalent rate $k_r$. The body moves relative to the road, with no independent unsprung degree of freedom:

$$
\Delta z=z_s-z_r,
\qquad F_s=k_r\Delta z,
\qquad F_t=F_s,
$$

$$
\ddot z_s=-\frac{F_s}{m_c},
\qquad \ddot z_u=\ddot z_s.
$$

Here $m_c$ is the corner-equivalent mass used by this reduced model. The assignment $F_t=F_s$ is the model's tire-force convention; it is not an independent tire spring equation.
