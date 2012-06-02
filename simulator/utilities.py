def bitmask(n):
    '''
    Returns a int with the first n bits set
    '''

    return 2**n - 1

def to_int(value, bases_to_try):
    '''
    Tries to convert the given value to an integer
    using the given bases in order
    '''

    if isinstance(value, int):
        return value

    result = None

    for b in bases_to_try:
        try:
            result = int(value, base=b)
            break
        except ValueError:
            continue

    return result

def invert(dictionary):
    '''
    Return a dictionary with an inverted mapping
    '''
    return dict(((v,k) for (k,v) in dictionary.iteritems()))
