#!/usr/bin/env python
import pdfplumber
import pandas as pd
import re
import sys, os

COLUMNS = [
    "club", "last_name", "first_name",
    "position", "base_salary", "guaranteed_compensation"
]

V_SEPARATORS = {
    "narrow": [ 0, 90, 185, 280, 330, 425, 540 ],
    "wide": [ 0, 110, 203, 300, 340, 425, 540 ]
}

NON_MONEY_CHAR_PAT = re.compile(r"[^\d\.]")

def parse_money(money_str):
    stripped = re.sub(NON_MONEY_CHAR_PAT, "", money_str)
    if len(stripped):
        return float(stripped)
    else:
        return None

def parse_page(page, year):
    t = dict(x_tolerance=5, y_tolerance=5)
    v = V_SEPARATORS["narrow" if year == 2007 else "wide"]
    table = page.extract_table(v=v, h="gutters", **t)
    df = pd.DataFrame(table)
    header_i = df[df[0] == "Club"].index[0]
    footer_i = df[df.fillna("").apply(lambda x: "Source" in "".join(x), axis=1)].index[0]
    main = df.loc[header_i + 1:footer_i-1].copy()
    main.columns = COLUMNS
    main["base_salary"] = main["base_salary"].apply(parse_money)
    main["guaranteed_compensation"] = main["guaranteed_compensation"].apply(parse_money)
    return main

def parse_pdf(path, year):
    with pdfplumber.open(path) as pdf:
        df = pd.concat([ parse_page(page, year) for page in pdf.pages ])
    return df

def main():
    HERE = os.path.dirname(os.path.abspath(__file__))
    for year in range(2007, 2017):
        print(year)
        pdf_path = os.path.join(HERE, "../pdfs/mls-salaries-{0}.pdf".format(year))
        csv_path = os.path.join(HERE, "../csvs/mls-salaries-{0}.csv".format(year))
        df = parse_pdf(pdf_path, year)
        df.to_csv(csv_path, index=False)

if __name__ == "__main__":
    main()
