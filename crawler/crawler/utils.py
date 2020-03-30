import re
from datetime import datetime


def convert_date_ja_to_ad(date_ja_str):
    """
    和暦書式の日付文字列を西暦書式の日付文字列へ変換します。
    例： 令和2年3月26日 → 2020/03/26
    ※取り急ぎ令和のみ対応 (年度パターンも必要か)
    """
    year_ja = re.search(r"令和(\d+)年", date_ja_str).group(1)
    year_ad = int(year_ja) + 2018

    date_ja = re.sub(r"令和(\d+)年", "", date_ja_str)
    return datetime.strptime(
        "{}年{}".format(year_ad, date_ja), "%Y年%m月%d日"
    ).strftime("%y/%m/%d")
