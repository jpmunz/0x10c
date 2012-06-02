import unittest
from simulator.memory import Memory,RAM, InvalidMemoryAccess, InvalidMemoryValue

class TestRAM(unittest.TestCase):

    def test_memory_access(self):
        memory = Memory(16)

        memory[0x0] = 0x1affff
        self.assertEqual(memory[0x0], 0xffff)

        self.assertRaisesRegexp(InvalidMemoryValue, 'foo', memory.__setitem__, 0, 'foo')

    def test_ram_access(self):
        max_address = 0xff
        ram = RAM(16, max_address)

        ram[max_address] = 77

        self.assertEqual(ram[max_address], 77)
        self.assertEqual(ram[0xaa], 0)

        self.assert_invalid_memory_access(ram, -1)
        self.assert_invalid_memory_access(ram, max_address + 1)

    def assert_invalid_memory_access(self, memory, key):
        address = "%#x" % key

        self.assertRaisesRegexp(InvalidMemoryAccess, address, memory.__getitem__, key)
        self.assertRaisesRegexp(InvalidMemoryAccess, address, memory.__setitem__, key, 0)

    def test_get_memory_dump(self):
        ram = RAM(16, 0xfff)

        ram[0x0000] = 0x7c01
        ram[0x0007] = 0xaaaa
        ram[0x0017] = 0x8463

        expected_dump = [
            "0000: 7c01 0000 0000 0000 0000 0000 0000 aaaa",
            "0010: 0000 0000 0000 0000 0000 0000 0000 8463",
        ]

        self.assertEqual(ram.get_memory_dump(), expected_dump)
        self.assertEqual(str(ram), "\n".join(expected_dump))



if __name__ == '__main__':
    unittest.main()
