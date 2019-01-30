# -*- coding: utf-8 -*-

"""
# @Author  : licheng
# @Time    : 2018/1/3 14:12
# @Ide     : PyCharm

Recommend ad keywords to news according the previously recommended advertisers
"""
from __future__ import division
from multiprocessing import Process
from configparser import ConfigParser
from recommend_advertisers import load_keys
from extract_keys import extract_ads_tags, chinese_word_extraction

import os
import utils
import math


def load_reco_aders(path, separator=" "):
    with open(path, 'r', encoding="utf-8") as rf:
        result = []
        for line in rf.readlines():
            news_id, reco_aders = line.rstrip("\r\n").split(separator)[:2]
            result.append([news_id, set(reco_aders.split(","))])
        return result


def get_news_context(keys, linker):
    abstracts_dict, links_dict = linker.link_entities(keys)[:2]
    abstracts, links = set(), set()
    for abstract in abstracts_dict.values():
        abstracts.add(abstract)
    for links_set in links_dict.values():
        links |= links_set
    return [abstracts, links]


def get_ads_context(keys, linker):
    abstracts_dict, links_dict = linker.link_entities(keys)[:2]
    return [abstracts_dict, links_dict]


def get_ads_keys(ad_ids, ads_dict):
    keys_set = set()
    keys_dict = dict()
    for ad_id in ad_ids:
        for ad_keyword in ads_dict[ad_id]:
            keys = extract_ads_tags(chinese_word_extraction(ad_keyword))
            keys_dict[ad_keyword] = keys
            keys_set |= set(keys)
    return [keys_set, keys_dict]


def cal_similarity(news_context, ad_keyword_context):
    abstract_similarity = len(news_context[0] & ad_keyword_context[0]) / (len(ad_keyword_context[0]) + 1)
    links_similarity = len(news_context[1] & ad_keyword_context[1]) / (len(ad_keyword_context[1]) + 1)
    return abstract_similarity + links_similarity


def recommend_ad_keywords(path, reco_aders_dict, ads_dict, news_dict, linker, topk=10):
    with open(path, 'w', encoding="utf-8") as wf:
        for res in reco_aders_dict:
            news_id, reco_aders = res[:]
            print(news_id)
            news_abstracts, news_links = get_news_context(news_dict[news_id], linker)[:]

            ad_keys_set, ad_keys_dict = get_ads_keys(reco_aders, ads_dict)[:]
            ad_abstracts_dict, ad_links_dict = get_ads_context(ad_keys_set, linker)

            reco_results = []
            for ad_id in reco_aders:
                results = []
                for ad_keyword in ads_dict[ad_id]:
                    keyword_abstracts, keyword_links = set(), set()
                    for key in ad_keys_dict[ad_keyword]:
                        if key in ad_abstracts_dict:
                            keyword_abstracts.add(ad_abstracts_dict[key])
                        if key in ad_links_dict:
                            keyword_links |= ad_links_dict[key]

                    sim = cal_similarity([news_abstracts, news_links], [keyword_abstracts, keyword_links])
                    results.append((ad_keyword, sim))
                results = sorted(results, key=lambda item: -item[1])[:topk]
                reco_results += [res[0] for res in results]
            wf.write("%s\t%s\n" % (news_id, ",".join(set(reco_results))))


if __name__ == "__main__":
    cp = ConfigParser()
    cp.read("config/path.cfg")

    kg_config_path = "config/kg.cfg"
    ads_path = cp.get("raw_data", "ad")
    news_keys_path = cp.get("keys", "news")
    reco_aders_path = cp.get("recommendation", "advertisers")
    reco_result_path = cp.get("recommendation", "ad_keywords")

    cp.read("config/parameter.cfg")
    topk = int(cp.get("ad_keywords", "topk"))
    process_number = int(cp.get("process", "process_number"))

    ad_keywords_dict = load_keys(ads_path, separator="\t")
    news_keys_dict = load_keys(news_keys_path, separator=" ")
    linker = utils.EntityLinking(kg_config_path)

    reco_aders_dict = load_reco_aders(reco_aders_path)

    total_length = len(reco_aders_dict)
    gap = math.ceil(total_length / process_number)

    processes = []
    result_paths = []
    for i in range(process_number):
        tmp_result_path = reco_result_path.replace(".txt", "_tmp%d.txt" % i)
        start = i * gap
        end = min((i + 1)*gap, total_length)

        process = Process(target=recommend_ad_keywords, args=(tmp_result_path, reco_aders_dict[start:end],
                                                              ad_keywords_dict, news_keys_dict, linker, topk))
        processes.append(process)
        result_paths.append(tmp_result_path)

    print("recommending ad keywords...")
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    with open(reco_result_path, 'w', encoding="utf-8") as wf:
        for tmp_result_path in result_paths:
            wf.writelines(open(tmp_result_path, 'r', encoding="utf-8").readlines())
            os.remove(tmp_result_path)
