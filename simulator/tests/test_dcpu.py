import unittest
import os
import glob
from simulator.dcpu import DCPU, read_instruction, parse_instruction, get_word_length, OpCodeNotImplemented, InvalidInstruction, InvalidValueCode, InfiniteLoopDetected
from simulator import specifications as specs

class TestDCPU(unittest.TestCase):

    def setUp(self):
        self.cpu = DCPU()

    def test_example_programs(self):
        self.run_program_file('32bitadd')
        self.assertEqual(self.cpu.RAM[0x1000], 0x2355)
        self.assertEqual(self.cpu.RAM[0x1001], 0xbcf0)

        self.assertRaises(InfiniteLoopDetected, self.run_program_file, 'basic')
        self.assertEqual(self.cpu.registers[specs.REGISTER_NAMES['X']], 0x40)

        self.run_program_file('fib')
        start_addr = 0x1000
        fib_terms = 10

        n, a, b = 0, 0, 1
        while n < fib_terms:
            self.assertEqual(self.cpu.RAM[start_addr + n], a)
            self.assertEqual(self.cpu.RAM[start_addr + n + 1], b)
            n, a, b = n + 1, b, a+b

    def run_program_file(self, program_file):
        path = os.path.join(__file__, "../../../examples/")

        f = open(os.path.join(path, program_file + '.' + specs.MACHINE_FILE_EXT))
        program = f.readlines()
        f.close()

        self.cpu.run_program(program)

        return

    def test_execute_next_instruction(self):
        self.assertFalse(self.cpu.execute_next_instruction(), "No instructions loaded, should stop")

        self.cpu.load_program([0x01])
        self.assertTrue(self.cpu.execute_next_instruction())

        self.cpu.load_program([0x9031, 0x9037])
        self.cpu.execute_next_instruction()
        self.cpu.execute_next_instruction()

        self.assertEqual(self.cpu.registers[0x03], 0x40)

    def test_set(self):
        self.assert_operation(
            specs.BasicOperations.SET,
            register1 = 0x00,
            register2 = 0x02,
            expected_cycles = 1,
            expected_result = 0x02
        )

    def test_add(self):
        self.assert_operation(
            specs.BasicOperations.ADD,
            register1 = 0xfffa,
            register2 = 0x0008,
            expected_cycles = 2,
            expected_result = 0x02,
            expected_overflow = 0x0001
        )

        self.assert_operation(
            specs.BasicOperations.ADD,
            register1 = 0x03,
            register2 = 0x02,
            expected_cycles = 2,
            expected_result = 0x05
        )

    def test_subtract(self):
        self.assert_operation(
            specs.BasicOperations.SUB,
            register1 = 0x0,
            register2 = 0xff,
            expected_cycles = 2,
            expected_result = 0xff00,
            expected_overflow = 0xffff
        )

        self.assert_operation(
            specs.BasicOperations.SUB,
            register1 = 0x03,
            register2 = 0x02,
            expected_cycles = 2,
            expected_result = 0x01
        )


    def test_multiply(self):
        self.assert_operation(
            specs.BasicOperations.MUL,
            register1 = 0x08,
            register2 = 0x02,
            expected_cycles = 2,
            expected_result = 0x10
        )

        self.assert_operation(
            specs.BasicOperations.MUL,
            register1 = 0x0,
            register2 = 0xff,
            expected_cycles = 2,
            expected_result = 0x0,
        )

        self.assert_operation(
            specs.BasicOperations.MUL,
            register1 = 0xa000,
            register2 = 0x2,
            expected_cycles = 2,
            expected_result = 0x4000,
            expected_overflow = 0x0001
        )

    def test_divide(self):
        self.assert_operation(
            specs.BasicOperations.DIV,
            register1 = 0x08,
            register2 = 0x02,
            expected_cycles = 3,
            expected_result = 0x04
        )

        self.assert_operation(
            specs.BasicOperations.DIV,
            register1 = 0x0001,
            register2 = 0x0002,
            expected_cycles = 3,
            expected_result = 0x0,
            expected_overflow = 0x8000
        )

        self.assert_operation(
            specs.BasicOperations.DIV,
            register1 = 0x08,
            register2 = 0x00,
            expected_cycles = 3,
            expected_result = 0x0
        )

    def test_modulo(self):
        self.assert_operation(
            specs.BasicOperations.MOD,
            register1 = 0x0034,
            register2 = 0x0008,
            expected_cycles = 3,
            expected_result = 0x4
        )

        self.assert_operation(
            specs.BasicOperations.MOD,
            register1 = 0x0031,
            register2 = 0x0000,
            expected_cycles = 3,
            expected_result = 0x0
        )

    def test_shift_left(self):
        self.assert_operation(
            specs.BasicOperations.SHL,
            register1 = 0x0071,
            register2 = 0x0004,
            expected_cycles = 2,
            expected_result = 0x0710
        )

        self.assert_operation(
            specs.BasicOperations.SHL,
            register1 = 0xffaa,
            register2 = 0x0008,
            expected_cycles = 2,
            expected_result = 0xaa00,
            expected_overflow = 0xff
        )

    def test_shift_right(self):
        self.assert_operation(
            specs.BasicOperations.SHR,
            register1 = 0x6600,
            register2 = 0x0008,
            expected_cycles = 2,
            expected_result = 0x0066
        )

        self.assert_operation(
            specs.BasicOperations.SHR,
            register1 = 0x55ab,
            register2 = 0x0004,
            expected_cycles = 2,
            expected_result = 0x055a,
            expected_overflow = 0xb000
        )

    def test_bitwise_and(self):
        self.assert_operation(
            specs.BasicOperations.AND,
            register1 = 0x0f0f,
            register2 = 0xafaf,
            expected_cycles = 1,
            expected_result = 0x0f0f
        )

    def test_bitwise_or(self):
        self.assert_operation(
            specs.BasicOperations.BOR,
            register1 = 0x0f0f,
            register2 = 0xafaf,
            expected_cycles = 1,
            expected_result = 0xafaf
        )

    def test_bitwise_xor(self):
        self.assert_operation(
            specs.BasicOperations.XOR,
            register1 = 0x0f00,
            register2 = 0xafaf,
            expected_cycles = 1,
            expected_result = 0xa0af
        )

    def test_if_equal(self):
        self.assert_operation(
            specs.BasicOperations.IFE,
            register1 = 0x2,
            register2 = 0x2,
            expected_cycles = 2,
            expected_result = True
        )

        self.assert_operation(
            specs.BasicOperations.IFE,
            register1 = 0x2,
            register2 = 0x1,
            expected_cycles = 3,
            expected_result = False
        )

    def test_if_not_equal(self):
        self.assert_operation(
            specs.BasicOperations.IFN,
            register1 = 0x2,
            register2 = 0x3,
            expected_cycles = 2,
            expected_result = True
        )

        self.assert_operation(
            specs.BasicOperations.IFN,
            register1 = 0x2,
            register2 = 0x2,
            expected_cycles = 3,
            expected_result = False
        )

    def test_if_greater_than(self):
        self.assert_operation(
            specs.BasicOperations.IFG,
            register1 = 0x8,
            register2 = 0x2,
            expected_cycles = 2,
            expected_result = True
        )

        self.assert_operation(
            specs.BasicOperations.IFG,
            register1 = 0x2,
            register2 = 0x8,
            expected_cycles = 3,
            expected_result = False
        )

    def test_if_bitwise_and(self):
        self.assert_operation(
            specs.BasicOperations.IFB,
            register1 = 0xf1,
            register2 = 0x01,
            expected_cycles = 2,
            expected_result = True
        )

        self.assert_operation(
            specs.BasicOperations.IFB,
            register1 = 0x0f1,
            register2 = 0xf00,
            expected_cycles = 3,
            expected_result = False
        )

    def test_jump_and_set_return(self):
        self.cpu.PC = 0x77
        self.cpu.registers[0x0] = 0xa10

        self.cpu.SP = 0xffff

        jsr = self.cpu.get_op(specs.NonBasicOperations.JSR, is_basic=False)

        jsr(self.cpu.get_value(0x0))


        self.assertEqual(self.cpu.RAM[0xfffe], 0x77)
        self.assertEqual(self.cpu.SP, 0xfffe)
        self.assertEqual(self.cpu.PC, 0xa10)
        self.assertEqual(self.cpu.cycles_ran, 2)

    def test_branching(self):
        for (instruction, word_length) in [(0xa861, 1), (0x7c01, 2), (0x7de1, 3)]:
            self.cpu.PC = 0
            self.cpu.RAM[0x0] = instruction
            op = self.cpu.get_op(specs.BasicOperations.IFE, True)
            op(self.cpu.get_value(0x20), self.cpu.get_value(0x21))
            self.assertEqual(self.cpu.PC, word_length)

    def test_get_word_length(self):
        self.assertEqual(get_word_length(0xa861), 1)
        self.assertEqual(get_word_length(0x7c01), 2)
        self.assertEqual(get_word_length(0x7de1), 3)

    def assert_operation(self, operation, register1, register2, expected_cycles, expected_result, expected_overflow=0x0):
        self.cpu.PC = 0
        self.cpu.RAM[0x0] = 0xa861
        self.cpu.registers[0x0] = register1
        self.cpu.registers[0x1] = register2

        self.cpu.get_op(operation, True)(self.cpu.get_value(0x0), self.cpu.get_value(0x1))

        if operation in [specs.BasicOperations.IFE, specs.BasicOperations.IFN, specs.BasicOperations.IFG, specs.BasicOperations.IFB]:
            if expected_result:
                self.assertEqual(self.cpu.PC, 0)
            else:
                self.assertEqual(self.cpu.PC, 1)
        else:
            self.assertEqual(self.cpu.registers[0x0], expected_result)

        self.assertEqual(self.cpu.O, expected_overflow)
        self.assertEqual(self.cpu.cycles_ran, expected_cycles)

        self.cpu.O = 0x0
        self.cpu.cycles_ran = 0

    def test_get_value(self):

        for register in specs.REGISTERS.keys() + specs.SPECIAL_REGISTERS.keys():
            self.assert_value_retrieval(self.cpu.registers, register, register)

            if register in specs.REGISTERS:
                self.assert_getting_register_reference(register)
                self.assert_getting_register_reference_next_word(register)

        # POP
        self.cpu.SP = 0xfffe
        self.assert_value_retrieval(self.cpu.RAM, 0xfffe, 0x18)
        self.assertEqual(self.cpu.SP, 0xffff)

        # PEEK
        self.cpu.SP = 0x7777
        self.assert_value_retrieval(self.cpu.RAM, 0x7777, 0x19)
        self.assertEqual(self.cpu.SP, 0x7777)

        # PUSH
        self.cpu.SP = 0x2002
        self.assert_value_retrieval(self.cpu.RAM, 0x2001, 0x1a)
        self.assertEqual(self.cpu.SP, 0x2001)

        # [next word]
        self.cpu.PC = 0x0
        self.cpu.RAM[0x0] = 0x6655
        self.assert_value_retrieval(self.cpu.RAM, 0x6655, 0x1e)
        self.assertEqual(self.cpu.PC, 0x1)

        # Literals
        self.cpu.PC = 0x0
        self.cpu.RAM[0x0] = 0x4444
        value = self.cpu.get_value(0x1f)
        self.assertEqual(value.read(), 0x4444)
        value.write(0x0) # Fail silently

        for literal in range(0x20, 0x3f):
            self.assert_getting_literal(literal)

        self.assertRaisesRegexp(InvalidValueCode, '0xff', self.cpu.get_value, 0xff)

        # "All values that read a word (0x10-0x17, 0x1e, and 0x1f) take 1 cycle to look up. The rest take 0 cycles", so loading all posible values should cost 10 cycles
        self.assertEqual(self.cpu.cycles_ran, 10)

    def assert_getting_literal(self, value_code):
        value = self.cpu.get_value(value_code)
        self.assertEqual(value.read(), value_code - 0x20)
        value.write(0x0) # Fail silently

    def assert_getting_register_reference_next_word(self, value_code):
        self.cpu.PC = 0x0
        self.cpu.RAM[0x0] = 0x01
        self.cpu.registers[value_code] = 0x1000
        self.assert_value_retrieval(self.cpu.RAM, 0x1001, value_code + 0x10)

    def assert_getting_register_reference(self, value_code):
        self.cpu.registers[value_code] = 0x1000
        self.assert_value_retrieval(self.cpu.RAM, 0x1000, value_code + 0x08)

    def assert_value_retrieval(self, memory, addr, value_code):
        memory[addr] = 0xbeef
        value = self.cpu.get_value(value_code)
        self.assertEqual(value.read(), 0xbeef, "Failed on retrieving value code %x, read %x instead of %x" % (value_code, value.read(), 0xbeef))

        value.write(0xfeeb)

        self.assertEqual(memory[addr], 0xfeeb, "Failed on write for value code %x" % value_code)

    def test_get_op(self):
        self.assertRaisesRegexp(OpCodeNotImplemented, '0x309', self.cpu.get_op, 0x309, is_basic=False)

        self.assertTrue(callable(self.cpu.get_op(0x01, is_basic=True)))
        self.assertTrue(callable(self.cpu.get_op(0b000000000000001, is_basic=False)))

    def test_get_next_word(self):
        self.cpu.RAM[0x0] = 0xaa
        self.cpu.RAM[0x1] = 0xbb

        self.assertEqual(self.cpu.get_next_word(), 0xaa)
        self.assertEqual(self.cpu.get_next_word(), 0xbb)
        self.assertEqual(self.cpu.cycles_ran, 2)

    def test_reset(self):
        self.cpu.cycles_ran = 12
        self.cpu.registers[0x0] = 0xff
        self.cpu.registers[0x6] = 0xff

        self.cpu.PC = 0xaa
        self.cpu.SP = 0x0001
        self.cpu.O = 0xffff

        self.cpu.RAM[0x1000] = 0xff

        self.cpu.reset()

        self.assertEqual(self.cpu.cycles_ran, 0)
        self.assertEqual(len(self.cpu.RAM), 0)

        for register in specs.REGISTERS.keys() + specs.SPECIAL_REGISTERS.keys():
            if register == specs.SPECIAL_REGISTER_NAMES['SP']:
                self.assertEqual(self.cpu.registers[register], specs.MAX_RAM_ADDRESS)
            else:
                self.assertEqual(self.cpu.registers[register], 0)

    def test_load_program(self):
        self.assert_instructions_loaded([2,4,8,16])
        self.assert_instructions_loaded([0x73, 0xaa])

    def assert_instructions_loaded(self, instructions):
        self.cpu.load_program(instructions)

        self.assertEqual(len(self.cpu.RAM), len(instructions))

        for address in sorted(self.cpu.RAM):
            self.assertEqual(self.cpu.RAM[address], instructions[address])

    def test_parse_instruction(self):
        self.assert_parsed_instruction(0b0001111000000011, op_code=3, a=32, b=7)
        self.assert_parsed_instruction(0b0001111000000000, op_code=32, a=7, b=None)

    def assert_parsed_instruction(self, instruction, op_code, a, b):
        parsed = parse_instruction(instruction)

        self.assertEqual(parsed[0], op_code)
        self.assertEqual(parsed[1], a)
        self.assertEqual(parsed[2], b)

    def test_read_instruction(self):
        self.assertEqual(read_instruction(0x0020), 32)
        self.assertEqual(read_instruction('7c01'), 31745)
        self.assertEqual(read_instruction('0020'), 32)
        self.assertEqual(read_instruction('1001'), 4097)

        self.assertRaisesRegexp(InvalidInstruction, 'qqrr', read_instruction, 'qqrr')
        self.assertRaisesRegexp(InvalidInstruction, 'not 16-bit', read_instruction, '0xffaaa')
        self.assertRaisesRegexp(InvalidInstruction, 'not 16-bit', read_instruction, 'ffaaa')
        self.assertRaisesRegexp(InvalidInstruction, 'not 16-bit', read_instruction, '10001000')

    def test_get_state(self):
        expected_output = 'Ran 0 cyles\n\nPC: 0x0000\nSP: 0xffff\nO:  0x0000\n\nRegister values\n---------------\nA: 0x0000\nB: 0x0000\nC: 0x0000\nX: 0x0000\nY: 0x0000\nZ: 0x0000\nI: 0x0000\nJ: 0x0000\n\nMemory dump\n-----------\n'

        self.assertEqual(str(self.cpu), expected_output)
if __name__ == '__main__':
    unittest.main()
