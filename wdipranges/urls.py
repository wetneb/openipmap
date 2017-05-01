"""iplocator URL Configuration

"""
from django.conf.urls import url
from .views import locate_api, render_tile, slippy_map

urlpatterns = [
    url(r'^locate', locate_api, name='locate_api'),
    url(r'^iptile-(?P<zoom>\d+)-(?P<x>\d+)-(?P<y>\d+).svg', render_tile, name='render_tile'),
    url(r'^$', slippy_map, name='slippy_map'),
]
