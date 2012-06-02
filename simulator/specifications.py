from utilities import invert

# http://0x10c.com/doc/dcpu-16.txt

DCPU_VERSION = '1.1'

ASSEMBLER_FILE_EXT = 'dasm16'
MACHINE_FILE_EXT = 'dcpu'


BASIC_OP_CODE_LENGTH = 4
NON_BASIC_OP_CODE_LENGTH = 6
VALUE_LENGTH = 6
NON_BASIC_INSTRUCTION = 0x0

MAX_RAM_ADDRESS = 0xffff
WORD_SIZE = 16

STOP_INSTRUCTION = 0x0

GET_WORD_VALUE_CODES = range(0x10, 0x17 + 1) + [0x1e, 0x1f]

REGISTERS = {
    0x00: 'A',
    0x01: 'B',
    0x02: 'C',
    0x03: 'X',
    0x04: 'Y',
    0x05: 'Z',
    0x06: 'I',
    0x07: 'J',
}

SPECIAL_REGISTERS = {
    0x1b: 'SP',
    0x1c: 'PC',
    0x1d: 'O',
}

STACK_CODES = {
    0x18: 'POP',
    0x19: 'PEEK',
    0x1a: 'PUSH',
}

REGISTER_NAMES = invert(REGISTERS)
SPECIAL_REGISTER_NAMES = invert(SPECIAL_REGISTERS)
STACK_CODE_NAMES = invert(STACK_CODES)

class BasicOperations:
    SET = 0x1
    ADD = 0x2
    SUB = 0x3
    MUL = 0x4
    DIV = 0x5
    MOD = 0x6
    SHL = 0x7
    SHR = 0x8
    AND = 0x9
    BOR = 0xa
    XOR = 0xb
    IFE = 0xc
    IFN = 0xd
    IFG = 0xe
    IFB = 0xf

class NonBasicOperations:
    JSR = 0x01
