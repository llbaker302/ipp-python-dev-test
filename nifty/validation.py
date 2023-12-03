import datetime
from typing import Dict, Optional, Any
import json
from starlette.requests import Request
from jsonschema import validate, ValidationError
import pandas as pd

ALLOWED_DATE_FORMAT = "%d/%m/%Y"
LOOKBACK_DAYS = 50
SUPPORTED_PRICE_TYPES = ("close", "open", "high", "low")


def validate_parameters(request: Request) -> Optional[Dict[str, str]]:
    """
    Ideally this would be a decorator but that doesn't appear to be supported in Starlette currently
    Validates there is a symbol in the request path_params and also that year in the request query_params is valid
    Returns a jsonlike error message if validation fails, otherwise None
    """
    if not request.path_params.get("symbol"):
        return {"error": "No symbol provided"}

    year = request.query_params.get("year")
    if year:
        try:
            year = int(year)
            _valid_date = datetime.date(year=year, month=1, day=1)
        except ValueError:
            return {"error": f"Provided year {year} is invalid"}


def validate_json(request_json: Any, schema_file) -> Optional[Dict[str, str]]:
    """
    Ideally this would be a decorator but that doesn't appear to be supported in Starlette currently
    Validates a request_json using provided schema
    Also completes additional validation on date to ensure DD/MM/YYYY format
    Returns a jsonlike error message if validation fails, otherwise None
    """

    try:
        with open(schema_file) as f:
            schema_file = json.load(f)
        validate(instance=request_json, schema=schema_file)
    except ValidationError as e:
        return {"error": f"Validation error: {str(e)}"}

    try:
        _valid_date = datetime.datetime.strptime(
            request_json.get("date"), ALLOWED_DATE_FORMAT
        )
    except ValueError:
        return {"error": f"Validation error: date must be in DD/MM/YYYY format"}


def validate_data(
    data_frame: pd.DataFrame, request_json: Any
) -> Optional[Dict[str, str]]:
    """
    Validates that the current data doesn't already exist and also verifies
    that any price data is within 1 standard deviation of a given lookback period
    otherwise rejects the data entry
    Returns a jsonlike error message if validation fails, otherwise None
    """

    symbol = request_json.get("symbol")
    date = datetime.datetime.strptime(request_json.get("date"), "%d/%m/%Y").date()

    # Check if the current symbol/date is already in the dataset
    filtered_data = data_frame[data_frame["Symbol"] == symbol]
    filtered_data.columns = [col.lower() for col in filtered_data.columns]
    filtered_data["date"] = pd.to_datetime(filtered_data["date"]).dt.date
    filtered_data_on_date = filtered_data[filtered_data["date"] == date]

    # If this filtered dataset is empty then we know it doesn't exist so carry on with validation
    # Otherwise if it exists return an error message
    if filtered_data_on_date.empty:
        # Sort the data and slice on the last number of days defined by LOOKBACK_DAYS
        filtered_data = filtered_data.sort_values(by="date", ascending=False)
        last_available_data = filtered_data[filtered_data["date"] < date].head(
            LOOKBACK_DAYS
        )

        # Iterate over supported price types and verify that the input value is within
        # 1 standard deviation of the mean over the lookback period, if not then return an error
        for price_type in SUPPORTED_PRICE_TYPES:
            if request_json.get(price_type):
                price_value = float(request_json.get(price_type))
                std = float(
                    last_available_data.head(50)
                    .groupby("symbol")[price_type]
                    .std()
                    .iloc[0]
                )
                mean = float(
                    last_available_data.head(50)
                    .groupby("symbol")[price_type]
                    .mean()
                    .iloc[0]
                )

                if price_value < (mean - std) or price_value > (mean + std):
                    return {
                        "message": f"Value {price_value} for {price_type} is greater than one standard deviation of the previous {LOOKBACK_DAYS} values"
                    }
    else:
        return {"error": f"Entry already exists for {symbol} and {date}"}
