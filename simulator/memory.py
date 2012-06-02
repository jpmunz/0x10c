from utilities import bitmask

class InvalidMemoryAccess(Exception):
    def __init__(self, address):
        self.address = address

    def __str__(self):
        return "Memory access outside of addressable range: %#x" % self.address

class InvalidMemoryValue(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Attempt to set memory address to invalid value %s: " % self.value

class Memory(dict):
    '''
    A dictionary that forces values to be set within the range [0x0, word_size - 1]
    Any access to an unset key returns 0x0
    '''

    def __init__(self, word_size):
        self.word_mask = bitmask(word_size)

    def __setitem__(self, key, val):
        if not isinstance(val, int):
            raise InvalidMemoryValue(val)

        super(Memory, self).__setitem__(key, (val & self.word_mask))

    def __getitem__(self, key):
        return super(Memory, self).__getitem__(key) if key in self else 0x0

class RAM(Memory):
    '''
    A block of memory that only accepts keys which are hex values
    between 0x0 and max_address. 
    '''

    DUMP_WORDS_PER_ROW = 8
    DUMP_HEX_FORMAT = '%04x'

    def __init__(self, word_size, max_address):
        super(RAM, self).__init__(word_size)
        self.max_address = max_address

    def check_RAM_access(self, address):
        if isinstance(address, int) and(address < 0x0 or address > self.max_address):
            raise InvalidMemoryAccess(address)

    def __setitem__(self, key, val):
        self.check_RAM_access(key)
        super(RAM, self).__setitem__(key, val)

    def __getitem__(self, key):
        self.check_RAM_access(key)
        return super(RAM, self).__getitem__(key)

    def get_memory_dump(self):
        '''
        Returns a list of strings representing the values stored in RAM
        each item is a row of 8 words preceeded by the address of the first word

        Ex.
            0000: 7c01 0030 7de1 1000 0020 7803 1000 c00d
            0008: 7dc1 001a a861 7c01 2000 2161 2000 8463

        A row is added only if it contains at least one used address
        '''

        dump = []
        current_row = None

        for address in sorted(self.keys()):

            if current_row is None or address >= current_row + self.DUMP_WORDS_PER_ROW:

                # Round to closest multiple of DUMP_WORDS_PER_ROW
                current_row = self.DUMP_WORDS_PER_ROW * (address / self.DUMP_WORDS_PER_ROW)

                words = [self.DUMP_HEX_FORMAT % self[current_row + offset] \
                            for offset in range(self.DUMP_WORDS_PER_ROW)]

                dump.append(self.DUMP_HEX_FORMAT % current_row + ": " + " ".join(words))

        return dump

    def __str__(self):
        return '\n'.join(self.get_memory_dump())

