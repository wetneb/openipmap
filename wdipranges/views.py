from django.shortcuts import render
from django.http import HttpResponse, Http404
from .models import IPRange
from .forms import LocateForm, TileForm
from .tiling import ip_range_to_xyz, xyz_to_ip_range
from .tiling import max_2d_coord
from .tiling import ip_to_xy
from jsonview.decorators import json_view
from jsonview.exceptions import BadRequest
from ipware.ip import get_real_ip
from netaddr import IPNetwork
import svgwrite
import math

def ip_fallback(request):
    """
    Gets the IP specified by the user in the parameters,
    or fall back on its actual IP address
    """
    params = request.POST if request.method == 'POST' else request.GET

    # if IP is not given, use the one in the request
    request_ip = get_real_ip(request)
    if 'ip' not in params and request_ip is not None:
        params = params.copy()
        params['ip'] = request_ip

    locate_form = LocateForm(params)
    if locate_form.is_valid():
        return locate_form.cleaned_data['ip']

@json_view
def locate_api(request):
    ip = ip_fallback(request)
    if not ip:
        raise BadRequest("No IP provided")

    coords = ip_to_xy(ip)
    qs = IPRange.objects.filter(cidr__net_contains=ip)[:64]
    return {
        'ip':str(ip),
        'coordinates' : {
            'x': coords[0],
            'y': coords[1],
        },
        'results':[rng.json() for rng in qs]
    }

def slippy_map(request):
    ip = ip_fallback(request)

    context = {
        'ip': ip,
        'coords': ip_to_xy(ip) if ip else None,
        'map_size': max_2d_coord,
        'min_zoom': -int(math.log((max_2d_coord / 1024),2)+1)
    }
    return render(request, 'wdipranges/slippy.html', context)

def render_tile(request, zoom, x, y):
    tile_form = TileForm({'zoom':zoom,'x':x,'y':y})
    if not tile_form.is_valid():
        raise Http404("Invalid parameters")

    # Convert x y z to an IP range
    zoom = tile_form.cleaned_data['zoom']
    origx = tile_form.cleaned_data['x'] << (16-zoom)
    origy = tile_form.cleaned_data['y'] << (16-zoom)
    if origx < 0 or origy < 0 or origx >= max_2d_coord or origy >= max_2d_coord:
        raise Http404('Tile is out of bounds')

    bounding_range = xyz_to_ip_range((origx, origy, zoom))

    # Request all supernets
    supernets = IPRange.objects.filter(
        cidr__net_contains=str(bounding_range)).order_by('level')

    # Request the current range
    current_range = IPRange.objects.filter(cidr=str(bounding_range))

    # Request all ranges within that range, up to a certain zoom level
    ranges = IPRange.objects.filter(
        cidr__net_contained=str(bounding_range),
        level__lt=bounding_range.prefixlen + 11).order_by('level')

    # All the ranges we need to display
    ranges_to_display = list(supernets)+list(current_range)+list(ranges)

    # Draw the SVG
    size = 256
    svg_doc = svgwrite.Drawing(size=(size,size))
    scale = float(size) / (1 << (16 - zoom))

    # background color
    rect = svg_doc.rect(insert = (0, 0),
                size=(size,size),
                fill = "rgb(200,200,200)")
    svg_doc.add(rect)


    for rng in ranges_to_display:
        if rng.level % 2 == 0:
            # even prefix lengths are represented by squares
            x, y, z = ip_range_to_xyz(str(rng.cidr))
            size = scale*(1 << (16 - z))
            sizex = size
            sizey = size
        else:
            # odd prefix lengths are represented by two concatenated
            # squares
            z = rng.level
            size = scale*(1 << (16 - int((z+1)/2)))

            # split the IP network in two
            first_block = IPNetwork(str(rng.cidr))
            first_block.prefixlen = first_block.prefixlen+1
            next_block = IPNetwork(str(first_block))
            next_block.value = first_block.value + (1 << (32 - first_block.prefixlen))

            # compute the coordinates of both parts
            x1, y1, z1 = ip_range_to_xyz(str(first_block))
            x2, y2, z2 = ip_range_to_xyz(str(next_block))

            # compute the coordinates of the bounding rectangle
            x = min(x1,x2)
            y = min(y1,y2)

            # at least one of (x1,x2) (y1,y2) have to agree
            if x1 == x2:
                # vertical rectangle
                sizex = size
                sizey = 2*size
            elif y1 == y2:
                sizex = 2*size
                sizey = size

        rect = svg_doc.rect(insert = (scale*(x-origx), scale*(y-origy)),
                    size=(sizex,sizey),
                    stroke_width = "1",
                    stroke = "black",
                    fill = "rgb(255,0,255)",
                    fill_opacity="0.4")
        svg_doc.add(rect)

    return HttpResponse(svg_doc.tostring(), content_type="image/svg+xml")

