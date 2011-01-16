# -*- coding: utf-8 -*-
'''
twitter message utility
'''

import re

# a simplified URL expression
__re_url__ = re.compile(\
        '(https?|ftp)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)')
# a reference expression for twitter
__re_at__ = re.compile(\
        '@[a-zA-Z0-9_]+')
# a loose RT/QT expression of twitter
__re_rtqt__ = re.compile(\
        '[QR]T.*$')

def cut_message(message):
    '''
    return the message that is cut URLs, references and RT/QTs
    '''
    message = __re_url__.sub(" ", message)
    message = __re_at__.sub(" ", message)
    message = __re_rtqt__.sub(" ", message)
    return message
