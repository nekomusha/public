# -*- coding: utf-8 -*-
'''
statistics table definitions for SQLAlchemy
and utility functions
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship, backref

TID_LEN = 15
TMES_LEN = 255

Base = declarative_base()
class Sender(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'senders'
    __table_args__ = {'mysql_engine':'InnoDB'}

    sid = Column(Integer, primary_key=True)
    sender = Column(String(TID_LEN), nullable=False, index=True, unique=True)

    def __init__(self, sender):
        self.sender = sender

    def __repr__(self):
        return "<Sender('%s')>" % (self.sender)

class Word(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'words'
    __table_args__ = {'mysql_engine':'InnoDB'}

    wid = Column(Integer, primary_key=True, autoincrement = True)
    word = Column(String(TMES_LEN), nullable=False, index=True, unique=True)
    sender_count = Column(Integer, nullable=False)

    def __init__(self, word, sender_count):
        self.word = word
        self.sender_count = sender_count

    def __repr__(self):
        return "<Word('%s', %d)>" % (self.word, self.sender_count)

class Message(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'messages'
    __table_args__ = {'mysql_engine':'InnoDB'}

    mid = Column(BigInteger, primary_key=True, autoincrement = True)
    time = Column(Integer, nullable=False)
    sid = Column(Integer, ForeignKey('senders.sid'), nullable=False)
    message = Column(String(TMES_LEN), nullable=False)

    sender = relationship(Sender, backref=backref('messages', order_by=mid))

    def __init__(self, mid, time, message):
        self.mid = mid
        self.time = time
        self.message = message

    def __repr__(self):
        return "<Message(%d, %d, %d, %d)>" % \
               (self.mid, self.time, self.sid, self.message)

class MessageWord(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'message_words'
    __table_args__ = {'mysql_engine':'InnoDB'}

    wid = Column(Integer, ForeignKey('words.wid'), primary_key=True)
    count = Column(Integer, nullable=False)
    mid = Column(BigInteger, ForeignKey('messages.mid'), primary_key=True)

    word = relationship(Word, \
                        backref=backref('message_words', order_by=wid))
    message = relationship(Message, \
                           backref=backref('message_words', order_by=mid))

    def __init__(self, count):
        self.count = count

    def __repr__(self):
        return "<MessageWord(%d)>" % self.count

class Score(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'scores'
    __table_args__ = {'mysql_engine':'InnoDB'}

    sid = Column(Integer, ForeignKey('senders.sid'), primary_key=True)
    wid = Column(Integer, ForeignKey('words.wid'), primary_key=True)
    score = Column(Float, nullable=False)

    sender = relationship(Sender, backref=backref('scores', order_by=wid))
    word = relationship(Word, backref=backref('scores', order_by=wid))

    def __init__(self, score):
        self.score = score

    def __repr__(self):
        return "<Score(%s)>" % self.score
    
class Parameter(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'parameters'
    __table_args__ = {'mysql_engine':'InnoDB'}

    key = Column(String(255), primary_key=True)
    value = Column(String(1000), nullable=True)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<Parameter(%s, %s)>" % (self.key, self.value)

class TmpMessage(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'tmp_messages'
    __table_args__ = {'mysql_engine':'InnoDB'}


    mid = Column(BigInteger, primary_key=True)
    time = Column(Integer, nullable=False)
    sender = Column(String(TID_LEN), nullable=False)
    message = Column(String(TMES_LEN), nullable=False)
    need = Column(Boolean, nullable=False)

    def __init__(self, mid, time, sender, message, need):
        self.mid = mid
        self.time = time
        self.sender = sender
        self.message = message
        self.need = need

    def __repr__(self):
        return "<TmpMessage(%d, %d, %s, %s, %s)>" \
               % (self.mid, self.time, self.sender, self.message, self.need)

class TmpMessageWord(Base):
    '''
    ORM class and table declaration by SQLAlchemy
    '''
    __tablename__ = 'tmp_message_words'
    __table_args__ = {'mysql_engine':'InnoDB'}

    word = Column(String(TMES_LEN), primary_key=True)
    count = Column(Integer, nullable=False)
    mid = Column(BigInteger, primary_key=True)

    def __init__(self, word, count, mid):
        self.word = word
        self.count = count
        self.mid = mid

    def __repr__(self):
        return "<TmpMessageWord(%d)>" % self.count
