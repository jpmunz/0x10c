import unittest
import glob
import os
from simulator import specifications as specs
from assembler.assembler import assemble, parse_line, AssemblerSyntaxError, InvalidOperation, ValueOutOfRange, InvalidValueReference

class TestAssembler(unittest.TestCase):

    def test_assemble_examples(self):
        path = os.path.join(__file__, "../../../examples/")

        for assembly_file in glob.glob(os.path.join(path, '*.' + specs.ASSEMBLER_FILE_EXT)):
            f = open(assembly_file)
            program = f.readlines()
            f.close()

            machine_file = assembly_file[:assembly_file.find(specs.ASSEMBLER_FILE_EXT)] + specs.MACHINE_FILE_EXT

            expected_output = []
            f = open(machine_file)
            for line in f:
                expected_output.append("%#x" % int(line.strip(), base=16))
            f.close()

            code = assemble(program)

            self.assertEqual(code, expected_output, "Assembled output of example file %s did not match %s" % (assembly_file, machine_file))


    def test_syntax_errors(self):
        self.assertRaisesRegexp(AssemblerSyntaxError, "closing bracket", parse_line, "SET [0x001 + A], A")

        self.assertRaisesRegexp(InvalidOperation, "FOO", parse_line, "FOO B, 0x1")
        self.assertRaisesRegexp(ValueOutOfRange, "0x10000", parse_line, "SET B, 0x10000")

        self.assertRaises(AssemblerSyntaxError, assemble, ["SET"])
        self.assertRaises(AssemblerSyntaxError, assemble, ["SET A,"])
        self.assertRaises(AssemblerSyntaxError, assemble, ["SET A, 0x10000"])

    def test_assemble_label_lookup(self):
        program = [
            ':loop SET A, B',
            '; commented line',
            'JSR loop'
        ]

        code = assemble(program)
        self.assertEqual(code[1], hex((0x1f << 10) + (0x1 << 4)))
        self.assertEqual(code[2], hex(0))

        # Push the label down by 3 words
        program = ['SET 0x1000, 0x1000'] + program
        code = assemble(program)
        self.assertEqual(code[4], hex((0x1f << 10) + (0x1 << 4)))
        self.assertEqual(code[5], hex(0x3))

        # Invalid lookup
        self.assertRaisesRegexp(InvalidValueReference, 'foo', assemble, ['JSR foo'])

    def test_parse_line(self):

        # Test a comment
        self.assertTrue(parse_line("    ;commented line SET A, 0x10") is None)

        # register, literal value
        ins = parse_line(":sub SET A, 0x10")
        self.check_parsed_instruction(ins, label='sub', op_code=0x01, \
                value_code_a=0x00, value_code_b=0x30, additional_words=[])

        # [register], [next word]
        ins = parse_line("ADD [C], [0x1000]")
        self.check_parsed_instruction(ins, op_code=0x02, \
                value_code_a=0xa, value_code_b=0x1e, additional_words=[int(0x1000)])

        # POP, PEEK
        ins = parse_line("SUB POP, PEEK")
        self.check_parsed_instruction(ins, op_code=0x03, \
                value_code_a=0x18, value_code_b=0x19, additional_words=[])

        # SP, PC
        ins = parse_line("MUL SP, PC")
        self.check_parsed_instruction(ins, op_code=0x04, \
                value_code_a=0x1b, value_code_b=0x1c, additional_words=[])

        # O, literal value
        ins = parse_line("DIV O, 0x1f")
        self.check_parsed_instruction(ins, op_code=0x05, \
                value_code_a=0x1d, value_code_b=0x3f, additional_words=[])

        # PUSH, next word (literal)
        ins = parse_line("MOD PUSH, 0xaa")
        self.check_parsed_instruction(ins, op_code=0x06, \
                value_code_a=0x1a, value_code_b=0x1f, additional_words=[int(0xaa)])

        # [next word + register], [next word + register]
        ins = parse_line("SHL [0x1001+X], [0x1002+J]")
        self.check_parsed_instruction(ins, op_code=0x07, \
                value_code_a=0x13, value_code_b=0x17, additional_words=[int(0x1001), int(0x1002)])

        # Non-basic instruction
        ins = parse_line("JSR 0x1000")
        self.assertTrue(ins.value_code_b is None)
        self.assertFalse(ins.is_basic)
        self.assertEqual(ins.op_code, 0x01)


    def check_parsed_instruction(self, ins, is_basic=True, **kwargs):
        for arg in kwargs:
            if kwargs[arg]:
                self.assertEqual(getattr(ins, arg), kwargs[arg], "%s did not match, got %s instead of %s" % (arg, getattr(ins, arg), kwargs[arg]))

if __name__ == '__main__':
    unittest.main()
