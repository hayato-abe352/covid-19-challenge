# -*- coding: utf-8 -*-
import os
import re

import scrapy
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTContainer, LTTextBox
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

from crawler.items import Covid19ChallengeItem
from crawler.utils import convert_date_ja_to_ad

PREF_CODE = 15
PREF_NAME = "新潟県"


class NiigataSpider(scrapy.Spider):
    name = "niigata_spider"
    allowed_domains = ["www.pref.niigata.lg.jp", "www.city.niigata.lg.jp"]
    start_urls = [
        "http://www.pref.niigata.lg.jp/sec/kikitaisaku/shingata-corona.html"
    ]

    def parse(self, response):
        # detail_free配下の2つ目のulが発生状況リスト
        ul = response.css(".detail_free > ul")[1]
        for li in ul.css("li"):
            src_label = "".join(li.css("*::text").getall())
            patients = re.search("県内(.*?)例目", src_label).group(1)
            date_ja = re.search(r"令和\d+年\d+月[\s0-9]+日", src_label).group()
            date_ja = re.sub(r"\s+", "", date_ja)

            if "～" in patients:
                # 3件以上が同日に発生
                dash_index = patients.find("～")
                patient_no_min = int(patients[0:dash_index])
                dash_index = dash_index + 1
                patient_no_max = int(patients[dash_index:])
                patients = list(range(patient_no_min, patient_no_max + 1))
            elif "、" in patients:
                # 2件が同日に発生
                comma_index = patients.find("、")
                patient_no_first = patients[0:comma_index]
                comma_index = comma_index + 1
                patient_no_second = patients[comma_index:]
                patients = [patient_no_first, patient_no_second]
            else:
                patients = [patients]

            for patient_no in patients:
                item = Covid19ChallengeItem()
                item["pref_code"] = PREF_CODE
                item["pref_name"] = PREF_NAME
                item["date_ja"] = date_ja
                item["publication_date"] = convert_date_ja_to_ad(
                    item["date_ja"]
                )
                item["pref_patient_no"] = patient_no
                item["patient_id"] = "{}-{}".format(PREF_CODE, patient_no)

                href = li.css("a::attr(href)").get()
                if "www.city.niigata.lg.jp" in href:
                    # 新潟市HPへのリンクの場合
                    request = scrapy.Request(
                        href,
                        callback=self.parse_city_niigata,
                        dont_filter=True,
                    )
                    request.meta["item"] = item
                    yield request
                else:
                    # 新潟市以外のリンク (報道資料への直リンク) の場合
                    href = response.urljoin(href)
                    request = scrapy.Request(
                        href, callback=self.parse_pref_niigata
                    )
                    request.meta["item"] = item
                    yield request

    def parse_city_niigata(self, response):
        # 新潟市のHPから日付の一致する資料を探す
        item = response.meta["item"]
        pdf_links = response.css("a.pdf")
        pdf_links = [
            response.urljoin(x.css("*::attr(href)").get())
            for x in pdf_links
            if item["date_ja"] in x.get()
        ]

        if not pdf_links:
            # 資料がなければ過去ページに遷移する
            href = response.css(".linktxt > .innerLink::attr(href)").get()
            href = response.urljoin(href)
            request = scrapy.Request(
                href, callback=self.parse_city_niigata, dont_filter=True
            )
            request.meta["item"] = item
            yield request
        else:
            item["information_source"] = "; ".join(pdf_links)
            for pdf_link in pdf_links:
                request = scrapy.Request(
                    pdf_link, callback=self.save_pdf, dont_filter=True
                )
                request.meta["item"] = item
                yield request
            yield item

    def parse_pref_niigata(self, response):
        item = response.meta["item"]
        pdf_links = response.css(
            "div.detail_free > p > a::attr(href)"
        ).getall()
        pdf_links = [response.urljoin(x) for x in pdf_links]

        item["information_source"] = "; ".join(pdf_links)
        for pdf_link in pdf_links:
            request = scrapy.Request(
                pdf_link, callback=self.save_pdf, dont_filter=True
            )
            request.meta["item"] = item
            yield request

        yield item

    def save_pdf(self, response):
        os.makedirs("output/temp/niigata/pdf", exist_ok=True)
        pdf_file = os.path.join(
            "output/temp/niigata/pdf", response.url.split("/")[-1]
        )

        # ファイルの保存
        if os.path.exists(pdf_file):
            # 既に存在すればスキップ
            return

        with open(pdf_file, "wb") as f:
            f.write(response.body)

        # PDFのテキスト抽出
        laparams = LAParams(detect_vertical=True)
        resource_manager = PDFResourceManager()
        device = PDFPageAggregator(resource_manager, laparams=laparams)
        interpreter = PDFPageInterpreter(resource_manager, device)

        os.makedirs("output/temp/niigata/text", exist_ok=True)
        text_file = os.path.splitext(os.path.basename(pdf_file))[0] + ".txt"
        text_file = os.path.join("output/temp/niigata/text", text_file)
        with open(pdf_file, "rb") as pdf_f:
            with open(text_file, "w", encoding="utf-8") as text_f:
                for page in PDFPage.get_pages(pdf_f):
                    interpreter.process_page(page)
                    layout = device.get_result()

                    boxes = self.get_pdf_textbox_list(layout)
                    boxes.sort(key=lambda b: (-b.y1, b.x0))

                    for box in boxes:
                        text_f.write(box.get_text().strip())

    def get_pdf_textbox_list(self, pdf_layout_obj):

        if isinstance(pdf_layout_obj, LTTextBox):
            return [pdf_layout_obj]

        if isinstance(pdf_layout_obj, LTContainer):
            boxes = []
            for child in pdf_layout_obj:
                boxes.extend(self.get_pdf_textbox_list(child))

            return boxes

        return []
