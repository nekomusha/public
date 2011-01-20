#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import sys
from contextlib import closing
import logging
from ConfigParser import SafeConfigParser

#LOG_FILENAME = '/tmp/logging_example.out'
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)
logging.basicConfig(level=logging.DEBUG)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from twitter_statistics.statisticsdb import Base
from twitter_statistics import gwibberdb
from twitter_statistics.statistics_logic import \
    get_parameter_value, LAST_MID_OF_INSERT_MESSAGE, \
    insert_messages, extract_and_insert_words, \
    calculate_df, calculate_tf_idf, \
    get_high_score_words, report_summary
from twitter_statistics import japanese

def main(args):
    '''
    display words and score extracted from tweets on gwibberdb
    '''
    # SQLite database file path for statisticsdb
    home = os.path.expanduser("~")
    configbase = os.path.join(home, ".config/twitter_statistics")
    configfile = os.path.join(configbase, "config.ini")
    config = SafeConfigParser()
    if not os.access(configfile, os.F_OK):
        if not os.access(configbase, os.F_OK):
            os.makedirs(configbase)
        with open(configfile, "w") as fout:
            fout.write(
"""[Statistics]
DatabaseURI = sqlite:///%s/morph.sqlite
""" % home)
    config.read(configfile)
    dburi = config.get("Statistics", "DatabaseURI") 
    
    # TODO: unicode parameters was not effective...
    # create tables and a SQLAlchemy session class
    engine = create_engine(dburi, echo=False)
    
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    with closing(Session()) as session:
        # synchronize statisticsdb from gwibberdb
        last_mid = mid = get_parameter_value(
                  session, LAST_MID_OF_INSERT_MESSAGE)
        while True:
            #  insert extracted words into staticsdb from tweets on gwibberdb
            insert_messages(gwibberdb.read(last=mid), session, japanese)
            extract_and_insert_words(session, japanese)
            session.commit()
            
            mid = get_parameter_value(session, LAST_MID_OF_INSERT_MESSAGE)
            if mid == last_mid:
                break
            last_mid = mid

        # calculate DF
        calculate_df(session)
        session.commit()

        # calculate TF-IDF
        calculate_tf_idf(session)
        session.commit()
        
        # report summary to log.
        report_summary(session)
        
        # get words with high TF-IDF
        for sender, word, score in get_high_score_words(session):
            if not isinstance(sender, unicode):
                sender = unicode(sender, "utf-8")
            if not isinstance(word, unicode):
                word = unicode(word, "utf-8")
            print u'"%s","%s",%s' % (sender, word, score)

if __name__ == '__main__':
    main(sys.argv)
