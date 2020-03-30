# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Covid19ChallengeItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    patient_id = scrapy.Field()
    pref_code = scrapy.Field()
    pref_patient_no = scrapy.Field()
    publication_date = scrapy.Field()
    pref_name = scrapy.Field()
    information_source = scrapy.Field()

    date_ja = scrapy.Field()
    src_label = scrapy.Field()
