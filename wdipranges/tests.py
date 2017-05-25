from django.test import TestCase
import unittest
from .tiling import xyz_to_ip_range
from .tiling import ip_range_to_xyz
from .whois import lookup_whois

class XyzHilbertTest(unittest.TestCase):
    def test_inverse(self):
        for val in ['::ffff:129.199.0.0/112',
                    '::ffff:0.0.0.0/96',
                    '::ffff:129.199.1.1/128']:
            self.assertEqual(val,
                    str(xyz_to_ip_range(ip_range_to_xyz(val))))

    def test_odd(self):
        with self.assertRaises(ValueError):
            ip_range_to_xyz('246.23.128.0/17')

class WhoisTest(unittest.TestCase):
    def test_ipv4(self):
        w = lookup_whois('94.118.162.96')
        self.assertEqual(w['asn_registry'].upper(), 'RIPENCC')
        self.assertEqual(w['asn_cidr'], '94.118.0.0/16')

