from fastapi import FastAPI, Request, UploadFile, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import string
import re
from collections import Counter
import db
from datetime import datetime
from math import log10


app = FastAPI()
FILE_PATH = './text/{filename}'



templates = Jinja2Templates(directory=".")


@app.get('/', response_class=HTMLResponse)
async def upload_file_form(request: Request):
    return templates.TemplateResponse(
        request=request, name='upload.html'
    )


@app.post('/', response_class=HTMLResponse)
async def upload_file(
        request: Request, file: UploadFile, session: Session = Depends(db.get_session),
):
    _bytes = await file.read()
    filename = datetime.now().strftime('%Y%m%d%H%S') + file.filename
    total_number_words, word_list, prepare_string_words = await prepare_data(_bytes)
    file_data_from_request = dict(Counter(word_list))
    result = await TF_IDF_func(total_number_words, file_data_from_request, prepare_string_words, filename, session)
    return templates.TemplateResponse(
            request=request, name='table.html', context={'result': result, 'length': len(result)}
    )


async def prepare_data(_bytes):
    text = _bytes.decode('utf-8')
    word_list = []
    string_words = ''
    regex = re.compile("[" + re.escape(string.punctuation) + "\\d" + "\\s" + "—" + "«" + "»" + "]")
    for word in text.lower().split():
        word = re.sub(regex, '', word)
        if word:
            word_list.append(word)
            string_words += word + ' '
    return len(word_list), word_list, string_words


async def TF_IDF_func(total_number_words, file_data_from_request, prepare_string_words, filename, session):

    with open(FILE_PATH.format(filename=filename), 'w') as f:
        f.write(prepare_string_words)
        files_data = db.FilesBase(file_path=f.name, number_word=total_number_words)
        await db.add_file_to_db(session=session, files_data=files_data)

    all_files_from_db = await db.get_file_from_db(session)

    response_result_dict = {
        word: {'TF': TF_Function(count, total_number_words)} for word, count in file_data_from_request.items()
    }

    total_number_documents = 0

    for file in all_files_from_db:
        total_number_documents += 1
        with open(file.file_path, 'r') as f:
            text = f.read()
            for word in file_data_from_request:
                response_result_dict[word].setdefault('num', 0)
                if re.search(word, text):
                    response_result_dict[word]['num'] += 1

    for word, data in response_result_dict.items():
        number_documents_with_word = data.pop('num')
        data['IDF'] = await IDF_Function(total_number_documents, number_documents_with_word)

    return sorted(response_result_dict.items(), key=lambda x: x[1]['IDF'], reverse=True)[:50]


def TF_Function(word_frequency, total_number_words):
    return round(word_frequency / total_number_words, 4)


async def IDF_Function(total_number_documents, number_documents_with_word):
    return round(log10(total_number_documents / number_documents_with_word), 4)











