# -*- coding: utf-8 -*-
'''
statics logics.
otherwise, definitions of queries.
'''
import logging
from sqlalchemy import func, distinct, desc, insert, delete

from uniq_utils import uniq_count_gen
import message_utils
from statisticsdb import Sender, Word, Message, MessageWord, Score, Parameter, \
                         TmpMessage, TmpMessageWord

MESSAGE_COUNT_PER_COMMIT = 5000
MAX_ROW_COUNT_PER_INSERT = 1000
LAST_MID_OF_INSERT_MESSAGE = "LastMidOfInsertMessage"
LAST_MID_OF_INSERT_WORDS = "LastMidOfInsertWord"

def get_parameter_value(session, key):
    '''
    get value by key from parameter table 
    '''
    value = session.query(Parameter).filter(Parameter.key == key).first()
    if value:
        value = value.value
    return value

def _tmp_message_gen(reader):
    '''
    tmp message generator
    '''
    count = 0
    for time, sender, text, mid in reader:
        yield time, sender, text, mid
        count += 1
        if count >= MESSAGE_COUNT_PER_COMMIT:
            break

def _tmp_message_values_gen(reader):
    '''
    tmp message values generator
    '''
    count = 0
    values = []
    for time, sender, text, mid in reader:
        values.append(
              {
               "mid": mid,
               "time": time,
               "sender": sender,
               "message": text,
               "need": 0
               }
         )
        count += 1
        if count == MAX_ROW_COUNT_PER_INSERT:
            yield values
            values = []
            count = 0
    if count > 0:
        yield values
    
def _insert_tmp_messages(reader, session):
    '''
    insert messages into tmp table from reader.
    '''
    reader = _tmp_message_values_gen(_tmp_message_gen(reader))
    stmt = insert(TmpMessage.__table__)
    count = 0
    mid = None
    
    for values in reader:
        session.execute(stmt.values(), values)
        count += len(values)
        mid = values[-1]["mid"]
    session.flush()
    logging.info("%d temporay messages was inserted", count)

    return mid

def _mark_tmpmsg_from_known_senders(session):
    '''
    mark tmp messages from known senders need.
    '''
    session.execute("""
        update
            tmp_messages
        set
            need = 1
        where
            sender in (
                select 
                    sender
                from
                    senders
    )
    """)

def _mark_tmpmsg_in_japanese(session, japanase):
    '''
    mark tmp messages in Japanese need.
    '''
    for tmp_message in session.query(TmpMessage):
        message = tmp_message.message
        if not isinstance(message, unicode):
            message = unicode(message, "utf-8")
        if japanase.is_japanese(message):
            tmp_message.need = True
    session.flush()

def _get_new_tmp_senders(session):
    '''
    get new senders
    '''
    return session.execute("""
        select 
            distinct sender
        from
            tmp_messages
        where
            sender not in (
                select
                    sender
                from
                    senders
            )
    """)

def _register_new_tmp_messages(session):
    '''
    register new messages from tmp table to messages table.
    '''
    session.execute("""
        insert into
            messages
        select
            mid, time, sid, message
        from
            tmp_messages
            join senders on tmp_messages.sender = senders.sender
    """)

def insert_messages(reader, session, japanese_module):
    '''
    retrieve new messages from reader limit MESSAGE_COUNT_PER_COMMIT
    insert messages into database if in Japanese.
    '''
    mid = _insert_tmp_messages(reader, session)

    # delete messages without need from tmp table    
    _mark_tmpmsg_from_known_senders(session)
    _mark_tmpmsg_in_japanese(session, japanese_module)
    stmt = delete(TmpMessage.__table__).where(TmpMessage.need == False)
    session.execute(stmt)

    # register new senders and new messages from tmp table.
    for sender, in _get_new_tmp_senders(session):
        session.add(Sender(sender))
    session.flush()
    _register_new_tmp_messages(session)
    
    # delete all records from tmp table.
    session.execute(delete(TmpMessage.__table__))
    
    # record last registered mid into parameters table.
    if mid:
        session.merge(Parameter(LAST_MID_OF_INSERT_MESSAGE, mid))

def _get_new_messges_query(session):
    '''
    retrieve new messages.extract nouns from them.
    '''
    max_mid = get_parameter_value(session, LAST_MID_OF_INSERT_MESSAGE)
    if not max_mid:
        return None
    query = session.query(Message).filter(Message.mid <= max_mid)
    min_mid = get_parameter_value(session, LAST_MID_OF_INSERT_WORDS)
    if min_mid:
        query = query.filter(Message.mid > min_mid)
    query = query.order_by(Message.time).limit(MESSAGE_COUNT_PER_COMMIT)
    return query

def _apply_message_cutter(message_reader):
    '''
    return cut messages generator
    '''
    for message in message_reader:
        # cut RT/QTs, etc... from the message.
        yield message.mid, message_utils.cut_message(message.message)

def _message_words_gen(message_reader, japanese_module):
    '''
    return messages_words generator
    '''
    mcount = wcount = 0
    for mid, message in message_reader:
        # extract words from message.
        if not isinstance(message, str):
            message = message.encode("utf-8")
        words = japanese_module.get_nouns(message)
    
        # register word, count, message tuples.
        words.sort()
        word_count_pairs = uniq_count_gen(words)
        for word, count in word_count_pairs:
            word = unicode(word, "utf-8")
            yield word, count, mid
            wcount += 1
        mcount += 1
    logging.info("%s words extracted from %s messages.", wcount, mcount)

def  _register_new_words(session):
    '''
    register new words from tmp_message_words table.
    '''
    for word, in session.execute("""
        select
            distinct word
        from
            tmp_message_words
        where
            word not in (
                select
                    word
                from
                    words
            )
    """):
        session.add(Word(word, 0))
    session.flush()

def _resiter_new_message_words(session):
    '''
    register new message words from tmp_message_words table.
    '''
    session.execute("""
        insert into
            message_words
        select
            wid, count, mid
        from
            tmp_message_words
            join words on tmp_message_words.word=words.word
    """)
    session.execute(delete(TmpMessageWord.__table__))

def _message_words_values_gen(message_words_reader):
    '''
    sets of message_words generator
    '''
    values = []
    loop_count = 0
    for word, count, mid in message_words_reader:
        values.append({"word": word, "count": count, "mid": mid})
        if loop_count == MAX_ROW_COUNT_PER_INSERT:
            yield values
            values = []
            loop_count = 0
    if len(values):
        yield values

def extract_and_insert_words(session, japanese_module):
    '''
    retrieve new messages.extract nouns from them.
    insert the noun-message pairs into tmp table.
    register new words and message_words into tables from tmp table.
    '''
    # setup generators(filter and extractor)
    message_reader = _get_new_messges_query(session)
    if not message_reader:
        return
    message_reader = _apply_message_cutter(message_reader)
    message_words_reader = _message_words_gen(message_reader, japanese_module)
    message_words_values_gen = _message_words_values_gen(message_words_reader)
    
    # insert the noun-message pairs into tmp table.
    mid = None
    stmt = insert(TmpMessageWord.__table__)
    values = []
    loop_count = 0
    for values in message_words_values_gen:
        session.execute(stmt.values(), values)
        loop_count += len(values)
        mid = values[-1]["mid"]
    session.flush()
    logging.info("%s temporary message words was inserted.", loop_count)

    # register new words from tmp_message_words table.
    _register_new_words(session)

    # register new message words from tmp_message_words table.
    _resiter_new_message_words(session)

    if mid:
        session.merge(Parameter(LAST_MID_OF_INSERT_WORDS, mid))

def calculate_df(session):
    '''
    calculate and update DFs for all words. 
    '''
    for word, count in session\
            .query(Word, func.count(distinct(Sender.sid)))\
            .join(Sender.messages, Message.message_words, MessageWord.word)\
            .group_by(Word.wid):
        word.sender_count = count
    session.flush()

def calculate_tf_idf(session):
    '''
    calculate and update TF-IDF for all scores. 
    '''
    all_sender_count = session.query(Sender).count()
    session.execute(delete(Score.__table__))
    session.execute("""
        insert into
            scores
        select
            sid,
            words.wid,
            1. * sum(message_words.count)
            * :all_sender_count / sender_count as tfidf
        from
            words,
            messages,
            message_words
        where
            words.wid = message_words.wid
            and message_words.mid = messages.mid
        group by
            sid,
            words.wid
        order by
            sid,
            message_words.wid,
            tfidf desc
    """, {'all_sender_count': all_sender_count})

def get_high_score_words(session, word_limit=5, sender_limit=10, sender=None):
    '''
    return generator
    which will generate word_limit count of high score words
    group by most often tweeting sender within sender_limit.  
    '''
    # most often tweeting sender
    query = session.query(Sender, func.count(Message.mid).label('count_label'))\
            .join(Sender.messages)
    if sender:
        query = query.filter(Sender.sender == sender)
    query = query.group_by(Sender.sid).order_by(desc('count_label'))
    if sender_limit > 0:
        query = query.limit(sender_limit)
    
    for sender, count in query:
        for word, score in session \
                .query(Word, Score)\
                .join(Sender.scores, Score.word)\
                .filter(Sender.sid == sender.sid)\
                .order_by(desc(Score.score))\
                .limit(word_limit):
            yield sender.sender, word.word, score.score

def report_summary(session):
    '''
    report summary to log.
    '''
    logging.info("=========================")
    logging.info("total messages:%10d", session.query(Message).count())
    logging.info("total senders: %10d", session.query(Sender).count())
    logging.info("total words:   %10d", session.query(Word).count())
    logging.info("=========================")
