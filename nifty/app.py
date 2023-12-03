from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn

from nifty.wsgi.blueprints.stocks import price_data, create_price

# URL routes
app = Starlette(
    debug=True,
    routes=[
        Route(path="/nifty/stocks/{symbol}", endpoint=price_data, methods=["GET"]),
        Route(path="/nifty/stocks/", endpoint=create_price, methods=["POST"]),
    ],
)


def main() -> None:
    """
    start the server
    """
    uvicorn.run(app, host="0.0.0.0", port=8888)
