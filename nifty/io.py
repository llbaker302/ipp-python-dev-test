from typing import Optional
import pandas as pd


def csv_to_df(filename: str) -> Optional[pd.DataFrame]:
    """
    Attempt to convert csv file to a dataframe, return None if error
    """
    try:
        df = pd.read_csv(filename, parse_dates=["Date"])
    except Exception:
        return None
    return df


def df_to_csv(filename: str, data_frame: pd.DataFrame) -> Optional[bool]:
    """
    Attempt to write dataframe to csv file, return None if error
    """
    try:
        data_frame.to_csv(filename, index=False)
    except Exception as e:
        return None
    return True
