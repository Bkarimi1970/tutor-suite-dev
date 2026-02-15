import os
import matplotlib.pyplot as plt

def _save_fig(fig, outpath: str):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    fig.savefig(outpath, dpi=160, bbox_inches="tight")
    return outpath

def fbd_atwood(mass_label: str, outdir: str, title_prefix="FBD"):
    """
    mass_label: "m1" or "m2"
    Shows forces on a hanging mass:
      - Tension T upward
      - Weight mg downward
    """
    mass_label = mass_label.lower().strip()
    if mass_label not in ("m1", "m2"):
        raise ValueError("mass_label must be 'm1' or 'm2'")

    fig, ax = plt.subplots(figsize=(4, 5))
    ax.set_aspect("equal")
    ax.axis("off")

    # Draw a simple point/mass
    ax.plot([0], [0], marker="o", markersize=18)

    # Force arrows
    # Up arrow: T
    ax.annotate("", xy=(0, 1.4), xytext=(0, 0.2),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(0.1, 0.9, "T", fontsize=14)

    # Down arrow: mg
    ax.annotate("", xy=(0, -1.4), xytext=(0, -0.2),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(0.1, -1.1, f"{mass_label} g", fontsize=14)

    ax.text(-1.2, 1.8, f"{title_prefix}: Atwood — {mass_label}", fontsize=12)

    outpath = os.path.join(outdir, f"fbd_atwood_{mass_label}.png")
    _save_fig(fig, outpath)
    return fig, outpath

def fbd_incline(outdir: str, show_components: bool = True, title_prefix="FBD"):
    """
    Block on an incline:
      - Normal N perpendicular to surface
      - Weight mg downward
      - Friction f along surface opposing motion (generic arrow)
      - Optional: weight components mg sinθ and mg cosθ (as guides)
    (We don't draw the actual incline angle to keep it simple.)
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_aspect("equal")
    ax.axis("off")

    # "Block"
    ax.add_patch(plt.Rectangle((-0.3, -0.2), 0.6, 0.4, fill=False, linewidth=2))

    # Coordinate-ish arrows: along slope (x') and perpendicular (y')
    ax.annotate("", xy=(1.4, 0.7), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="->", linewidth=1.8))
    ax.text(1.45, 0.7, "along slope", fontsize=10)

    ax.annotate("", xy=(-0.6, 1.2), xytext=(0.0, 0.0),
                arrowprops=dict(arrowstyle="->", linewidth=1.8))
    ax.text(-0.95, 1.25, "normal", fontsize=10)

    # N (roughly normal direction)
    ax.annotate("", xy=(-0.5, 1.0), xytext=(0.0, 0.2),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(-0.65, 0.7, "N", fontsize=14)

    # mg downward
    ax.annotate("", xy=(0.0, -1.4), xytext=(0.0, -0.2),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(0.1, -1.1, "mg", fontsize=14)

    # friction (generic, up the slope)
    ax.annotate("", xy=(-1.1, -0.6), xytext=(-0.2, -0.1),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(-1.25, -0.65, "f", fontsize=14)

    if show_components:
        ax.text(0.8, -0.9, "mg sinθ (along)", fontsize=10)
        ax.text(-1.05, 0.05, "mg cosθ (normal)", fontsize=10)

    ax.text(-1.4, 1.5, f"{title_prefix}: Incline block", fontsize=12)

    outpath = os.path.join(outdir, "fbd_incline.png")
    _save_fig(fig, outpath)
    return fig, outpath

def fbd_1d_horizontal(outdir: str, title_prefix="FBD"):
    """
    1D horizontal surface:
      - Applied force F (right)
      - Friction f (left)
      - Normal N (up)
      - Weight mg (down)
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_aspect("equal")
    ax.axis("off")

    # Block
    ax.add_patch(plt.Rectangle((-0.3, -0.15), 0.6, 0.3, fill=False, linewidth=2))

    # F right
    ax.annotate("", xy=(1.5, 0.0), xytext=(0.3, 0.0),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(1.55, 0.0, "F", fontsize=14)

    # friction left
    ax.annotate("", xy=(-1.5, 0.0), xytext=(-0.3, 0.0),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(-1.8, 0.0, "f", fontsize=14)

    # N up
    ax.annotate("", xy=(0.0, 1.2), xytext=(0.0, 0.15),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(0.1, 0.9, "N", fontsize=14)

    # mg down
    ax.annotate("", xy=(0.0, -1.2), xytext=(0.0, -0.15),
                arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(0.1, -0.95, "mg", fontsize=14)

    ax.text(-1.5, 1.5, f"{title_prefix}: 1D horizontal", fontsize=12)

    outpath = os.path.join(outdir, "fbd_1d_horizontal.png")
    _save_fig(fig, outpath)
    return fig, outpath
