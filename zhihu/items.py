# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class ZhihuItem(Item):
    # define the fields for your item here like:
    # name = Field()
    user_id = Field()
    user_image_url = Field()
    name = Field()
    locations = Field()
    business = Field() # 所在行业
    employments = Field() # 职业经历
    gender = Field()
    education = Field()
    followees_num = Field() # 我关注的人数
    followers_num = Field() # 关注我的人数


class RelationItem(Item):
    user_id = Field()
    relation_type = Field() # 关系类型
    relations_id = Field()


class AnswerItem(Item):
    answer_user_id = Field()
    answer_id = Field()
    question_id = Field()
    cretated_time = Field()
    updated_time = Field()
    voteup_count = Field()
    comment_count = Field()
    content = Field()


class QuestionItem(Item):
    ask_user_id = Field()
    question_id = Field()
    ask_time = Field()
    answer_count = Field()
    followees_count = Field()
    title = Field()


class ArticleItem(Item):
    author_id = Field()
    title = Field()
    article_id = Field()
    content = Field()
    cretated_time = Field()
    updated_time = Field()
    voteup_count = Field()
    comment_count = Field()