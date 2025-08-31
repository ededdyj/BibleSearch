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
    # Load versification map (WLC -> KJV) to align verses
    verse_map = {}
    vm_file = os.path.join('data', 'morphhb', 'wlc', 'VerseMap.xml')
    VM_NS = {'vm': 'http://www.APTBibleTools.com/namespace'}
    if os.path.isfile(vm_file):
        vm_tree = ET.parse(vm_file)
        vm_root = vm_tree.getroot()
        for bk in vm_root.findall('vm:book', VM_NS):
            for v_node in bk.findall('vm:verse', VM_NS):
                wlc_id = v_node.attrib.get('wlc')
                kjv_id = v_node.attrib.get('kjv')
                if wlc_id and kjv_id:
                    verse_map[wlc_id] = kjv_id

    interlinear = {}
    wlc_dir = os.path.join('data', 'morphhb', 'wlc')
    for fname in os.listdir(wlc_dir):
        if not fname.endswith('.xml') or fname == 'VerseMap.xml':
            continue
        path = os.path.join(wlc_dir, fname)
        tree = ET.parse(path)
        root = tree.getroot()
        # find all verse elements
        for verse in root.findall('.//osis:verse', NS):
            wlc_id = verse.attrib.get('osisID')
            if not wlc_id:
                continue
            # map WLC verse to KJV versification if needed
            osis_id = verse_map.get(wlc_id, wlc_id)
            parts = osis_id.split('.')
            if len(parts) != 3:
                continue
            book_code, chap, verse_no = parts
            book = OSIS_TO_BOOK.get(book_code)
            if not book:
                continue
            key = f"{book} {chap}:{verse_no}"
            # sequentially index Hebrew tokens to align with KJV words
            token_idx = 0
            for w in verse.findall('osis:w', NS):
                entry = {
                    'strongs': w.attrib.get('lemma', ''),
                    'lemma': w.attrib.get('lemma', ''),
                    'morph': w.attrib.get('morph', ''),
                    'def': ''
                }
                interlinear.setdefault(key, {})[str(token_idx)] = entry
                token_idx += 1
    # Augment entries with Strong's definitions if available
    defs_map = {}
    defs_path = 'strongs_definitions.json'
    if os.path.isfile(defs_path):
        defs_map = json.load(open(defs_path, encoding='utf-8'))
    else:
        try:
            import requests
            url = 'https://raw.githubusercontent.com/openscriptures/HebrewLexicon/master/HebrewLexicon.text.json'
            resp = requests.get(url)
            defs_map = resp.json() if resp.ok else {}
        except Exception:
            defs_map = {}
    # Populate definition field from defs_map keyed by Strong's number
    for tokens in interlinear.values():
        for entry in tokens.values():
            strong = entry.get('strongs', '')
            key = strong.split('/')[-1]
            entry['def'] = defs_map.get(key, '')

    out_path = 'kjv_interlinear.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(interlinear, f, ensure_ascii=False, indent=2)
    print(f"Generated interlinear mapping: {out_path} ({len(interlinear)} verses)")

if __name__ == '__main__':
    main()
