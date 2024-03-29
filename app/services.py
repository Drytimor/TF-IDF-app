from utils import (
    open_csvfile, _prepare_data, _IDF_Function, create_path_to_csvfile, create_dict_with_count_words
)
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_file_from_db, FilesBase, SessionDep, create_file_to_db
import csv
from datetime import datetime

async def create_csv_file(file, session: AsyncSession):

    filename = datetime.now().strftime('%Y%m%d%H%S') + file.filename
    total_number_words, word_list = await _prepare_data(file)
    dict_with_count_words = await create_dict_with_count_words(word_list, total_number_words)

    async with open_csvfile(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=dict_with_count_words.keys(), quoting=csv.QUOTE_NONNUMERIC
        )
        writer.writeheader()
        writer.writerow(dict_with_count_words)

    await add_file_to_db(filename, file.filename, total_number_words, session)

    return filename


async def calculate_TF_IDF_measure(
    filename: str, session: AsyncSession
):
    async with open_csvfile(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        for row in reader:
            response_result_dict = {word: {'TF': tf} for word, tf in row.items()}
            break

    all_files_from_db = await get_file_from_db(session)

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
        data['IDF'] = await _IDF_Function(total_number_documents, number_documents_with_word)

    return sorted(response_result_dict.items(), key=lambda x: x[1]['IDF'], reverse=True)[:50], all_files_from_db


async def add_file_to_db(
    filename, orig_file_name, total_number_words, session: AsyncSession
):
    data = FilesBase(
        file_path=filename, file_name=orig_file_name, number_word=total_number_words
    )
    await create_file_to_db(session=session, files_data=data)