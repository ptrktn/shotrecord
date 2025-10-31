import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.ticker import MaxNLocator
from io import BytesIO
import numpy as np


def weekly_series_plot(formatted):

    weeks = [entry['week'] for entry in formatted]
    counts = [entry['count'] for entry in formatted]
    tick_spacing = 4  # or any spacing that suits your data density

    fig, ax = plt.subplots(figsize=(10, 3))

    x = np.arange(len(weeks))  # use x-axis as an index
    ax.bar(x, counts, width=0.8, color='slateblue')

    # Ordinary Least Squares fit (linear regression)
    slope = intercept = None
    if len(x) >= 2:
        slope, intercept = np.polyfit(x, counts, 1)
        if slope < -0.2:
            color = 'red'
        elif slope < -0.1:
            color = 'orange'
        else:
            color = 'green'

        x_line = np.linspace(0, x[-1], 100)
        y_line = intercept + slope * x_line
        ax.plot(x_line, y_line, '-', color=color, linewidth=0.5, label='trend')

        # show slope value on the plot
        # ax.annotate(f"Slope: {slope:.2f} counts/index",
        #             xy=(0.98, 0.95), xycoords='axes fraction',
        #             ha='right', va='top', fontsize=9, color='red',
        #             bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))

    ax.set_xticks(range(0, len(weeks), tick_spacing))
    ax.set_xticklabels(weeks[::tick_spacing],
                       rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Count')
    ax.set_title('Weekly Series Count', fontsize=10)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.ylim(bottom=0)  # Hide negative y-values

    # optional legend if regression shown
    if slope is not None:
        ax.legend(loc='upper left', fontsize=8)

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return buf


def generate_target(series):
    # FIXME: ensure shots are in order
    shotdata = [(i.x, i.y, i.shotnum) for i in series.shot]
    fig, ax = plt.subplots(figsize=(6, 5))
    xscale = 2.2  # FIXME: this should be a parameter

    x0 = 10
    y0 = 10
    lf = 20
    ax.annotate(series.description, (x0, y0), color='black',
                fontsize=8, ha='left', va='center')
    y0 += lf
    ax.annotate(series.created_at.strftime('%Y-%m-%d %H:%M'), (x0, y0), color='black',
                fontsize=8, ha='left', va='center')
    y0 += lf
    ax.annotate(f"Points: {series.total_points:.1f} Time: {series.total_t:.1f}", (x0, y0), color='black',
                fontsize=8, ha='left', va='center')
    y0 += lf

    # TODO: Add precision metric (requires calibration, a.u. not suitable)

    pct = next((m.value for m in series.metric if m.name ==
               'ConsistencyPct'), None)
    if pct:
        ax.annotate(f"Consistency: {pct:.1f}%", (x0, y0), color='black',
                    fontsize=8, ha='left', va='center')
        y0 += lf

    for shot in series.shot:
        ax.annotate(f"Shot {shot.shotnum}: {shot.points:.1f}", (x0, y0), color='black',
                    fontsize=8, ha='left', va='center')
        y0 += lf

    ring = Circle((300, 250), radius=int(0.5 * 59.5 * xscale),
                  fill=True, facecolor='black', edgecolor='black', linewidth=1)
    ax.add_patch(ring)

    n = 11
    for i in [5, 11.5, 27.5, 43.5, 59.5, 75.5, 91.5, 107.5, 123.5, 139.5, 155.5]:
        if n > 7:
            edgecolor = 'white'
        else:
            edgecolor = 'black'

        ring = Circle((300, 250), radius=int(0.5 * i * xscale),
                      fill=False, edgecolor=edgecolor, linewidth=1)
        ax.add_patch(ring)
        n -= 1

    # Plot the Main Point of Impact (MPI)
    x0 = next((m.value for m in series.metric if m.name == 'MPI_x'), None)
    y0 = next((m.value for m in series.metric if m.name == 'MPI_y'), None)
    if x0 and y0:
        delta = 50
        x0 = int(x0)
        y0 = int(y0)
        x = [(x0 - delta), (x0 + delta)]
        y = [(y0), (y0)]
        ax.plot(x, y, linewidth=0.8, color='orange')
        x = [(x0), (x0)]
        y = [(y0 - delta), (y0 + delta)]
        ax.plot(x, y, linewidth=0.8, color='orange')

    # Plot each shot as a circle
    for (x, y, n) in shotdata:
        circle = Circle((x, y), radius=9, fill=True,
                        facecolor='yellow', edgecolor='black', linewidth=1)
        ax.add_patch(circle)
        if n > 0:
            ax.annotate(str(n), (x, y), color='blue',
                        fontsize=7, ha='center', va='center')

    ax.set_xlim(0, 600)
    ax.set_ylim(0, 500)
    ax.set_aspect('equal', adjustable='box')
    ax.axes.invert_yaxis()
    ax.axis('off')  # Turn off the axis
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return buf


def median_points(series):
    data = []

    for s in series:
        points = []
        for shot in s.shot:
            points.append(shot.points)

        data.append(np.median(np.array(points)))

    return data
