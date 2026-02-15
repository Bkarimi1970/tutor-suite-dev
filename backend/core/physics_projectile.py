import numpy as np
import math

def solve_projectile(v0, theta_deg, y0=0.0, g=9.8):
    theta = math.radians(theta_deg)

    v0x = v0 * math.cos(theta)
    v0y = v0 * math.sin(theta)

    # Time of flight
    tf = (v0y + math.sqrt(v0y**2 + 2*g*y0)) / g

    # Key results
    R = v0x * tf
    ymax = y0 + (v0y**2) / (2*g)

    return {
        "v0x": v0x,
        "v0y": v0y,
        "time_of_flight": tf,
        "range": R,
        "max_height": ymax
    }

def trajectory(v0, theta_deg, y0=0.0, g=9.8, n=400):
    theta = math.radians(theta_deg)
    v0x = v0 * math.cos(theta)
    v0y = v0 * math.sin(theta)

    tf = (v0y + math.sqrt(v0y**2 + 2*g*y0)) / g
    t = np.linspace(0, tf, n)

    x = v0x * t
    y = y0 + v0y * t - 0.5 * g * t**2

    return x, y, t
