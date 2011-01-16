# -*- coding: utf-8 -*-
'''
gwibber database utility
'''
import sqlite3
import os.path
from contextlib import closing

HOME = os.path.expanduser("~")
DBPATH = os.path.join(HOME, ".config/gwibber/gwibber.sqlite")

def read(last=None):
    '''
    tweets reader(generator)
    '''
    with sqlite3.connect(DBPATH) as con:
        with closing(con.cursor()) as cursor:
            if last:
                cursor.execute(u"""
                    select
                        time, sender, text, mid
                    from
                        messages
                    where
                        mid > :last
                    group by
                        mid
                    order by
                        mid
                    """, {"last": last})
            else:
                cursor.execute(u"""
                    select
                        time, sender, text, mid
                    from
                        messages
                    group by
                        mid
                    order by
                        mid
                    """)
            for time, sender, text, mid in cursor:
                yield (time, sender, text, mid)
    return
