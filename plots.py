import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.ticker import MaxNLocator
from io import BytesIO

def weekly_series_plot(formatted):
    weeks = [entry['week'] for entry in formatted]
    counts = [entry['count'] for entry in formatted]
    tick_spacing = 4  # or any spacing that suits your data density

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.bar(range(len(weeks)), counts, width=0.8, color='slateblue')

    ax.set_xticks(range(0, len(weeks), tick_spacing))
    ax.set_xticklabels(weeks[::tick_spacing], rotation=45, ha='right', fontsize=8)

    ax.set_ylabel('Count')
    ax.set_title('Weekly Series Count', fontsize=10)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return buf


def generate_target(series):
    coords = [(i.x, i.y) for i in series.shot]  # FIXME: ensure shots are in order
    fig, ax = plt.subplots(figsize=(6, 5))
    n = 11
    xscale = 2.2
    ring = Circle((300, 250), radius=int(0.5 * 59.5 * xscale), fill=True, facecolor='black', edgecolor='black', linewidth=1)
    ax.add_patch(ring)
    xcal = 0
    ycal = 0

    for i in [5, 11.5, 27.5, 43.5, 59.5, 75.5, 91.5, 107.5, 123.5, 139.5, 155.5]:
        if n > 7:
            edgecolor = 'white'
        else:
            edgecolor = 'black'

        ring = Circle((300, 250), radius=int(0.5 * i * xscale), fill=False, edgecolor=edgecolor, linewidth=1)
        ax.add_patch(ring)
        n -= 1

    # Plot each shot as a circle
    num = 0
    for (x, y) in coords:
        num += 1
        circle = Circle((x + xcal, y + ycal), radius=9, fill=True, facecolor='yellow', edgecolor='black', linewidth=1)
        ax.add_patch(circle)
        ax.annotate(str(num), (x + xcal, y + ycal), color='blue', fontsize=7, ha='center', va='center')

    ax.set_xlim(0, 600)
    ax.set_ylim(0, 500)
    ax.set_aspect('equal', adjustable='box')
    ax.axes.invert_yaxis()
    ax.axis('off')  # Turn off the axis
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return buf