# -*- coding: utf-8 -*-
'''
日本語関連モジュール
'''

import MeCab
import re

MEISHI = u"名詞".encode("utf-8")
__mecab__ = MeCab.Tagger("")
__re_hiragana__ = re.compile(u"[あ-ん]+")

def get_nouns(sentence):
    '''
    日本語文(sentence)(UTF-8)から名詞抽出してリストを返す。
    '''
    node = __mecab__.parseToNode(sentence)
    res = []
    while node:
        pos = node.feature.split(",", 1)[0]
        if pos == MEISHI:
            res.append(node.surface)
        node = node.next
    return res

def is_japanese(sentence):
    '''
    sentence(Unicode文字列)が日本語かどうか(実際には平仮名を含んでいるか)を返す。
    '''
    return __re_hiragana__.search(sentence)
