# -*- coding: utf-8 -*-
'''
unique utility
'''

import itertools

def uniq_count_gen(the_sorted):
    '''
    generates pairs of an element and the count of it
    from the sorted element iterator.
    '''
    if not the_sorted:
        return
    the_iter, = itertools.tee(the_sorted, 1)
    prev = the_iter.next()
    count = 1
    for cur in the_iter:
        if cur == prev:
            count += 1
        else:
            yield (prev, count)
            prev = cur
            count = 1
    yield (prev, count)
