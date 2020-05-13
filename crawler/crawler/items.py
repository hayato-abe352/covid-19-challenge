# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Covid19ChallengeItem(scrapy.Item):
    # 都道府県コード
    pref_code = scrapy.Field()
    # 都道府県症例番号
    pref_patient_no = scrapy.Field()
    # 都道府県名
    pref_name = scrapy.Field()

    # 確定日 (新型コロナウイルス検査に対して陽性が判明した日)
    fixed_date = scrapy.Field()
    # 年代
    # (0 - 9, 10 - 19, 20 - 29, 30 - 39, 40 - 49, 50 - 59, 60 - 69, 70 - 79,
    # 80 - 89, 90 -, 非公表, NA)
    age = scrapy.Field()
    # 性別 (男性, 女性, その他, 非公表)
    gender = scrapy.Field()
    # 居住地
    residence = scrapy.Field()
    # 職業
    occupation = scrapy.Field()
    information_source = scrapy.Field()


class Covid19ChallengeDocumentItem(scrapy.Item):
    # ファイル名
    file_name = scrapy.Field()
    # 都道府県コード
    pref_code = scrapy.Field()
    # 都道府県名
    pref_name = scrapy.Field()
    # リンクテキスト
    label = scrapy.Field()
    # URL
    href = scrapy.Field()
    # 最終更新日時
    last_modified = scrapy.Field()
