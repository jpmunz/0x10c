import operator
import specifications as specs

from memory import Memory, RAM
from utilities import bitmask, to_int

class Value(object):
    def __init__(self, getter, setter):
        self.read = getter
        self.write = setter

class DCPU(object):
    HEX_OUTPUT_FORMAT = "%#06x"
    MAX_VAL = bitmask(specs.WORD_SIZE)

    def __init__(self):
        self.cycles_ran = 0
        self.registers = Memory(specs.WORD_SIZE)

        self.reset_registers()

        self.RAM = RAM(specs.WORD_SIZE, specs.MAX_RAM_ADDRESS)

        self.basic_ops = {
            specs.BasicOperations.SET: self.set,
            specs.BasicOperations.ADD: self.add,
            specs.BasicOperations.SUB: self.subtract,
            specs.BasicOperations.MUL: self.multiply,
            specs.BasicOperations.DIV: self.divide,
            specs.BasicOperations.MOD: self.modulo,
            specs.BasicOperations.SHL: self.shift_left,
            specs.BasicOperations.SHR: self.shift_right,

            specs.BasicOperations.AND:
                lambda a, b: self.boolean_operation(operator.and_, a, b),

            specs.BasicOperations.BOR:
                lambda a, b: self.boolean_operation(operator.or_, a, b),

            specs.BasicOperations.XOR:
                lambda a, b: self.boolean_operation(operator.xor, a, b),

            specs.BasicOperations.IFE:
                lambda a, b: self.if_condition(operator.eq, a, b),

            specs.BasicOperations.IFN:
                lambda a, b: self.if_condition(operator.ne, a, b),

            specs.BasicOperations.IFG:
                lambda a, b: self.if_condition(operator.gt, a, b),

            specs.BasicOperations.IFB:
                lambda a, b: self.if_condition(operator.and_, a, b),
        }

        self.non_basic_ops = {
            specs.NonBasicOperations.JSR: self.jump_and_set_return,
        }


    def cycles(num_cycles):
        '''
        Decorator used to specify the number of cycles
        taken by a function
        '''

        def cycle_decorator(fn):
            def wrapper(self, *args, **kwargs):
                self.cycles_ran += num_cycles

                return fn(self, *args, **kwargs)
            return wrapper

        return cycle_decorator

    '''
    Helper functions to access the special register values: SP, PC, 0
    '''

    @property
    def PC(self):
        return self.registers[specs.SPECIAL_REGISTER_NAMES['PC']]

    @PC.setter
    def PC(self, value):
        self.registers[specs.SPECIAL_REGISTER_NAMES['PC']] = value

    @property
    def SP(self):
        return self.registers[specs.SPECIAL_REGISTER_NAMES['SP']]

    @SP.setter
    def SP(self, value):
        self.registers[specs.SPECIAL_REGISTER_NAMES['SP']] = value

    @property
    def O(self):
        return self.registers[specs.SPECIAL_REGISTER_NAMES['O']]

    @O.setter
    def O(self, value):
        self.registers[specs.SPECIAL_REGISTER_NAMES['O']] = value

    def reset_registers(self):
        '''
        Set all registers to default values
        '''

        self.registers.clear()
        self.SP = specs.MAX_RAM_ADDRESS

    def reset(self):
        '''
        Set CPU to clean state
        '''

        self.cycles_ran = 0
        self.reset_registers()
        self.RAM.clear()

    def load_program(self, program):
        '''
        Load given instructions into RAM sequentially
        '''

        self.reset()
        for i in range(len(program)):
            self.RAM[i] = read_instruction(program[i])

    def run_program(self, program):
        '''
        Runs the given program and detects any infinite loops
        '''

        self.load_program(program)

        visited_states = set()

        while self.execute_next_instruction():
            state = ("\n").join(self.get_state(show_cycles=False))

            if state in visited_states:
                raise InfiniteLoopDetected()
            else:
                visited_states.add(state)

    def execute_next_instruction(self):
        '''
        Main execution function, grabs the next instruction and executes it

        Stops if it ever reads STOP_INSTRUCTION
        '''
        next_instruction = self.get_next_word()

        if next_instruction == specs.STOP_INSTRUCTION:
            return False

        (op_code, a, b) = parse_instruction(next_instruction)

        is_basic = (b is not None)

        op = self.get_op(op_code, is_basic)

        op(self.get_value(a), self.get_value(b)) if is_basic \
            else op(self.get_value(a))

        return True

    @cycles(1)
    def get_next_word(self):
        '''
        Retrieves the word pointed to by PC and increments PC by 1
        '''

        next_word = self.RAM[self.PC]
        self.PC += 1
        return next_word

    def get_op(self, op_code, is_basic):
        '''
        Returns a function representing an implementation of
        the given op_code
        '''
        ops = self.basic_ops if is_basic else self.non_basic_ops

        if op_code not in ops:
            raise OpCodeNotImplemented(op_code)

        return ops[op_code]

    def get_value(self, value_code):
        '''
        Returns a Value instance with appropriate read/write functionality
        based on the given value_code
        '''

        # These value codes read/write to a register
        if value_code in specs.REGISTERS.keys() + specs.SPECIAL_REGISTERS.keys():
            def read():
                return self.registers[value_code]
            def write(v):
                self.registers[value_code] = v

        # These value codes read/write to an address in RAM
        elif value_code <= 0x1e:

            # [register]
            if value_code <= 0x0f:
                address = self.registers[value_code - 0x08]

            # [next word + register]
            elif value_code <= 0x17:
                address = self.registers[value_code - 0x10] + self.get_next_word()

            # POP
            elif value_code == 0x18:
                address = self.SP
                self.SP += 1

            # PEEK
            elif value_code == 0x19:
                address = self.SP

            # PUSH
            elif value_code == 0x1a:
                self.SP -= 1
                address = self.SP

            # [next word]
            elif value_code == 0x1e:
                address = self.get_next_word()

            def read():
                return self.RAM[address]
            def write(v):
                self.RAM[address] = v

        # These value codes represent literals
        elif value_code <= 0x3f:

            # next word (literal)
            if value_code == 0x1f:
                value = self.get_next_word()

            # literal value 0x00-0x1f
            else:
                value = (value_code - 0x20)

            def read():
                return value
            def write(v):
                # Fail silently on trying to assign to a literal
                pass

        # Value codes > 0x3f are undefined
        else:
            raise InvalidValueCode(value_code)

        return Value(read, write)

    @cycles(1)
    def set(self, a, b):
        '''
        Sets a to b
        '''

        a.write(b.read())

    @cycles(2)
    def add(self, a, b):
        '''
        Sets a to a+b, sets O to 0x0001 if there's an overflow, 0x0 otherwise
        '''

        result = a.read() + b.read()

        if result > self.MAX_VAL:
            self.O = 0x0001
        else:
            self.O = 0x0

        a.write(result)

    @cycles(2)
    def subtract(self, a, b):
        '''
        Sets a to a-b, sets O to 0xffff if there's an underflow, 0x0 otherwise
        '''

        a_value = a.read()
        b_value = b.read()

        if b_value > a_value:
            a_value += self.MAX_VAL
            self.O = 0xffff
        else:
            self.O = 0x0

        result = a_value - b_value

        a.write(result)

    @cycles(2)
    def multiply(self, a, b):
        '''
        Sets a to a*b, sets O to ((a*b)>>16)&0xffff
        '''

        result = a.read() * b.read()

        self.O = (result >> specs.WORD_SIZE)
        a.write(result)

    @cycles(3)
    def divide(self, a, b):
        '''
        Sets a to a/b, sets O to ((a<<16)/b)&0xffff. if b==0, sets a and O to 0 instead
        '''

        a_value = a.read()
        b_value = b.read()

        if b_value == 0:
            self.O = 0
            a.write(0)
        else:
            self.O = ((a_value << specs.WORD_SIZE)/b_value)
            a.write(a_value / b_value)

    @cycles(3)
    def modulo(self, a, b):
        '''
        Sets a to a%b. if b==0, sets a to 0 instead
        '''

        b_value = b.read()

        if b_value == 0:
            a.write(0)
        else:
            a.write(a.read() % b_value)

    @cycles(2)
    def shift_left(self, a, b):
        '''
        Sets a to a<<b, sets O to ((a<<b)>>16)&0xffff
        '''

        result = a.read() << b.read()
        a.write(result)
        self.O = (result >> 16)

    @cycles(2)
    def shift_right(self, a, b):
        '''
        Sets a to a>>b, sets O to ((a<<16)>>b)&0xffff
        '''

        a_value = a.read()
        b_value = b.read()

        a.write(a_value >> b_value)
        self.O = ((a_value << 16) >> b_value)

    @cycles(1)
    def boolean_operation(self, boolean_operator, a, b):
        '''
        Sets a to a <boolean_operator> b
        '''

        a.write(boolean_operator(a.read(), b.read()))

    @cycles(2)
    def if_condition(self, conditional, a, b):
        '''
        Performs next instruction only if a <conditional> b
        '''

        if not conditional(a.read(), b.read()):
            self.PC += get_word_length(self.RAM[self.PC])
            self.cycles_ran += 1

    @cycles(2)
    def jump_and_set_return(self, a):
        '''
        Pushes the address of the next instruction to the stack, then sets PC to a
        '''

        self.SP -= 1
        self.RAM[self.SP] = self.PC
        self.PC = a.read()

    def get_state(self, show_cycles=True):
        state = []

        if show_cycles:
            state.append("Ran %d cyles" % self.cycles_ran)
            state.append("")

        state.append("PC: " + self.HEX_OUTPUT_FORMAT % self.PC)
        state.append("SP: " + self.HEX_OUTPUT_FORMAT % self.SP)
        state.append("O:  " + self.HEX_OUTPUT_FORMAT % self.O)
        state.append("")
        state.append("Register values")
        state.append("---------------")
        state.append('\n'.join([name + ": " + self.HEX_OUTPUT_FORMAT % self.registers[key] \
                            for (key, name) in sorted(specs.REGISTERS.iteritems())]))
        state.append("")
        state.append("Memory dump")
        state.append("-----------")
        state.append(str(self.RAM))

        return state

    def __str__(self):
        return '\n'.join(self.get_state())


def get_word_length(instruction):
    '''
    Determines the word length of the given instruction
    '''

    (_, a, b) = parse_instruction(instruction)
    return 1 + (a in specs.GET_WORD_VALUE_CODES) + (b in specs.GET_WORD_VALUE_CODES)

def parse_instruction(instruction):
    '''
    Parses the given WORD_SIZE-bit instruction into an op_code
    and a and b operands

    If the op_code specifies a non-basic instruction, b is returned as None
    '''

    op_code = instruction & bitmask(specs.BASIC_OP_CODE_LENGTH)

    if op_code == specs.NON_BASIC_INSTRUCTION:
        op_code = (instruction >> specs.BASIC_OP_CODE_LENGTH) & bitmask(specs.NON_BASIC_OP_CODE_LENGTH)
        a = (instruction >> (specs.BASIC_OP_CODE_LENGTH + specs.NON_BASIC_OP_CODE_LENGTH)) \
                & bitmask(specs.VALUE_LENGTH)
        b = None
    else:
        a = (instruction >> specs.BASIC_OP_CODE_LENGTH) & bitmask(specs.VALUE_LENGTH)
        b = (instruction >> (specs.BASIC_OP_CODE_LENGTH + specs.VALUE_LENGTH)) & bitmask(specs.VALUE_LENGTH)

    return (op_code, a, b)

def read_instruction(instruction):
    '''
    Returns the given instruction as an integer after verifying it is
    a valid WORD_SIZE-bit instruction
    '''

    value = to_int(instruction, bases_to_try=[16])

    if not value:
        raise InvalidInstruction("Could not read instruction as a binary or hexadecimal number", instruction)


    if value.bit_length() > specs.WORD_SIZE:
        raise InvalidInstruction("Instruction was not %d-bit" % specs.WORD_SIZE, instruction)

    return value

class InfiniteLoopDetected(Exception):
    pass

class InvalidValueCode(Exception):
    def __init__(self, op_code):
        self.op_code = op_code

    def __str__(self):
        return "Value code was out of range: %#x" % self.op_code

class OpCodeNotImplemented(Exception):
    def __init__(self, op_code):
        self.op_code = op_code

    def __str__(self):
        return "%#x" % self.op_code

class InvalidInstruction(Exception):
    def __init__(self, msg, instruction):
        self.msg = msg
        self.instruction = instruction

    def __str__(self):
        return "%s: %s" % (self.msg, self.instruction)
