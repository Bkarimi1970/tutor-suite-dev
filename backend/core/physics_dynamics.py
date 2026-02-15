import math
from pint import UnitRegistry
from core.physics_dynamics import solve_dyn_1d, solve_dyn_incline

ureg = UnitRegistry()
Q_ = ureg.Quantity

def _to_si(val, unit, target_unit):
    """Convert (val, unit) to target_unit. If unit missing, assume already SI."""
    if unit:
        return float(Q_(val, unit).to(target_unit).magnitude)
    return float(val)

def solve_dyn_1d(m=None, F=None, mu=None, N=None, g=9.81):
    """
    1D dynamics on a horizontal surface.
    Inputs: m (kg), F (N), mu (unitless), N (N)
    If mu and N given -> friction f = mu*N assumed opposing motion.
    Returns: net force and acceleration.
    """
    if m is None or F is None:
        return None, "Usage: /dyn 1d m=2 kg, F=10 N, mu=0.2, N=19.62 N"

    friction = 0.0
    if mu is not None and N is not None:
        friction = mu * N

    F_net = F - friction
    a = F_net / m

    return {
        "F_friction": friction,
        "F_net": F_net,
        "a": a
    }, None

def solve_dyn_incline(m=None, theta_deg=None, mu=None, g=9.81):
    """
    Block on incline angle theta (degrees).
    Assumes motion down the slope unless friction prevents it.
    Forces along slope:
      m g sin(theta) - friction
    Normal:
      N = m g cos(theta)
    friction magnitude (if mu given):
      f = mu * N
    acceleration along slope:
      a = (m g sin(theta) - f) / m  (down-slope positive)
    """
    if m is None or theta_deg is None:
        return None, "Usage: /dyn incline m=2 kg, theta=30 deg, mu=0.10"

    theta = math.radians(theta_deg)
    N = m * g * math.cos(theta)
    F_parallel = m * g * math.sin(theta)

    friction = 0.0
    if mu is not None:
        friction = mu * N

    F_net = F_parallel - friction
    a = F_net / m

    # If friction is big enough to prevent sliding, a could be <= 0 (static friction not modeled)
    return {
        "N": N,
        "F_parallel": F_parallel,
        "F_friction": friction,
        "F_net": F_net,
        "a": a
    }, None
elif user_msg.startswith("/dyn "):
    arg_str = user_msg[len("/dyn "):].strip()

    # format: "/dyn 1d m=..., F=..., mu=..., N=..."
    # or:     "/dyn incline m=..., theta=..., mu=..."
    parts = arg_str.split(" ", 1)
    if len(parts) < 2:
        reply = "Usage:\n/dyn 1d m=2 kg, F=10 N, mu=0.2, N=19.62 N\n/dyn incline m=2 kg, theta=30 deg, mu=0.10"
    else:
        mode = parts[0].lower()
        args = parse_kin_args(parts[1])

        def get_num(name, default=None):
            if name not in args:
                return default
            return float(args[name][0])

        def get_unit(name):
            if name not in args:
                return None
            return args[name][1]

        # Pull values
        m = None
        if "m" in args:
            m = float(args["m"][0])
            m_unit = args["m"][1]
            # convert to kg if unit provided
            try:
                from pint import UnitRegistry
                ureg = UnitRegistry()
                m = float((ureg.Quantity(m, m_unit)).to("kg").magnitude) if m_unit else float(m)
            except Exception:
                pass

        mu = get_num("mu", None)

        if mode == "1d":
            F = None
            if "F" in args:
                F = float(args["F"][0])
                F_unit = args["F"][1]
                try:
                    from pint import UnitRegistry
                    ureg = UnitRegistry()
                    F = float((ureg.Quantity(F, F_unit)).to("N").magnitude) if F_unit else float(F)
                except Exception:
                    pass

            N = None
            if "N" in args:
                N = float(args["N"][0])
                N_unit = args["N"][1]
                try:
                    from pint import UnitRegistry
                    ureg = UnitRegistry()
                    N = float((ureg.Quantity(N, N_unit)).to("N").magnitude) if N_unit else float(N)
                except Exception:
                    pass

            res, err = solve_dyn_1d(m=m, F=F, mu=mu, N=N)
            if err:
                reply = err
            else:
                reply = (
                    "**Dynamics (1D) — Newton’s 2nd Law**\n\n"
                    f"- Friction force: {res['F_friction']:.3f} N\n"
                    f"- Net force: {res['F_net']:.3f} N\n"
                    f"- Acceleration: {res['a']:.3f} m/s²\n\n"
                    "Sanity check: units → (N/kg) = m/s² ✅"
                )

        elif mode == "incline":
            theta = None
            if "theta" in args:
                theta = float(args["theta"][0])
                # if student uses radians they can pass theta=0.52 rad (later upgrade)
                # for now assume degrees if unit contains 'deg' or missing.
                # If they pass 'rad', convert.
                th_unit = args["theta"][1]
                if th_unit and "rad" in th_unit:
                    theta = theta * 180.0 / 3.141592653589793

            res, err = solve_dyn_incline(m=m, theta_deg=theta, mu=mu)
            if err:
                reply = err
            else:
                reply = (
                    "**Dynamics (Incline) — Newton’s 2nd Law along the slope**\n\n"
                    f"- Normal force N: {res['N']:.3f} N\n"
                    f"- Component down slope (mg sinθ): {res['F_parallel']:.3f} N\n"
                    f"- Friction (μN): {res['F_friction']:.3f} N\n"
                    f"- Net force along slope: {res['F_net']:.3f} N\n"
                    f"- Acceleration down slope: {res['a']:.3f} m/s²\n\n"
                    "Note: This assumes kinetic friction if μ is provided."
                )
        else:
            reply = "Unknown mode. Use: /dyn 1d ...  or  /dyn incline ..."

    st.session_state.chat.append(("assistant", reply))
    with st.chat_message("assistant"):
        st.markdown(reply)
