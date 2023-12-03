from starlette.responses import JSONResponse
from starlette.requests import Request
import os
from http import HTTPStatus
import datetime
import pandas as pd
from copy import deepcopy

from nifty.io import csv_to_df, df_to_csv
from nifty.serialization import serialise_price_data
from nifty.validation import validate_parameters, validate_json, validate_data

# This reference to the data file is ugly, but can't guarantee cwd so this wil have to do
# In reality this would be replaced with an ORM
SOURCE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "nifty50_all.csv")
CREATE_SCHEMA_FILE = os.path.join(
    os.path.dirname(__file__), "schema", "stocks", "CREATE.json"
)


async def price_data(request: Request) -> JSONResponse:
    """
    Return price data for the requested symbol and optional year query parameter
    Will return a blank
    """

    error_message = validate_parameters(request=request)
    if error_message:
        return JSONResponse(content=error_message, status_code=HTTPStatus.BAD_REQUEST)

    full_data_frame = csv_to_df(SOURCE_FILE)
    if full_data_frame is None:
        return JSONResponse(
            content={"error": f"Error reading from data file"},
            status_code=HTTPStatus.BAD_REQUEST,
        )

    response_json = serialise_price_data(
        data_frame=full_data_frame,
        symbol=request.path_params.get("symbol"),
        year=request.query_params.get("year"),
    )

    return JSONResponse(content=response_json, status_code=HTTPStatus.OK)


async def create_price(request: Request) -> JSONResponse:
    """
    Create a new price entry in the given SOURCE_FILE
    Validated against schema in CREATE_SCHEMA_FILE
    """

    # Attempt to access the request json
    try:
        request_json = await request.json()
    except:
        return JSONResponse(
            content={"error": f"Validation error: No json payload found"},
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Attempt to validate the json
    error_message = validate_json(
        request_json=request_json, schema_file=CREATE_SCHEMA_FILE
    )
    if error_message:
        return JSONResponse(content=error_message, status_code=HTTPStatus.BAD_REQUEST)

    # Attempt to read the flat data file
    full_data_frame = csv_to_df(SOURCE_FILE)
    if full_data_frame is None:
        return JSONResponse(
            content={"message": f"Error reading from data file"},
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Attempt to validate the request data
    data_error_message = validate_data(
        data_frame=full_data_frame, request_json=request_json
    )
    if data_error_message:
        return JSONResponse(
            content=data_error_message, status_code=HTTPStatus.BAD_REQUEST
        )

    # Passed all validation so format the request data into the same format as the file and attempt to write to csv
    output_json = deepcopy(request_json)
    output_json["date"] = datetime.datetime.strptime(
        request_json.get("date"), "%d/%m/%Y"
    ).date()
    new_row = pd.DataFrame(output_json, index=[0])
    new_row["date"] = pd.to_datetime(new_row["date"])
    for col in new_row.columns:
        new_row.rename(columns={col: col.capitalize()}, inplace=True)
    new_data_frame = pd.concat([full_data_frame, new_row], ignore_index=True).fillna(0)
    
    if df_to_csv(SOURCE_FILE, new_data_frame) is None:
        return JSONResponse(
            content={"message": f"Error writing to file"},
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Everything went well so return the request
    return JSONResponse(content=request_json, status_code=HTTPStatus.CREATED)