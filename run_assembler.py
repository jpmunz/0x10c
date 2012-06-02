import argparse
from simulator import specifications as specs
from assembler import assembler

def read_program(program):
    f = open(program)
    lines = f.readlines()
    f.close()

    return lines

def get_args():
    parser = argparse.ArgumentParser(description='Assemble the given code')

    parser.add_argument('program', help='the file containing the code to be assembled')
    parser.add_argument('--version', action='version', version='DCPU v%s' % specs.DCPU_VERSION)

    return parser.parse_args()

if __name__ == '__main__':

    args = get_args()
    print "\n".join(assembler.assemble(read_program(args.program)))
