from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import uvicorn


async def price_data(request: Request) -> JSONResponse:
    """
    Return price data for the requested symbol
    """
    symbol = request.path_params['symbol']

    # TODO:
    # 1) Return open, close, high, low prices for the requested symbol as json records
    # 2) Allow calling app to filter the data by specifying optionl 'to' and 'from' dates
    #    as query parameters
    # 3) Allow callers to sort the returned data by any of the four prices returned using a 'sort' query parameter

    # Symbol data is stored in the file data/nifty50_all.csv

    return JSONResponse({'implement': 'me'})

# URL routes
app = Starlette(debug=True, routes=[
    Route('/nifty/stocks/{symbol}', price_data)
])


def main() -> None:
    """
    start the server
    """
    uvicorn.run(app, host='0.0.0.0', port=8888)


# Entry point
main()
