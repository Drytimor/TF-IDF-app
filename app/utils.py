from contextlib import asynccontextmanager, contextmanager, ExitStack
from collections import Counter
from typing import AsyncIterator, Iterator, TextIO
from config import settings
import string
import re
import os
from datetime import datetime
from math import log10


async def _prepare_data(file) -> tuple[int, list]:
    _bytes = await file.read()
    await file.close()
    text = _bytes.decode('utf-8')
    word_list = []
    regex = re.compile("[" + re.escape(string.punctuation) + "\\d" + "\\s" + "—" + "«" + "»" + "]")
    for word in text.lower().split():
        word = re.sub(regex, '', word)
        if word:
            word_list.append(word)
    return len(word_list), word_list


async def _TF_Function(word_frequency: int, total_number_words: int) -> float:
    return round(word_frequency / total_number_words, 4)


async def _IDF_Function(total_number_documents, number_documents_with_word) -> float:
    number_documents_with_word = number_documents_with_word if number_documents_with_word else 1
    return round(log10(total_number_documents / number_documents_with_word), 4)


def create_path_to_csvfile(filename: str) -> str:
    file_csv = re.sub(r'\.txt', '.csv', filename)
    filepath = os.path.join(settings.DIR_PATH_DOWNLOAD, file_csv)
    return filepath


async def create_dict_with_count_words(words: list, total_number_words: int) -> dict:

    dict_words = dict(Counter(words))

    for word, count in dict_words.items():
        dict_words[word] = await _TF_Function(count, total_number_words)

    return dict_words



@contextmanager
def open_csvfile(
        filename: str, mode: str = 'r', **kwargs
):
    filename = create_path_to_csvfile(filename)

    file = open(filename, mode, **kwargs)

    try:
        yield file
    finally:
        file.close()


@contextmanager
def open_csvfiles(files: list):
    l = []
    with ExitStack() as stack:
        for f in files:
            l.append(stack.enter_context(open(f.file_path, 'r', newline='')))
        try:
            yield l
        finally:
            stack.pop_all().close()
