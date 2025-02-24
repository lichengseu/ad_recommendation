# -*- coding: utf-8 -*-

"""
# @Author  : captain
# @Time    : 2018/11/5 20:26
# @Ide     : PyCharm
"""
import os
import jieba
import jieba.posseg
from operator import itemgetter

_get_module_path = lambda path: os.path.join(os.path.dirname(__file__), path)

DEFAULT_IDF = _get_module_path('idf.txt')
DEFAULT_STOP = _get_module_path('stopwords.txt')


class KeywordExtractor(object):
    # 中文停用词需要自己设置
    STOP_WORDS = set()

    def __init__(self):
        self.set_stop_words(DEFAULT_STOP)

    def set_stop_words(self, stop_words_path):
        if not os.path.isfile(stop_words_path):
            raise Exception('file does not exist: {}'.format(stop_words_path))
        content = open(stop_words_path, 'rb').read().decode('utf-8')
        for line in content.splitlines():
            self.STOP_WORDS.add(line)

    def extract_tags(self, *args, **kwargs):
        raise NotImplementedError


class IDFLoader(object):
    def __init__(self, idf_path=None):
        self.path = ''
        self.idf_freq = {}
        self.median_idf = 0.0
        if idf_path:
            self.set_new_path(idf_path)

    def set_new_path(self, new_idf_path):
        if self.path != new_idf_path:
            self.path = new_idf_path
            content = open(new_idf_path, 'rb').read().decode('utf-8')
            self.idf_freq = {}
            for line in content.splitlines():
                word, freq = line.strip().split(' ')
                self.idf_freq[word] = float(freq)
            self.median_idf = sorted(self.idf_freq.values())[len(self.idf_freq) // 2]

    def get_idf(self):
        return self.idf_freq, self.median_idf


class TFIDF(KeywordExtractor):
    def __init__(self, idf_path=None):
        super().__init__()
        self.tokenizer = jieba.dt
        self.postokenizer = jieba.posseg.dt
        self.stop_words = self.STOP_WORDS.copy()
        self.idf_loader = IDFLoader(idf_path or DEFAULT_IDF)
        self.idf_freq, self.median_idf = self.idf_loader.get_idf()

    def set_idf_path(self, idf_path):
        new_abs_path = idf_path
        if not os.path.isfile(new_abs_path):
            raise Exception('file does not exist: {}'.format(new_abs_path))
        self.idf_loader.set_new_path(new_abs_path)
        self.idf_freq, self.median_idf = self.idf_loader.get_idf()

    def extract_tags(self, sentence, topK=20, withWeight=False, allowPOS=(), withFlag=False):
        """
        Extract keywords from sentence using TF-IDF algorithm.
        Parameter:
            - topK: return how many top keywords. `None` for all possible words.
            - withWeight: if True, return a list of (word, weight);
                          if False, return a list of words.
            - allowPOS: the allowed POS list eg. ['ns', 'n', 'vn', 'v','nr'].
                        if the POS of w is not in this list,it will be filtered.
            - withFlag: only work with allowPOS is not empty.
                        if True, return a list of pair(word, weight) like posseg.cut
                        if False, return a list of words
        """
        if allowPOS:
            allowPOS = frozenset(allowPOS)
            words = self.postokenizer.cut(sentence)
        else:
            words = self.tokenizer.cut(sentence)
        freq = {}
        for w in words:
            if allowPOS:
                if w.flag not in allowPOS:
                    continue
                elif not withFlag:
                    w = w.word
            wc = w.word if allowPOS and withFlag else w
            if len(wc.strip()) < 2 or wc.lower() in self.stop_words:
                continue
            freq[w] = freq.get(w, 0.0) + 1.0
        total = sum(freq.values())
        for k in freq:
            kw = k.word if allowPOS and withFlag else k
            freq[k] *= self.idf_freq.get(kw, self.median_idf) / total

        if withWeight:
            tags = sorted(freq.items(), key=itemgetter(1), reverse=True)
        else:
            tags = sorted(freq, key=freq.__getitem__, reverse=True)
        if topK:
            return tags[:topK]
        else:
            return tags
