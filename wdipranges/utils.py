import re
import netaddr

q_re = re.compile(r'(<?https?://www.wikidata.org/(entity|wiki)/)?(Q[0-9]+)>?')

def to_q(url):
    """
    Normalizes a Wikidata item identifier

    >>> to_q('Q1234')
    u'Q1234'
    >>> to_q('<http://www.wikidata.org/entity/Q801> ')
    u'Q801'
    >>> to_q('<http://www.wikidata.org/wiki/Q801> ')
    u'Q801'
    """
    if type(url) != str:
        return
    match = q_re.match(url.strip())
    if match:
        return match.group(3)

def nice_ip(ip):
    """
    Takes an IP address and represents it in IPv4 if applicable
    """
    nice = netaddr.IPAddress(str(ip))
    if nice.is_ipv4_mapped():
        nice = nice.ipv4()
    return str(nice)

