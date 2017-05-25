"""iplocator URL Configuration

"""
from django.conf.urls import url
from .views import locate_api, reverse_api, render_tile, render_ip_lookup, slippy_map
from .views import render_whois, push_ranges_to_wikidata

urlpatterns = [
    url(r'^api/locate', locate_api, name='locate_api'),
    url(r'^api/reverse', reverse_api, name='reverse_api'),
    url(r'^ip-lookup', render_ip_lookup, name='render_ip_lookup'),
    url(r'^push_to_wd', push_ranges_to_wikidata, name='push_ranges_to_wikidata'),
    url(r'^whois', render_whois, name='render_whois'),
    url(r'^iptile/(?P<zoom>-?\d+)/(?P<x>\d+)/(?P<y>\d+).svg', render_tile, name='render_tile'),
    url(r'^$', slippy_map, name='slippy_map'),
]
