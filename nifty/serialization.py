from typing import Dict, Any, Optional
import pandas as pd
import json


def serialise_price_data(
    data_frame: pd.DataFrame, symbol: str, year: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Filter a dataframe on a symbol and optionally a year then serialize in json format
    Resulting json is sorted by date (descending)
    """

    data_frame_filtered = data_frame[data_frame["Symbol"] == symbol].drop(
        columns=["Symbol"]
    )

    if data_frame_filtered.empty:
        return None

    data_frame_filtered.columns = [col.lower() for col in data_frame_filtered.columns]
    data_frame_filtered["date"] = pd.to_datetime(data_frame_filtered["date"])
    if year:
        data_frame_filtered = data_frame_filtered[
            data_frame_filtered["date"].dt.year == int(year)
        ]
    data_frame_filtered = data_frame_filtered.sort_values(by="date", ascending=False)
    data_frame_filtered["date"] = data_frame_filtered["date"].dt.strftime("%Y-%m-%d")
    return json.loads(data_frame_filtered.to_json(orient="records"))
