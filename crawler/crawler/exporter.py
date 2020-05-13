from firebase_admin import firestore
from scrapy.exporters import CsvItemExporter


class Covid19PatientsExporter(CsvItemExporter):
    def __init__(
        self, file, include_headers_line=True, join_multivalued=",", **kwargs
    ):
        super().__init__(
            file,
            include_headers_line=include_headers_line,
            join_multivalued=join_multivalued,
            **kwargs
        )

    def start_exporting(self):
        self.items = []

    def export_item(self, item):
        self.items.append(item)

    def finish_exporting(self):
        self.items.sort(key=lambda x: int(x["pref_patient_no"]))
        db = firestore.client()
        batch = db.batch()
        batch_set_count = 0
        for item in self.items:
            super().export_item(item)

            if batch_set_count >= 100:
                batch.commit()
                batch_set_count = 0

            item = dict(item)
            doc_ref = db.document(
                "Covid19Challenge/Patients/{}/{:08}".format(
                    item["pref_code"], int(item["pref_patient_no"])
                )
            )
            doc = doc_ref.get().to_dict() or {}
            if doc:
                del doc["isChecked"]

            if item.items() - doc.items():
                # 差分がある場合
                item["isChecked"] = False
                batch.set(doc_ref, item)
                batch_set_count += 1

        if batch_set_count > 0:
            batch.commit()


class Covid19DocumentsExporter(CsvItemExporter):
    def __init__(
        self, file, include_headers_line=True, join_multivalued=",", **kwargs
    ):
        super().__init__(
            file,
            include_headers_line=include_headers_line,
            join_multivalued=join_multivalued,
            **kwargs
        )

    def start_exporting(self):
        self.items = []

    def export_item(self, item):
        self.items.append(item)

    def finish_exporting(self):
        self.items.sort(key=lambda x: (x["last_modified"], x["file_name"]))

        db = firestore.client()
        batch = db.batch()
        batch_set_count = 0

        for item in self.items:
            super().export_item(item)

            if batch_set_count >= 100:
                batch.commit()
                batch_set_count = 0

            item = dict(item)
            doc_ref = db.document(
                "Covid19Challenge/Documents/{}/{}".format(
                    item["pref_code"], item["file_name"]
                )
            )
            doc = doc_ref.get().to_dict() or {}
            if doc:
                del doc["isChecked"]

            if item.items() - doc.items():
                # 差分がある場合
                item["isChecked"] = False
                batch.set(doc_ref, item)
                batch_set_count += 1

        if batch_set_count > 0:
            batch.commit()
