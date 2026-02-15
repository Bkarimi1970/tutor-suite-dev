import matplotlib.pyplot as plt
from core.physics_projectile import solve_projectile, trajectory
from tools.projectile_plot import plot_trajectory
def plot_trajectory(x, y):
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Projectile Motion Trajectory")
    ax.grid(True)
    return fig
elif user_msg.startswith("/projectile "):
    args = parse_kin_args(user_msg[len("/projectile "):])

    v0, _ = args.get("v0", (None, None))
    theta, _ = args.get("theta", (None, None))
    y0, _ = args.get("y0", (0.0, None))

    if v0 is None or theta is None:
        reply = "Usage: /projectile v0=20 m/s, theta=30 deg, y0=0 m"
    else:
        results = solve_projectile(v0, theta, y0)
        x, y, _ = trajectory(v0, theta, y0)

        fig = plot_trajectory(x, y)
        st.pyplot(fig)

        reply = f"""
**Projectile Motion Results**

Time of flight: {results['time_of_flight']:.2f} s  
Range: {results['range']:.2f} m  
Maximum height: {results['max_height']:.2f} m
"""

    st.session_state.chat.append(("assistant", reply))
    with st.chat_message("assistant"):

        st.markdown(reply)
