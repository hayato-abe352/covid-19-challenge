# -*- coding: utf-8 -*-
from datetime import datetime

import scrapy
from hashids import Hashids

import crawler.constants as constants
from crawler.items import Covid19ChallengeDocumentItem, Covid19ChallengeItem


class NiigataSpider(scrapy.Spider):
    name = "niigata_spider"
    allowed_domains = ["www.pref.niigata.lg.jp", "www.city.niigata.lg.jp"]
    start_urls = [
        "https://www.pref.niigata.lg.jp/sec/kikitaisaku/"
        "hasseijokyo-covid19-niigataken.html"
    ]

    pref_code = 15
    pref_name = "新潟県"
    pref_name_en = "niigata"
    hashids = Hashids()

    def parse(self, response):
        # 発生状況テーブルを取得
        table = response.css("table[summary='県内における感染者の発生状況']")

        # 発生状況テーブルをループ (先頭行はヘッダなのでスキップ)
        for tr in table.css("tr")[1:]:
            item = Covid19ChallengeItem()

            td_list = tr.css("td::text").extract()
            case_data = []
            for td in td_list:
                if "\n" in td:
                    # 改行を含むデータ(セル内の折り返し)は1つ前のデータに連結
                    case_data[len(case_data) - 1] = "{} {}".format(
                        case_data[len(case_data) - 1], td.replace("\n", "")
                    )
                else:
                    case_data.append(td)

            # 都道府県コード
            item["pref_code"] = self.pref_code
            # 都道府県名
            item["pref_name"] = self.pref_name
            # 都道府県症例番号
            item["pref_patient_no"] = case_data[0]

            # 確定日
            fixed_date_str = case_data[2]
            # 末尾の曜日部分を除去
            fixed_date_str = fixed_date_str[:-3]
            # 年月日書式に変更
            fixed_date_str = "2020年{}".format(fixed_date_str)
            # YYYY/MM/DD書式に変更
            fixed_date = datetime.strptime(fixed_date_str, "%Y年%m月%d日")
            item["fixed_date"] = fixed_date.strftime("2020/%m/%d")

            # 年代 (10歳代を 10 - 19 形式に変換)
            age_str = case_data[3]
            if "10歳未満" in age_str:
                # 10歳未満の場合のみ0-9固定
                item["age"] = constants.AGE_LIST[0]
            else:
                # 先頭の年代2文字を取得し、リストから年代を取得
                age = int(age_str[:2])
                item["age"] = constants.AGE_LIST[age // 10]

            # 性別
            item["gender"] = case_data[4]

            # 居住地
            item["residence"] = case_data[5]

            # 職業
            item["occupation"] = case_data[6]

            yield item

            # 報道資料へのリンクをリストに追加
            href = tr.css("a::attr(href)").get()
            if href is not None and "www.city.niigata.lg.jp" not in href:
                href = response.urljoin(href)
                request = scrapy.Request(
                    href, callback=self.parse_pref_niigata
                )
                yield request

        # 新潟市のHPへ遷移
        request = scrapy.Request(
            "https://www.city.niigata.lg.jp/"
            "iryo/kenko/yobou_kansen/kansen/coronavirus.html",
            callback=self.parse_city_niigata,
        )
        yield request

        # 新潟市HP 過去の報道資料へ遷移
        request = scrapy.Request(
            "https://www.city.niigata.lg.jp/"
            "iryo/kenko/yobou_kansen/kansen/covid-19/houdou/index.html",
            callback=self.parse_city_niigata_index,
        )
        yield request

    def parse_city_niigata_index(self, response):
        links = response.css("ul.norcor > li > a")
        for link in links:
            href = link.css("::attr(href)").get()

            request = scrapy.Request(
                response.urljoin(href), callback=self.parse_city_niigata
            )
            yield request

    def parse_city_niigata(self, response):
        pdf_links = response.css("a.pdf")
        for pdf_link in pdf_links:
            href = pdf_link.css("*::attr(href)").get()
            if "press" not in href:
                continue

            label = pdf_link.css("*::text").get()
            request = scrapy.Request(
                response.urljoin(href), callback=self.parse_documents
            )
            item = Covid19ChallengeDocumentItem()
            item["label"] = label
            request.meta["item"] = item
            yield request

    def parse_pref_niigata(self, response):
        pdf_links = response.css("div.detail_free > p > a")

        for pdf_link in pdf_links:
            href = pdf_link.css("*::attr(href)").get()
            label = pdf_link.css("*::text").get()
            request = scrapy.Request(
                response.urljoin(href), callback=self.parse_documents
            )
            item = Covid19ChallengeDocumentItem()
            item["label"] = label
            request.meta["item"] = item
            yield request

    def parse_documents(self, response):
        item = response.meta["item"]
        # ファイル名
        item["file_name"] = response.url.split("/")[-1]
        item["pref_code"] = self.pref_code
        item["pref_name"] = self.pref_name
        item["href"] = response.url
        item["last_modified"] = response.headers.get("Last-Modified")

        if item["last_modified"]:
            # datetimeに変換
            item["last_modified"] = datetime.strptime(
                item["last_modified"].decode("utf-8"),
                "%a, %d %b %Y %H:%M:%S %Z",
            )

        yield item
