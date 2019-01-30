# -*- coding: utf-8 -*-

"""
# @Author  : licheng
# @Time    : 2018/12/30 10:47
# @Ide     : PyCharm

Recommend advertisers to news.
Note: The recommended ad keywords will be selected from these recommended advertisers.
"""
from configparser import ConfigParser


def load_keys(path, separator=" "):
    with open(path, 'r', encoding="utf-8") as rf:
        keys_dict = dict()
        for line in rf.readlines():
            id, keys = line.rstrip("\r\n").split(separator)[:2]
            keys_dict[id] = set(keys.split(","))
        return keys_dict


def recommend_advertisers(ad_keys_path, news_keys_path, result_path, threshold=2):
    ad_keys_dict = load_keys(ad_keys_path)
    news_keys_dict = load_keys(news_keys_path)

    with open(result_path, 'w', encoding="utf-8") as wf:
        results = []
        for news_id, news_keys_set in news_keys_dict.items():
            recommended_advertisers = set()
            for ad_id, ad_keys_set in ad_keys_dict.items():
                if len(news_keys_set & ad_keys_set) > threshold:
                    recommended_advertisers.add(ad_id)
            if len(recommended_advertisers) != 0:
                results.append("%s %s\n" % (news_id, ",".join(recommended_advertisers)))
        wf.writelines(results)


if __name__ == "__main__":
    cp = ConfigParser()
    cp.read("config/path.cfg")

    ad_keys_path = cp.get("keys", "ad")
    news_keys_path = cp.get("keys", "news")
    result_path = cp.get("recommendation", "advertisers")

    cp.read("config/parameter.cfg")
    threshold = int(cp.get("advertisers", "threshold"))

    print("recommending advertisers...")
    recommend_advertisers(ad_keys_path, news_keys_path, result_path, threshold=threshold)
