'''
Created on Mar 17, 2014

@author: pablob
'''


def incrementor(seed):
    # Return a function that when it is call the first time returns the seed 
    # given. Subsequents calls return 1 + the las value returned. So first, 
    # would be seed. Then seed +1, then seed +2 and you can imagine the other
    # calls.
    def _infinit_incr(value):
        i = value
        while True:
            yield i
            i = i + 1
    inc = _infinit_incr(seed)
    return lambda : inc.next()