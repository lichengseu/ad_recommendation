# -*- coding: utf-8 -*-

"""
# @Author  : captain
# @Time    : 2018/11/5 20:25
# @Ide     : PyCharm
"""
from .tfidf import TFIDF
from .textrank import TextRank
from .entity_linking import EntityLinking

default_tfidf = TFIDF()
default_textrank = TextRank()

extract_tags = tfidf = default_tfidf.extract_tags
set_idf_path = default_tfidf.set_idf_path
textrank = default_textrank.extract_tags


def set_stop_words(stop_words_path):
    default_tfidf.set_stop_words(stop_words_path)
    default_textrank.set_stop_words(stop_words_path)
