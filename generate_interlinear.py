#!/usr/bin/env python3
"""
Generate kjv_interlinear.json mapping each verse and word index
to its original-language Strong's number, lemma, and morphology.

Reads OSIS XML files under data/morphhb/wlc and outputs a JSON file
in the project root.
"""
import json
import os
import xml.etree.ElementTree as ET

# Map OSIS book codes to English book names matching verses-1769.json keys
OSIS_TO_BOOK = {
    'Gen': 'Genesis', 'Exod': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers', 'Deut': 'Deuteronomy',
    'Josh': 'Joshua', 'Judg': 'Judges', 'Ruth': 'Ruth', '1Sam': '1 Samuel', '2Sam': '2 Samuel',
    '1Kgs': '1 Kings', '2Kgs': '2 Kings', '1Chr': '1 Chronicles', '2Chr': '2 Chronicles',
    'Ezra': 'Ezra', 'Neh': 'Nehemiah', 'Esth': 'Esther', 'Job': 'Job',
    'Ps': 'Psalms', 'Prov': 'Proverbs', 'Eccl': 'Ecclesiastes', 'Song': 'Song of Solomon',
    'Isa': 'Isaiah', 'Jer': 'Jeremiah', 'Lam': 'Lamentations', 'Ezek': 'Ezekiel', 'Dan': 'Daniel',
    'Hos': 'Hosea', 'Joel': 'Joel', 'Amos': 'Amos', 'Obad': 'Obadiah', 'Jonah': 'Jonah',
    'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk', 'Zeph': 'Zephaniah', 'Hag': 'Haggai',
    'Zech': 'Zechariah', 'Mal': 'Malachi'
}

NS = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}

def main():
    interlinear = {}
    wlc_dir = os.path.join('data', 'morphhb', 'wlc')
    for fname in os.listdir(wlc_dir):
        if not fname.endswith('.xml'):
            continue
        path = os.path.join(wlc_dir, fname)
        tree = ET.parse(path)
        root = tree.getroot()
        # find all verse elements
        for verse in root.findall('.//osis:verse', NS):
            osis_id = verse.attrib.get('osisID')
            if not osis_id:
                continue
            parts = osis_id.split('.')
            if len(parts) != 3:
                continue
            book_code, chap, verse_no = parts
            book = OSIS_TO_BOOK.get(book_code)
            if not book:
                continue
            key = f"{book} {chap}:{verse_no}"
            for w in verse.findall('osis:w', NS):
                n_attr = w.attrib.get('n')
                if not n_attr:
                    continue
                idx = n_attr.split('.')[-1]
                entry = {
                    'strongs': w.attrib.get('lemma', ''),
                    'lemma': w.attrib.get('lemma', ''),
                    'morph': w.attrib.get('morph', ''),
                    'def': ''
                }
                interlinear.setdefault(key, {})[idx] = entry
    out_path = 'kjv_interlinear.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(interlinear, f, ensure_ascii=False, indent=2)
    print(f"Generated interlinear mapping: {out_path} ({len(interlinear)} verses)")

if __name__ == '__main__':
    main()
