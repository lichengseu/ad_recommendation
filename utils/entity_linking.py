# -*- coding: utf-8 -*-

"""
# @Author  : licheng
# @Time    : 2018/12/1 11:01
# @Ide     : PyCharm
"""
import urllib.parse
from configparser import ConfigParser
from franz.openrdf.connect import ag_connect


class EntityLinking:
    def __init__(self, kg_config_path):
        cp = ConfigParser()
        cp.read(kg_config_path)

        self.prefix = "<http://localkg.cn/entity/%s>"
        self.conn = ag_connect(repo=cp.get("repository", "repo"), catalog=cp.get("repository", "catalog"),
                               host=cp.get("server", "host"),
                               user=cp.get("account", "user"), password=cp.get("account", "password"))

    # 链接
    def link_entities(self, keywords_set):
        keywords_uri_set = set([self.prefix % urllib.parse.quote(keyword) for keyword in keywords_set])
        keywords_uri_set, inverse_redirect_dict = self._disambiguate_entities(keywords_uri_set)[:2]

        abstracts = dict()
        internal_links = dict()
        query_string = "PREFIX ontology:<http://localkg.cn/ontology/> " \
                       "select ?s ?o " \
                       "{VALUES ?s {%s} " \
                       "?s ontology:%s ?o}"
        with self.conn.executeTupleQuery(query_string % (" ".join(list(keywords_uri_set)), 'abstract')) as results:
            for res in results:
                if str(res['s']) in inverse_redirect_dict:
                    subject = self._decode_uri(inverse_redirect_dict[str(res['s'])])
                else:
                    subject = self._decode_uri(str(res['s']))
                abstracts[subject] = str(res['o'])

        with self.conn.executeTupleQuery(query_string % (" ".join(list(keywords_uri_set)), 'internalLink')) as results:
            for res in results:
                if str(res['s']) in inverse_redirect_dict:
                    subject = self._decode_uri(inverse_redirect_dict[str(res['s'])])
                else:
                    subject = self._decode_uri(str(res['s']))

                if subject not in internal_links:
                    internal_links[subject] = set()
                internal_links[subject].add(self._decode_uri(str(res['o'])))

        return [abstracts, internal_links]

    # 消歧
    def _disambiguate_entities(self, keywords_uri_set):
        query_string = "PREFIX ontology:<http://localkg.cn/ontology/> " \
                       "select ?s ?o " \
                       "{VALUES ?s {%s} " \
                       "?s ontology:pageRedirects ?o}" % (" ".join(list(keywords_uri_set)))
        inverse_redirect_dict = dict()
        with self.conn.executeTupleQuery(query_string) as results:
            for res in results:
                subject = str(res['s'])
                object = str(res['o'])
                keywords_uri_set.remove(subject)
                keywords_uri_set.add(object)
                inverse_redirect_dict[object] = subject
        return [keywords_uri_set, inverse_redirect_dict]

    def _decode_uri(self, uri):
        return urllib.parse.unquote(uri.split("/")[-1].rstrip(">"))

    def __del__(self):
        if self.conn:
            self.conn.close()

