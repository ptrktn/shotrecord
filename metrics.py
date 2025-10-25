# https://copilot.microsoft.com/shares/Rn18G7JSH6GqL9XyGiRWR
import math
from itertools import combinations

def compute_metrics(shots, s_ref=50.0):
    # shots: list of (x, y) in consistent units (e.g., mm at known range)
    n = len(shots)
    xs = [p[0] for p in shots]
    ys = [p[1] for p in shots]

    mx = sum(xs) / n
    my = sum(ys) / n

    r = [math.hypot(x-mx, y-my) for x,y in shots]
    mr = sum(r) / n
    rsd = math.sqrt(sum((ri - mr)**2 for ri in r) / n)
    rms = math.sqrt(sum(ri*ri for ri in r) / n)

    # extreme spread (max center-to-center distance)
    extreme = 0.0
    for (x1,y1),(x2,y2) in combinations(shots,2):
        d = math.hypot(x1-x2, y1-y2)
        if d > extreme:
            extreme = d

    # simple consistency score: clamp to [0,100]
    consistency = max(0.0, 100.0 * (1.0 - rsd / s_ref))

    return {
        "MPI_x": mx, 
        "MPI_y": my,
        "MeanRadius": mr,
        "RadialStdDev": rsd,
        "RMS": rms,
        "ExtremeSpread": extreme,
        "ConsistencyPct": consistency
    }

# Example
# shots = [(12.3, -3.2), (11.8, -2.9), (12.7, -3.5), (11.9, -3.0)]
# print(compute_metrics(shots, s_ref=30.0))
