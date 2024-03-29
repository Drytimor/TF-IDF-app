from fastapi import FastAPI, Request, UploadFile, Depends, Query, status, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from log import Logger
from services import create_csv_file, calculate_TF_IDF_measure, SessionDep


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
    request: Request, file: UploadFile, session: SessionDep,
):
    filename = await create_csv_file(file, session)
    return RedirectResponse(
        request.url_for('display_results_table').include_query_params(filename=filename),
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get('/table', response_class=HTMLResponse)
async def display_results_table(
        request: Request, filename: Annotated[str, Query()], session: SessionDep
):
    result_TF_IDF_file, all_files_from_db = await (
        calculate_TF_IDF_measure(filename, session)
    )
    return templates.TemplateResponse(
        request=request, name='table.html',
        context={
            'result': result_TF_IDF_file,
            'length': len(result_TF_IDF_file),
            'all_files': all_files_from_db
        }
    )

