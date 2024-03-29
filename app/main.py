from fastapi import FastAPI, Request, UploadFile, Depends, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from collections import Counter
import db
import csv
from log import Logger
from utils import open_csvfile, prepare_data, TF_Function, IDF_Function, create_path_to_csvfile
from config import settings


log = Logger(__name__, 'log.log').logger

app = FastAPI()

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
    total_number_words, word_list = await prepare_data(file)
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


async def create_csv_file(
    total_number_words: int, word_list: list | None, filename: str, session: AsyncSession
):
    dict_with_count_words = dict(Counter(word_list))

    for word, count in dict_with_count_words.items():
        dict_with_count_words[word] = await TF_Function(count, total_number_words)

    filepath = await create_path_to_csvfile(filename)

    async with open_csvfile(filepath, 'w', newline='') as csvfile:
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


async def TF_IDF_func(
    filepath: str, session: AsyncSession
):
    async with open_csvfile(filepath, newline='') as csvfile:
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