# two_mass_suspension_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Left-right four-degree model without rigid-body roll coupling

For each side, suspension deflection is measured between sprung and unsprung masses. The modal forces use the sum and difference of the two sides:

$$
q_h=\Delta z_l+\Delta z_r,
\qquad q_\phi=\Delta z_r-\Delta z_l,
\qquad
F_h=k_hq_h+c_h\dot q_h,
\qquad F_\phi=k_\phi q_\phi+c_\phi\dot q_\phi.
$$

Corner suspension and tire forces are

$$
F_{s,l}=\frac{F_h-F_\phi}{2}+F_{q,l},
\qquad
F_{s,r}=\frac{F_h+F_\phi}{2}+F_{q,r},
$$

$$
F_{t,i}=k_t(z_{u,i}-z_{r,i})+c_t(\dot z_{u,i}-\dot z_{r,i}),
\quad i\in\{l,r\},
$$

$$
\ddot z_{s,i}=-\frac{F_{s,i}}{m_s},
\qquad
\ddot z_{u,i}=\frac{F_{s,i}-F_{t,i}}{m_u}.
$$

The four vertical states are integrated independently; roll shown for this model is derived from the left-right body displacement difference.
