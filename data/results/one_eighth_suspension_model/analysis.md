# one_eighth_suspension_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Single-degree spring-damper model

This model applies the equivalent suspension rate and damper between the body and road:

$$
F_s=k_r(z_s-z_r)+c_s(\dot z_s-\dot z_r),
\qquad F_t=F_s,
$$

$$
\ddot z_s=-\frac{F_s}{m_c},
\qquad \ddot z_u=\ddot z_s.
$$

The unsprung response is constrained to the body acceleration rather than integrated as a separate mass.
