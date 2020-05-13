# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os

import firebase_admin

from crawler.exporter import Covid19DocumentsExporter, Covid19PatientsExporter
from crawler.items import Covid19ChallengeDocumentItem, Covid19ChallengeItem


class Covid19ChallengePipeline(object):
    def __init__(self, settings={}):
        self.settings = settings
        firebase_admin.initialize_app()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def open_spider(self, spider):
        pref_code = spider.pref_code
        pref_name_en = spider.pref_name_en

        export_dir = "output/{}_{}".format(pref_code, pref_name_en)
        os.makedirs(export_dir, exist_ok=True)

        patients_file_path = "{}/patients.csv".format(export_dir)
        self.patients_file = open(patients_file_path, "wb")

        documents_file_path = "{}/documents.csv".format(export_dir)
        self.documents_file = open(documents_file_path, "wb")

        self.patients_exporter = Covid19PatientsExporter(
            self.patients_file,
            include_headers_line=True,
            join_multivalued=",",
            fields_to_export=self.settings["FEED_EXPORT_FIELDS_PATIENTS"],
        )

        self.documents_exporter = Covid19DocumentsExporter(
            self.documents_file,
            include_headers_line=True,
            join_multivalued=",",
            fields_to_export=self.settings["FEED_EXPORT_FIELDS_DOCUMENTS"],
        )

        self.patients_exporter.start_exporting()
        self.documents_exporter.start_exporting()

    def close_spider(self, spider):
        self.patients_exporter.finish_exporting()
        self.patients_file.close()

        self.documents_exporter.finish_exporting()
        self.documents_file.close()

    def process_item(self, item, spider):

        if type(item) is Covid19ChallengeItem:
            self.patients_exporter.export_item(item)
        elif type(item) is Covid19ChallengeDocumentItem:
            self.documents_exporter.export_item(item)

        return item
