from simulator import specifications as specs
from simulator.utilities import bitmask, to_int

class Tokens:
    COMMENT = ";"
    LABEL = ":"
    ARG_SEPARATOR = ","
    VALUE_REF_OPEN = "["
    VALUE_REF_CLOSE = "]"
    ADD = "+"

def assemble(program):
    current_address = 0x0
    instructions = []
    labels = {}

    # Generate list of instructions
    for line in program:
        try:
            instruction = parse_line(line)
        except Exception, e:
            raise AssemblerSyntaxError(line, e.message)

        if instruction is None:
            continue

        if instruction.label:
            labels[instruction.label] = current_address

        current_address += instruction.word_length

        instructions.append(instruction)

    return [word for ins in instructions for word in ins.get_hex(labels)]

def parse_line(line):
    tokens = line.strip().split()
    tokens.reverse()

    if not tokens:
        return None

    token = tokens.pop()
    if is_comment(token):
        return None
    else:
        tokens.append(token)

    token = tokens.pop()
    label = parse_label(token)
    if not label:
        tokens.append(token)

    (op_code, is_basic) = parse_op(tokens.pop())
    (value_code_a, word_a) = parse_value_code(tokens.pop(), is_basic)
    (value_code_b, word_b) = parse_value_code(tokens.pop()) if is_basic else (None, None)

    ins = Instruction(op_code, is_basic, value_code_a, value_code_b, label)

    if word_a:
        ins.add_word(word_a)

    if word_b:
        ins.add_word(word_b)

    return ins

def is_comment(token):
    return token.startswith(Tokens.COMMENT)

def parse_label(token):
    if token.startswith(Tokens.LABEL):
        return token[len(Tokens.LABEL):]
    else:
        return None

def parse_op(token):
    if token in dir(specs.BasicOperations):
        return (getattr(specs.BasicOperations, token), True)
    elif token in dir(specs.NonBasicOperations):
        return (getattr(specs.NonBasicOperations, token), False)
    else:
        raise InvalidOperation(token)

def parse_register(token, allow_special_values=True):
    code_mapping = specs.REGISTER_NAMES

    if allow_special_values:
        code_mapping.update(specs.SPECIAL_REGISTER_NAMES)
        code_mapping.update(specs.STACK_CODE_NAMES)

    if token in code_mapping:
        return code_mapping[token]
    else:
        raise InvalidValueReference(token)

def parse_value_code(token, is_basic=False):
    '''
    0x00-0x07: register (A, B, C, X, Y, Z, I or J, in that order)
    0x08-0x0f: [register]
    0x10-0x17: [next word + register]
         0x18: POP / [SP++]
         0x19: PEEK / [SP]
         0x1a: PUSH / [--SP]
         0x1b: SP
         0x1c: PC
         0x1d: O
         0x1e: [next word]
         0x1f: next word (literal)
    0x20-0x3f: literal value 0x00-0x1f (literal)
    '''

    word = None
    token = token.strip(Tokens.ARG_SEPARATOR)

    # [register], [next word + register], or [next word]
    if token.startswith(Tokens.VALUE_REF_OPEN):

        if token.find(Tokens.VALUE_REF_CLOSE) < 0:
            raise AssemblerSyntaxError(token, "No closing bracket")

        token = token[token.find(Tokens.VALUE_REF_OPEN)+1:token.find(Tokens.VALUE_REF_CLOSE)]

        add_loc = token.find(Tokens.ADD)

        # [next word + register]
        if add_loc > 0:
            word = to_int(token[:add_loc], bases_to_try=[10, 16])
            value_code = parse_register(token[add_loc+1:], allow_special_values=False)
            value_code += 0x10
        else:
            # [register]
            try:
                value_code = parse_register(token, allow_special_values=False)
                value_code += 0x08
            # [next word]
            except:
                word = to_int(token, bases_to_try=[10, 16])
                value_code = 0x1e
    else:
        # register
        try:
            value_code = parse_register(token)
        except:
            # next word (literal)
            try:
                word = to_int(token, bases_to_try=[10, 16])

                if word <= 0x1f:
                    value_code = word + 0x20
                    word = None
                else:
                    value_code = 0x1f
            except:
                # label reference
                value_code = 0x1f
                word = token

    if isinstance(word, int) and (word < 0x0 or word > bitmask(specs.WORD_SIZE)):
        raise ValueOutOfRange(word)

    return (value_code, word)

class ValueOutOfRange(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Value out of range: %#x" % self.value

class InvalidValueReference(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Unrecgonized value reference: %s" % self.value

class InvalidOperation(Exception):
    def __init__(self, op):
        self.op = op

    def __str__(self):
        return "Unrecognized operation: %s" % self.op

class AssemblerSyntaxError(Exception):
    def __init__(self, line, exception):
        self.line = line
        self.exception = exception

    def __str__(self):
        return "Syntax error on line:\n\t%s\nError: %s" % (self.line, self.exception)

class Instruction(object):
    def __init__(self, op_code, is_basic, value_code_a, value_code_b = None, label = None):
        self.op_code = op_code
        self.is_basic = is_basic
        self.value_code_a = value_code_a
        self.value_code_b = value_code_b
        self.label = label
        self.additional_words = []

    def add_word(self, word):
        self.additional_words.append(word)

    def get_hex(self, labels=None):
        '''
        Basic: bbbbbbaaaaaaoooo
        Non-basic: aaaaaaoooooo0000
        '''

        a = self.value_code_a
        if self.is_basic:
            b = self.value_code_b

            code = ((b << (specs.VALUE_LENGTH + specs.BASIC_OP_CODE_LENGTH))
                    + (a << (specs.BASIC_OP_CODE_LENGTH))
                    + (self.op_code))

        else:
            code = ((a << (specs.VALUE_LENGTH + specs.BASIC_OP_CODE_LENGTH))
                    + (self.op_code << (specs.BASIC_OP_CODE_LENGTH)))

        return [hex(code)] + [self.get_value(word, labels) for word in self.additional_words]

    @property
    def word_length(self):
        return (1 + len(self.additional_words))

    def get_value(self, value, labels):
        try:
            if not isinstance(value, int):
                value = labels[value]

            return hex(value)
        except:
            raise InvalidValueReference(value)
