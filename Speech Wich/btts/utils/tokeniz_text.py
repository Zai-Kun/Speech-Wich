import re
import textwrap
import unicodedata

def parse_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def find_punctuation(text):
    punctuation_marks = set()

    for char in text:
        category = unicodedata.category(char)
        if category.startswith("P"):
            punctuation_marks.add(char)

    return punctuation_marks

def get_index_of_last_punctuation_mark(text):
    punctuation = find_punctuation(text)

    index_of_last_punctuation_mark = float("-inf")
    
    for punctuation_mark in punctuation:
        index = text.rfind(punctuation_mark)
        if index > index_of_last_punctuation_mark:
            index_of_last_punctuation_mark = index

    return index_of_last_punctuation_mark


def split_text_into_chunks(text, max_chunk_length=50):
    text = parse_text(text)
    chunks = []
    
    while len(text)>max_chunk_length:
        text = text.strip()
        loop_chunk = textwrap.wrap(text, width=max_chunk_length, break_long_words=False)[0]

        if unicodedata.category(loop_chunk.strip()[-1]).startswith("P") or (index_of_last_punctuation_mark := get_index_of_last_punctuation_mark(loop_chunk)) == -1:
            text = text[len(loop_chunk)::]
            chunks.append(loop_chunk)
        else:
            chunk = loop_chunk[:index_of_last_punctuation_mark+1]
            text = text[len(chunk)::]
            chunks.append(chunk)

    if text:
        chunks.append(text)

    return chunks
