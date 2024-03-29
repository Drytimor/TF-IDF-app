from contextlib import asynccontextmanager
from typing import AsyncIterator
import config
import string
import re
import os
from datetime import datetime
from math import log10


settings = config.settings


async def prepare_data(file) -> tuple[int, list]:
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


async def TF_Function(word_frequency: int, total_number_words: int) -> float:
    return round(word_frequency / total_number_words, 4)


async def IDF_Function(total_number_documents, number_documents_with_word) -> float:
    number_documents_with_word = number_documents_with_word if number_documents_with_word else 1
    return round(log10(total_number_documents / number_documents_with_word), 4)


async def create_path_to_csvfile(filename: str) -> str:
    file_csv = re.sub(r'\.txt', '.csv', filename)
    filepath = os.path.join(settings.DIR_PATH_DOWNLOAD, datetime.now().strftime('%Y%m%d%H%S') + file_csv)
    return filepath


@asynccontextmanager
async def open_csvfile(
        filename: str, mode: str = 'r', **kwargs
) -> AsyncIterator[None]:

    file = open(filename, mode, **kwargs)

    try:
        yield file

    finally:
        file.close()
