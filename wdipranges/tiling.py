import math
from netaddr import IPNetwork
from netaddr import IPRange

# Max 2D X or Y coordinate
max_2d_coord = 1<<16
# We have 2^32 IP addresses to display on a 2D square,
# So we use 2^16 as length for each side.

# Taken from https://en.wikipedia.org/wiki/Hilbert_curve
def to_hilbert(pos, n):
    size = 1<<n
    x = 0
    y = 0
    remaining = pos
    for k in range(0,n):
        rx = 1 & (remaining >> 1)
        ry = 1 & (remaining ^ rx)
        s = 1 << k
        x, y = hilbert_rot(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        remaining = remaining >> 2
    return x, y

def hilbert_rot(size, x, y, rx, ry):
    if ry == 0:
        if rx == 1:
            x = size-1 - x
            y = size-1 - y
        return y, x
    return x, y

def from_hilbert(x, y, n):
    rx = 0
    ry = 0
    dist = 0
    for k in range(n-1,-1,-1):
        s = 1 << k
        rx = int((x & s) > 0)
        ry = int((y & s) > 0)
        dist += s*s*((3*rx) ^ ry)
        x, y = hilbert_rot(s, x, y, rx, ry)
    return dist

def ip_range_to_xyz(ip_network):
    """
    Converts an IP range to a tile coordinate (x,y,z)
    """
    if type(ip_network) == str:
        ip_network = IPNetwork(ip_network)
    if ip_network.prefixlen % 2:
        raise ValueError('Odd prefixlen: no associated tile')

    z = int(ip_network.prefixlen/2)
    shift = 16 - z
    path_length = int(ip_network.ip) >> (2*shift)
    x, y = to_hilbert(path_length, z)
    return (x << shift), (y << shift), z


def xyz_to_ip_range(tup):
    """
    Converts tile coordinates and zoom to an IP range
    """
    x, y, z = tup
    ip = IPNetwork('0.0.0.0/0')
    shift = 16 - z
    ip.value = from_hilbert(x >> shift, y >> shift, z) << (2*shift)
    ip.prefixlen = 2*z
    return ip

def ip_to_xy(ip):
    ipnetwork = IPRange(ip,ip).cidrs()[0]
    x,y,z = ip_range_to_xyz(ipnetwork)
    return (x,y)
