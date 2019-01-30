# -*- coding: utf-8 -*-

"""
# @Author  : Captain
# @Time    : 2018/12/15 15:26
# @Ide     : PyCharm

Extract keys from news and advertisement keywords.
"""
import re
import jieba.analyse
import utils
import pandas as pd
from configparser import ConfigParser


def extract_news(path, result_path):
    f = open(path, encoding='utf-8')
    news_data = pd.read_csv(f, sep='\t', header=None, names=['url_id', 'url', 'title', 'content'])
    with open(result_path, 'w', encoding='utf-8') as wf:
        res = []
        for i in range(len(news_data)):
            id, title, content = news_data.iloc[i]['url_id'], news_data.iloc[i]['title'], news_data.iloc[i][
                'content']
            if title and content and isinstance(title, str) and isinstance(content, str):
                text = title + content
                clean_text = chinese_word_extraction(text)
                keys = ','.join(extract_tags(clean_text))
                res.append('{} {}\n'.format(id, keys))

        wf.writelines(res)


def extract_ads(path, result_path):
    ad_data = pd.read_csv(path, sep='\t', header=None, encoding='utf-8',
                          names=['spread_id', 'keys', 'pri_industry',
                                 'sec_industry', 'pri_id', 'sec_id',
                                 'title', 'dec', 'sub_title'])
    with open(result_path, 'w', encoding='utf-8') as wf:
        res = []
        for i in range(len(ad_data)):
            data = ad_data.iloc[i]
            id, key_text, pri_industry, sec_industry = (data['spread_id'], data['keys'],
                                                        data['pri_industry'], data['sec_industry'])

            # 暂时不适用title, dec, sub_title，这些广告词对词频计算干扰非常大
            # text = key_text + pri_industry + sec_industry + title + dec + sub_title
            text = key_text + pri_industry + sec_industry
            clean_text = chinese_word_extraction(text)
            keys = ','.join(extract_ads_tags(clean_text))
            res.append('{} {}\n'.format(id, keys))
        wf.writelines(res)


def extract_tags(text, topK=10):
    tf_tags = utils.extract_tags(text, topK=topK)
    rank_tags = utils.textrank(text, topK=topK)
    # 取tfidf和textrank结果的并集
    return set(tf_tags + rank_tags)


# 使用正则表达式去除数字、标点符号等，提取中文
def chinese_word_extraction(text):
    chi_pattern = re.compile(u'([\u4e00-\u9fa5]+)')
    re_data = chi_pattern.findall(text)
    text_clean = ' '.join(re_data)
    return text_clean


def extract_ads_tags(text, topK=10):
    stop_words_path = 'utils/stopwords.txt'
    stop_words = set()
    content = open(stop_words_path, 'rb').read().decode('utf-8')
    for line in content.splitlines():
        stop_words.add(line)

    words = jieba.cut(text)
    freq = {}
    for word in words:
        if word not in stop_words:
            freq[word] = freq.get(word, 0.0) + 1.0
    return sorted(freq, key=freq.__getitem__, reverse=True)[:topK]


if __name__ == "__main__":
    cp = ConfigParser()
    cp.read("config/path.cfg")

    ad_path = cp.get("raw_data", "ad")
    ad_result_path = cp.get("keys", "ad")

    news_path = cp.get("raw_data", "news")
    news_result_path = cp.get("keys", "news")

    print("Extracting ads keys...")
    extract_ads(path=ad_path, result_path=ad_result_path)
    print("ads keys extracted finished.")

    print("Extracting news keys...")
    extract_news(path=news_path, result_path=news_result_path)
    print("news keys extracted finished.")
