from django.test import TestCase
import unittest
from .tiling import xyz_to_ip_range
from .tiling import ip_range_to_xyz


class XyzHilbertTest(unittest.TestCase):
    def test_inverse(self):
        for val in ['129.199.0.0/16','0.0.0.0/0','129.199.1.1/32']:
            self.assertEqual(val,
                    str(xyz_to_ip_range(ip_range_to_xyz(val))))

    def test_odd(self):
        with self.assertRaises(ValueError):
            ip_range_to_xyz('246.23.128.0/17')
