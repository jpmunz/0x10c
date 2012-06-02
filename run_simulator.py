import argparse

from simulator import DCPU, specifications, InfiniteLoopDetected

def read_program(program):
    f = open(program)
    instructions = f.readlines()
    f.close()

    return instructions

def get_args():
    parser = argparse.ArgumentParser(description='Run the DCPU simulator')

    parser.add_argument('program', help='the file containing the instruction words to be run')
    parser.add_argument('--version', action='version', version='DCPU v%s' % specifications.DCPU_VERSION)

    return parser.parse_args()

if __name__ == '__main__':

    args = get_args()
    instructions = read_program(args.program)

    cpu = DCPU()

    try:
        cpu.run_program(instructions)
    except InfiniteLoopDetected:
        print "*****Infinite loop detected, stopping execution*****"

    print
    print "--------------------------"
    print "DCPU State after execution"
    print "--------------------------"
    print cpu
