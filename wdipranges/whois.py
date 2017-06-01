"""
This file is largely taken from
https://github.com/whym/whois-gateway
BSD license
"""

from ipwhois import IPWhois, WhoisLookupError
from six.moves import urllib
import requests
import json

PROVIDERS = {
    'ARIN': lambda x: 'http://whois.arin.net/rest/ip/' + urllib.parse.quote(x),
    'RIPENCC': lambda x: 'https://apps.db.ripe.net/search/query.html?searchtext=%s#resultsAnchor' % urllib.parse.quote(x),
    'AFRINIC': lambda x: 'http://afrinic.net/cgi-bin/whois?searchtext=' + urllib.parse.quote(x),
    'APNIC': lambda x: 'http://wq.apnic.net/apnic-bin/whois.pl?searchtext=' + urllib.parse.quote(x),
    'LACNIC': lambda x: 'http://lacnic.net/cgi-bin/lacnic/whois?lg=EN&amp;query=' + urllib.parse.quote(x)
}

FIELDS_ORDER = [
    'name',
    'description',
    'address',
    'city',
    'country',
    'created',
]

def lookup_whois(ip):
    """
    Lookup an IP address
    """
    w = IPWhois(str(ip))
    r = w.lookup_whois()
    registry = r.get('asn_registry', '').upper()
    if registry in PROVIDERS:
        r['source_url'] = PROVIDERS[registry](ip)
    return r

def match_with_whois(ip, known_ranges):
    """
    Performs a WHOIS query and returns
    the list of WHOIS ranges that are
    not present in known_ranges.
    These are good candidates for import
    in Wikidata.
    """
    whois = lookup_whois(ip)
    known = set(
        str(rng['cidr']) for rng in known_ranges)
    new_ranges = list(filter(lambda net: not set(net['cidr'].split(', ')) & known,
        whois['nets']))
    fetch_reconciled_proposals(new_ranges)
    return map(render_whois_candidate, new_ranges)

def render_whois_candidate(candidate):
    """
    Orders the fields of a WHOIS candidate
    for rendering in a template
    """
    result = []
    for field in FIELDS_ORDER:
        val = candidate.get(field)
        if val:
            result.append((field, val))
    return {
        'cidr':candidate.get('cidr'),
        'created':candidate.get('created'),
        'metadata':result,
        'recon':candidate.get('recon'),
    }

def fetch_reconciled_proposals(candidates):
    """
    Uses the reconciliation API to retrieve QID proposals
    for a given WHOIS candidate
    """
    if not candidates:
        return
    queries = {}
    for idx, candidate in enumerate(candidates):
        queries[str(idx)] = {
            'query':candidate.get('description', ''),
            'type':'Q43229', # organization
            'type_strict':'should', # not used
            'properties':[{'pid':'P17','v':candidate.get('country','')}]
        }
    r = requests.get('https://tools.wmflabs.org/openrefine-wikidata/en/api',
        {'queries':json.dumps(queries)})
    js = r.json()
    # Put back the reconciliation results in the candidates
    for idx, candidate in enumerate(candidates):
        candidates[idx]['recon'] = js.get(str(idx))['result']

