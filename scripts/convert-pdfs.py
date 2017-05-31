#!/usr/bin/env python
import pdfplumber
import pandas as pd
import re
import sys, os

COLUMNS = [
    "club", "last_name", "first_name",
    "position", "base_salary", "guaranteed_compensation"
]

NON_MONEY_CHAR_PAT = re.compile(r"[^\d\.]")

def parse_money(money_str):
    stripped = re.sub(NON_MONEY_CHAR_PAT, "", money_str)
    if len(stripped):
        return float(stripped)
    else:
        return None

def get_data_bbox(page):
    words = page.extract_words()
    texts = [ w["text"] for w in words ]
    first_cell_ix = texts.index("Compensation") + 1
    last_cell_ix = texts.index("Source:")
    data_words = words[first_cell_ix:last_cell_ix]
    dw_df = pd.DataFrame(data_words)

    return (
        dw_df["x0"].min(),
        dw_df["top"].min(),
        dw_df["x1"].max(),
        dw_df["bottom"].max(),
    )

def get_gutters(cropped):
    x0s = pd.DataFrame(cropped.chars)["x0"].astype(float)\
        .sort_values()\
        .drop_duplicates()

    gutter_ends = pd.DataFrame({
        "x0": x0s,
        "dist": x0s - x0s.shift(1),
    }).sort_values("dist", ascending=False)\
        .pipe(lambda x: x[x["dist"] > 10])["x0"].sort_values()\
        .astype(int).tolist()

    return gutter_ends

def parse_page(page, year):
    sys.stderr.write("{}, page {}\n".format(year, page.page_number))

    data_bbox = get_data_bbox(page)
    cropped = page.within_bbox(data_bbox)
    gutters = get_gutters(cropped)

    v_lines = [ cropped.bbox[0] ] + gutters  + [ cropped.bbox[2] ]

    table = cropped.extract_table({
        "vertical_strategy": "explicit",
        "explicit_vertical_lines": v_lines,
        "horizontal_strategy": "text",
    })

    df = pd.DataFrame(table, columns=COLUMNS)
    df["base_salary"] = df["base_salary"].apply(parse_money)
    df["guaranteed_compensation"] = df["guaranteed_compensation"].apply(parse_money)

    return df

def parse_pdf(path, year):
    with pdfplumber.open(path) as pdf:
        df = pd.concat([ parse_page(page, year) for page in pdf.pages ])
    return df

def main():
    HERE = os.path.dirname(os.path.abspath(__file__))
    for year in range(2007, 2018):
        print(year)
        pdf_path = os.path.join(HERE, "../pdfs/mls-salaries-{0}.pdf".format(year))
        csv_path = os.path.join(HERE, "../csvs/mls-salaries-{0}.csv".format(year))
        df = parse_pdf(pdf_path, year)
        df.to_csv(csv_path, index=False)

if __name__ == "__main__":
    main()
