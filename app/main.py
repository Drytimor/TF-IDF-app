from fastapi import FastAPI, Request, UploadFile, Depends, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import string
import re
from collections import Counter
import db
from datetime import datetime
from math import log10
import csv
import os
import logging


log = logging.getLogger(__name__)
log.setLevel(level=logging.INFO)
file_handler = logging.FileHandler(filename='log.log', encoding='utf-8', mode='w')
formatter = logging.Formatter('%(name)s-%(message)s')
file_handler.setFormatter(formatter)
log.addHandler(file_handler)


app = FastAPI()
DIR_PATH_DOWNLOAD = './text'



templates = Jinja2Templates(directory=".")


@app.get('/', response_class=HTMLResponse)
async def upload_file_form(request: Request):
    return templates.TemplateResponse(
        request=request, name='upload.html'
    )


@app.post('/add', response_class=HTMLResponse)
async def upload_file(
    request: Request, file: UploadFile, session: db.SessionDep,
):
    _bytes = await file.read()
    total_number_words, word_list = await prepare_data(_bytes)
    path_csvfile = await create_csv_file(
        total_number_words, word_list, file.filename, session
    )
    return RedirectResponse(
        request.url_for('get_table_results').include_query_params(filepath=path_csvfile),
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get('/table', response_class=HTMLResponse)
async def get_table_results(
        request: Request, filepath: Annotated[str, Query()], session: db.SessionDep
):
    result_TF_IDF_file, all_files_from_db = await TF_IDF_func(filepath, session)

    return templates.TemplateResponse(
        request=request, name='table.html',
        context={
            'result': result_TF_IDF_file,
            'length': len(result_TF_IDF_file),
            'all_files': all_files_from_db
        }
    )


async def prepare_data(_bytes: bytes):
    text = _bytes.decode('utf-8')
    word_list = []
    regex = re.compile("[" + re.escape(string.punctuation) + "\\d" + "\\s" + "—" + "«" + "»" + "]")
    for word in text.lower().split():
        word = re.sub(regex, '', word)
        if word:
            word_list.append(word)
    return len(word_list), word_list


async def create_csv_file(
    total_number_words: int, word_list: list | None, filename:str, session: AsyncSession
):
    if word_list:
        dict_with_count_words = dict(Counter(word_list))

        for word, count in dict_with_count_words.items():
            dict_with_count_words[word] = await TF_Function(count, total_number_words)

        filepath= await create_path_to_csvfile(filename)

        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=dict_with_count_words.keys(), quoting=csv.QUOTE_NONNUMERIC
            )
            writer.writeheader()
            writer.writerow(dict_with_count_words)

            files_data = db.FilesBase(
                file_path=filepath, file_name=filename, number_word=total_number_words
            )
            await db.add_file_to_db(session=session, files_data=files_data)
            return filepath
    else:
        pass
        # TODO: - реализовать кеширование результата последнего отправленного файла
        # last_file_from_db = await db.get_last_file_from_db(session=session)
        # response_result_dict = await count_number_words_in_text(last_file_from_db)



async def TF_IDF_func(
        filepath: str, session: AsyncSession
):
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        for row in reader:
            response_result_dict = {word: {'TF': tf} for word, tf in row.items()}
            break

    all_files_from_db = await db.get_file_from_db(session)

    total_number_documents = 0

    for file in all_files_from_db:
        total_number_documents += 1
        with open(file.file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            for row in reader:
                row = row
                break

            for word in response_result_dict:
                response_result_dict[word].setdefault('num', 0)
                if row.get(word):
                    response_result_dict[word]['num'] += 1
                    continue

    for word, data in response_result_dict.items():
        number_documents_with_word = data.pop('num')
        data['IDF'] = await IDF_Function(total_number_documents, number_documents_with_word)

    return sorted(response_result_dict.items(), key=lambda x: x[1]['IDF'], reverse=True)[:50], all_files_from_db


async def create_path_to_csvfile(filename: str):
    file_csv = re.sub(r'\.txt', '.csv', filename)
    filepath = os.path.join(DIR_PATH_DOWNLOAD, datetime.now().strftime('%Y%m%d%H%S') + file_csv)
    return filepath


async def TF_Function(word_frequency: int, total_number_words: int) -> float:
    return round(word_frequency / total_number_words, 4)


async def IDF_Function(total_number_documents, number_documents_with_word) -> float:
    number_documents_with_word = number_documents_with_word if number_documents_with_word else 1
    return round(log10(total_number_documents / number_documents_with_word), 4)
