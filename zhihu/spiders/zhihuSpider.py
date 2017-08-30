#-*- coding:utf-8 -*-
"""
@Author: Jeff Zhang
@Time:   17-8-30 下午3:14
@File:   zhihuSpider.py
"""



import scrapy
import re
import json
from scrapy.http import Request
from zhihu.items import ZhihuItem,RelationItem,AnswerItem,QuestionItem,ArticleItem
from zhihu.scrapy_redis.spiders import RedisSpider
from scrapy import Spider
import time


class ZhihuSpider(Spider):
    name = "zhihuspider"
    redis_key = "zhihuspider:start_urls"
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://zhihu.com/']
    start_user_id = ['excited-vczh']

    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'locations,employments,industry_category,gender,educations,business,follower_count,following_count,description,badge[?(type=best_answerer)].topics'

    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    answers_url = ''

    def start_requests(self):
        for user_id in self.start_user_id:
            yield Request(
                'https://www.zhihu.com/api/v4/members/' + user_id + '?include=locations,employments,industry_category,gender,educations,business,follower_count,following_count,description,badge[?(type=best_answerer)].topics',
                meta={'user_id': user_id}, callback=self.parse_user)


    def parse_user(self, response):
        json_results = json.loads(response.text)
        item = ZhihuItem()
        # 获取性别
        if json_results['gender'] == 1:
            item['gender'] = u'男'
        elif json_results['gender'] == 0:
            item['gender'] = u'女'
        else:
            item['gender'] = u'未知'
        item['user_id'] = json_results['url_token']
        item['user_image_url'] = json_results['avatar_url']
        item['name'] = json_results['name']

        # 获取居住地
        item['locations'] = []
        try:
            for location in json_results['locations']:
                item['locations'].append(location['name'])
        except:
            pass

        # 获取行业
        try:
            item['business'] = json_results['business']['name']
        except:
            try:
                item['business'] = json_results['industry_category']
            except:
                item['business'] = u'未知'

        #获取教育情况
        item['education'] = []
        for element in json_results['educations']:
            try:
                education = element['school']['name'] + "-" + element['major']['name']
                item['education'].append(education)
            except:
                try:
                    education = element['school']['name']
                    item['education'].append(education)
                except:
                    pass

        item['followees_num'] = json_results['following_count']
        item['followers_num'] = json_results['follower_count']

        # 获取工作情况
        item['employments'] = []
        for element in json_results['employments']:
            try:
                employment = element['company']['name'] + "-" + element['job']['name']
                item['employments'].append(employment)
            except:
                try:
                    employment = element['company']['name']
                    item['employments'].append(employment)
                except:
                    pass

        yield item

        item = RelationItem()
        user_id = response.meta['user_id']
        item['relations_id'] = []
        item['user_id'] = user_id
        item['relation_type'] = ''

        yield Request('https://www.zhihu.com/api/v4/members/'+user_id+'/followers?include=data[*].answer_count,badge[?(type=best_answerer)].topics&limit=20&offset=0',callback=self.parse_relation,meta={'item':item, 'offset':0, 'relation_type':'followers'})
        yield Request('https://www.zhihu.com/api/v4/members/'+user_id+'/followees?include=data[*].answer_count,badge[?(type=best_answerer)].topics&limit=20&offset=0',callback=self.parse_relation,meta={'item':item, 'offset':0, 'relation_type':'followees'})
        yield Request('https://www.zhihu.com/api/v4/members/'+user_id+'/answers?include=data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,collapsed_by,suggest_edit,comment_count,can_comment,content,voteup_count,reshipment_settings,comment_permission,mark_infos,created_time,updated_time,review_info,question,excerpt,relationship.is_authorized,voting,is_author,is_thanked,is_nothelp,upvoted_followees;data[*].author.badge[?(type=best_answerer)].topics&limit=20&offset=0',callback=self.parse_answer,meta={'answer_user_id':user_id,'offset':0})
        yield Request('https://www.zhihu.com/api/v4/members/'+user_id+'/questions?include=data[*].created,answer_count,follower_count,author,admin_closed_comment&limit=20&offset=0',callback=self.parse_question,meta={'ask_user_id':user_id,'offset':0})
        yield Request('https://www.zhihu.com/api/v4/members/'+user_id+'/articles?include=data[*].comment_count,can_comment,comment_permission,admin_closed_comment,content,voteup_count,created,updated,upvoted_followees,voting,review_info;data[*].author.badge[?(type=best_answerer)].topics&limit=20&offset=0',callback=self.parse_article,meta={'author_id':user_id,'offset':0})


    def parse_relation(self, response):
        json_results = json.loads(response.text)
        relations_id = []
        for user_info in json_results['data']:
            relations_id.append(user_info['url_token'])
        response.meta['item']['relations_id'] = relations_id

        if response.meta['offset'] == 0:
            response.meta['item']['relation_type'] = response.meta['relation_type']
        else:
            response.meta['item']['relation_type'] = 'next:' + response.meta['relation_type']

        yield response.meta['item']

        for user_id in response.meta['item']['relations_id']:
            yield Request(
                'https://www.zhihu.com/api/v4/members/' + user_id + '?include=locations,employments,industry_category,gender,educations,business,follower_count,following_count,description,badge[?(type=best_answerer)].topics',
                meta={'user_id': user_id}, callback=self.parse_user)

        if json_results['paging']['is_end'] == False:
            offset = response.meta['offset'] + 20
            next_page = re.findall('(.*offset=)\d+', response.url)[0]
            yield Request(next_page + str(offset), callback=self.parse_relation,
                          meta={'item': response.meta['item'], 'offset': offset,
                                'relation_type': response.meta['relation_type']})

    def parse_article(self, response):
        json_results = json.loads(response.text)
        for result in json_results['data']:
            item = ArticleItem()
            item['author_id'] = response.meta['author_id']
            item['title'] = result['title']
            item['article_id'] = result['id']
            item['content'] = result['content']
            item['cretated_time'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['created']))
            item['updated_time'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['updated']))
            item['voteup_count'] = result['voteup_count']
            item['comment_count'] = result['comment_count']
            yield item
            if json_results['paging']['is_end'] == False:
                offset = response.meta['offset'] + 20
                next_page = re.findall('(.*offset=)\d+', response.url)[0]
                yield Request(next_page + str(offset), callback=self.parse_article,
                              meta={'author_id': response.meta['author_id'], 'offset': offset})

    def parse_answer(self, response):
        json_results = json.loads(response.text)
        for result in json_results['data']:
            item = AnswerItem()
            item['answer_user_id'] = response.meta['answer_user_id']
            item['answer_id'] = result['id']
            item['cretated_time'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['created_time']))
            item['updated_time'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['updated_time']))
            item['voteup_count'] = result['voteup_count']
            item['comment_count'] = result['comment_count']
            item['content'] = result['content']
            yield item
        if json_results['paging']['is_end'] == False:
            offset = response.meta['offset'] + 20
            next_page = re.findall('(.*offset=)\d+', response.url)[0]
            yield Request(next_page + str(offset), callback=self.parse_answer,
                          meta={'answer_user_id': response.meta['answer_user_id'], 'offset': offset})




    def parse_question(self, response):
        json_results = json.loads(response.text)
        for result in json_results['data']:
            item = QuestionItem()
            item['ask_user_id'] = response.meta['ask_user_id']
            item['title'] = result['title']
            item['question_id'] = result['id']
            item['ask_time'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['created']))
            item['answer_count'] = result['answer_count']
            item['followees_count'] = result['follower_count']
            yield item
        if json_results['paging']['is_end'] == False:
            offset = response.meta['offset'] + 20
            next_page = re.findall('(.*offset=)\d+', response.url)[0]
            yield Request(next_page + str(offset), callback=self.parse_question,
                          meta={'ask_user_id': response.meta['ask_user_id'], 'offset': offset})



