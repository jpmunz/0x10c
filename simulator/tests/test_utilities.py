import unittest
from simulator.utilities import bitmask, to_int

class TestUtilities(unittest.TestCase):

    def test_to_int(self):
        self.assertEqual(to_int(52, bases_to_try=[2,3]), 52)

        self.assertEqual(to_int('0x0020', bases_to_try=[2,5,16]), 32)
        self.assertEqual(to_int('0x0020', bases_to_try=[3,4]), None)

        self.assertEqual(to_int('0b0001', bases_to_try=[2]), 1)
        self.assertEqual(to_int('0b0100', bases_to_try=[3,4]), None)

        self.assertEqual(to_int('0b0000000000010001', bases_to_try=[2,16]), 17)

    def test_bitmask(self):
        self.assertEqual(bitmask(16), 0xffff)

if __name__ == '__main__':
    unittest.main()
