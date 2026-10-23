# Half_rollcenter_all_model

Each run creates a fresh state and evaluates the model's force and acceleration equations at each time step. Symbols below use the implementation's sign convention: vertical displacement is positive upward; subscripts $s$, $u$, and $r$ denote sprung mass, unsprung mass, and road; $l/r$ denote left/right and $f/r$ denote front/rear. A force called $F_t$ follows the particular model's force definition and can therefore differ between simplified model families.

The semi-implicit Euler update used for translational states is

$$
\dot z^{n+1}=\dot z^n+\ddot z^n\Delta t,
\qquad
z^{n+1}=z^n+\dot z^{n+1}\Delta t.
$$

## Left-right half-car model with compliant frame force transfer

The model has four suspension/tire DOFs plus one equivalent body-spring RC branch. Following the RC optimization study, lateral excitation uses the half-car sprung mass $M_s=2m_s$, and the branch uses $m_{frame}=M_s/4$. This equivalent mass does not add vehicle mass. The roll-center force command drives the branch:

$$
M_{x,rc}=-a_yM_sh_{rc},
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

The body moment is $M_x=(F_{s,r}-F_{s,l})t/2+a_yM_s(h_{cg}-h_{rc})$, with $\ddot z_b=-(F_{s,l}+F_{s,r})/(2m_s)$ and $\ddot\phi=M_x/I_x$. The frame displacement and velocity are integrated alongside the corner states.

The body-spring stiffness is $k_{frame}=\rho_{frame}k_\phi$, where $\rho_{frame}$ is `k_frame_to_roll_ratio` (default 10) and $k_\phi$ is the LR model's linear `k_roll` channel rate, equal to half the shared `Ks_roll_N_per_m`. The nonnegative `zeta_frame` input defaults to 0.5. After applying upstream mass and stiffness, the damping coefficient is recalculated as $c_{frame}=2\zeta_{frame}\sqrt{k_{frame}m_{frame}}$ to preserve the requested damping ratio. Response timing follows $\omega_{frame}=\sqrt{k_{frame}/m_{frame}}$ and damping. The unused `tau_rc` parameter has been removed.

The default damping ratio of 0.5 produces decaying oscillations. If `zeta_frame` is set to zero, with zero initial state and a constant force command, the transmitted force is

$$
F_{frame}(\tau)=F_{frame,cmd}[1-\cos(\omega_{frame}\tau)],
$$

where $\tau$ denotes elapsed time after excitation starts. All oscillations are retained. The LR model keeps its suspension/tire dynamics and uses the average upstream front/rear RC height; the RC study optimizes the first transfer-rate pulse of separate axle models. Their complete responses need not coincide. The equivalent branch is not a full model of coupled chassis flexibility.

CSV and PKL exports include `F_frame_cmd`, `F_frame_spring`, `F_frame_damper`, `dF_roll`, `d_frame`, `v_frame`, and `a_frame`. Each scenario also provides a frame-force/displacement plot.
