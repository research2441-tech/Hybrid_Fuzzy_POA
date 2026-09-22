"""IEEE 33-bus radial distribution test feeder used by the manuscript.

Loads are standard benchmark values in kW/kVAr. Branch numbering follows the
common 33-bus data convention. Five normally open tie branches are included.
"""

from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Branch:
    index: int
    fbus: int
    tbus: int
    r_ohm: float
    x_ohm: float
    normally_open: bool = False

# bus, P(kW), Q(kVAr)
LOAD_DATA = np.array([
    [1,0,0],[2,100,60],[3,90,40],[4,120,80],[5,60,30],[6,60,20],
    [7,200,100],[8,200,100],[9,60,20],[10,60,20],[11,45,30],[12,60,35],
    [13,60,35],[14,120,80],[15,60,10],[16,60,20],[17,60,20],[18,90,40],
    [19,90,40],[20,90,40],[21,90,40],[22,90,40],[23,90,50],[24,420,200],
    [25,420,200],[26,60,25],[27,60,25],[28,60,20],[29,120,70],[30,200,600],
    [31,150,70],[32,210,100],[33,60,40]
], dtype=float)

BRANCHES = [
    Branch(1,1,2,0.0922,0.0470), Branch(2,2,3,0.4930,0.2511),
    Branch(3,3,4,0.3660,0.1864), Branch(4,4,5,0.3811,0.1941),
    Branch(5,5,6,0.8190,0.7070), Branch(6,6,7,0.1872,0.6188),
    Branch(7,7,8,0.7114,0.2351), Branch(8,8,9,1.0300,0.7400),
    Branch(9,9,10,1.0440,0.7400), Branch(10,10,11,0.1966,0.0650),
    Branch(11,11,12,0.3744,0.1238), Branch(12,12,13,1.4680,1.1550),
    Branch(13,13,14,0.5416,0.7129), Branch(14,14,15,0.5910,0.5260),
    Branch(15,15,16,0.7463,0.5450), Branch(16,16,17,1.2890,1.7210),
    Branch(17,17,18,0.7320,0.5740), Branch(18,2,19,0.1640,0.1565),
    Branch(19,19,20,1.5042,1.3554), Branch(20,20,21,0.4095,0.4784),
    Branch(21,21,22,0.7089,0.9373), Branch(22,3,23,0.4512,0.3083),
    Branch(23,23,24,0.8980,0.7091), Branch(24,24,25,0.8960,0.7011),
    Branch(25,6,26,0.2030,0.1034), Branch(26,26,27,0.2842,0.1447),
    Branch(27,27,28,1.0590,0.9337), Branch(28,28,29,0.8042,0.7006),
    Branch(29,29,30,0.5075,0.2585), Branch(30,30,31,0.9744,0.9630),
    Branch(31,31,32,0.3105,0.3619), Branch(32,32,33,0.3410,0.5302),
    Branch(33,8,21,2.0000,2.0000,True),
    Branch(34,9,15,2.0000,2.0000,True),
    Branch(35,12,22,2.0000,2.0000,True),
    Branch(36,18,33,0.5000,0.5000,True),
    Branch(37,25,29,0.5000,0.5000,True),
]

N_BUSES = 33
SLACK_BUS = 1
NORMALLY_OPEN = [33,34,35,36,37]
NORMALLY_CLOSED = list(range(1,33))

# Candidate weak-bus-style DG locations. The manuscript does not list exact
# optimized DG buses, so the choices are exposed here instead of hidden.
DG_BUSES_3MG = [18, 25, 33]
DG_BUSES_5MG = [7, 14, 20, 25, 32]

MG_PARTITIONS_3 = {
    1: list(range(2,19)),
    2: list(range(19,26)),
    3: list(range(26,34)),
}

MG_PARTITIONS_5 = {
    1: list(range(2,8)),
    2: list(range(8,15)),
    3: list(range(15,21)),
    4: list(range(21,27)),
    5: list(range(27,34)),
}

def loads_mw_mvar(multiplier=1.0):
    """Return active/reactive load vectors in MW/MVAr indexed 1..33."""
    p = np.zeros(N_BUSES + 1)
    q = np.zeros(N_BUSES + 1)
    for bus, pk, qk in LOAD_DATA:
        p[int(bus)] = pk * multiplier / 1000.0
        q[int(bus)] = qk * multiplier / 1000.0
    return p, q

def branch_dict():
    return {b.index: b for b in BRANCHES}
