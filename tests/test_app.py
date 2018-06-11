import os
from typing import Optional, Tuple

import pytest

from molten import (
    HTTP_200, HTTP_201, HTTP_204, App, Cookies, Header, QueryParam, QueryParams, Request,
    RequestData, Response, Route, testing
)


def path_to(*xs):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *xs)


def index(request: Request) -> Response:
    return Response(HTTP_200, content="Hello!")


def params(params: QueryParams) -> Response:
    return Response(HTTP_200, content=repr(params))


def named_headers(content_type: Header) -> Response:
    return Response(HTTP_200, content=f"{content_type}")


def named_optional_headers(content_type: Optional[Header]) -> Response:
    return Response(HTTP_200, content=f"{content_type}")


def named_params(x: QueryParam, y: QueryParam) -> Response:
    return Response(HTTP_200, content=f"x: {x}, y: {y}")


def named_optional_params(x: Optional[QueryParam]) -> Response:
    return Response(HTTP_200, content=f"{x}")


def failing(request: Request) -> Response:
    raise RuntimeError("something bad happened")


def parser(data: RequestData) -> Response:
    return Response(HTTP_200)


def no_content() -> Response:
    return Response(HTTP_204)


def returns_dict() -> dict:
    return {"x": 42}


def returns_tuple() -> Tuple[str, dict]:
    return HTTP_201, {"x": 42}


def reads_cookies(cookies: Cookies) -> Response:
    return cookies


def get_countries() -> Response:
    return Response(HTTP_200, stream=open(path_to("fixtures", "example.json"), mode="rb"), headers={
        "content-type": "application/json",
    })


app = App(routes=[
    Route("/", index),
    Route("/params", params),
    Route("/named-headers", named_headers),
    Route("/named-optional-headers", named_optional_headers),
    Route("/named-params", named_params),
    Route("/named-optional-params", named_optional_params),
    Route("/failing", failing),
    Route("/parser", parser, method="POST"),
    Route("/no-content", no_content),
    Route("/returns-dict", returns_dict),
    Route("/returns-tuple", returns_tuple),
    Route("/reads-cookies", reads_cookies),
    Route("/countries", get_countries),
])
client = testing.TestClient(app)


def test_apps_can_handle_requests():
    # Given that I have an app and a test client
    # When I make a request to an existing handler
    response = client.get("/")

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "Hello!"


def test_apps_can_handle_requests_with_dependency_injection():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses DI
    response = client.get("/params", params={"x": "42"})

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "QueryParams({'x': ['42']})"


def test_apps_can_handle_requests_with_named_headers():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named header
    response = client.get("/named-headers", headers={
        "content-type": "text/plain",
    })

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "text/plain"


def test_apps_can_handle_requests_with_missing_named_headers():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named header without that header
    response = client.get("/named-headers", headers={})

    # Then I should get back a 400 response
    assert response.status_code == 400
    assert response.data == '{"content-type": "missing"}'


def test_apps_can_handle_requests_with_missing_named_optional_headers():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses an optional named header without that header
    response = client.get("/named-optional-headers", headers={})

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "None"


def test_apps_can_handle_requests_with_named_query_params():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named query param
    response = client.get("/named-params", params={
        "x": "42",
        "y": "hello!",
    })

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "x: 42, y: hello!"


def test_apps_can_handle_requests_with_missing_named_query_params():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses a named query param without that param
    response = client.get("/named-params")

    # Then I should get back a 400 response
    assert response.status_code == 400


def test_apps_can_handle_requests_with_missing_named_optional_query_params():
    # Given that I have an app and a test client
    # When I make a request to an existing handler that uses an optional named query param without that param
    response = client.get("/named-optional-params")

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "None"

    # When I make a request to an existing handler that uses an optional named query param with that param
    response = client.get("/named-optional-params", params={"x": "42"})

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.data == "42"


def test_apps_can_parse_json_request_data():
    # Given that I have an app and a test client
    # When I make a request to a handler that parses
    response = client.post("/parser", json={
        "x": 42,
    })

    # Then I should get back a 200 response
    assert response.status_code == 200


def test_apps_can_parse_urlencoded_request_data():
    # Given that I have an app and a test client
    # When I make a request to a handler that parses
    response = client.post("/parser", data={
        "x": "42",
    })

    # Then I should get back a 200 response
    assert response.status_code == 200


def test_apps_fall_back_to_404_if_a_route_isnt_matched():
    # Given that I have an app and a test client
    # When I make a request to a route that doesn't exist
    response = client.get("/i-dont-exist")

    # Then I should get back a 404 response
    assert response.status_code == 404


def test_apps_fall_back_to_500_if_a_route_raises_an_exception():
    # Given that I have an app and a test client
    # When I make a request to a route that raises an exception
    response = client.get("/failing")

    # Then I should get back a 500 response
    assert response.status_code == 500


def test_apps_fall_back_to_415_if_request_media_type_is_not_supported():
    # Given that I have an app
    # When I make a request containing un-parseable data
    response = client.post("/parser", headers={
        "content-type": "text/html",
    })

    # Then I should get back a 415
    assert response.status_code == 415


def test_apps_can_return_responses_without_content():
    # Given that I have an app
    # When I make a request to a handler that returns no content
    response = client.get("/no-content")

    # Then I should get back a 204
    assert response.status_code == 204
    assert response.data == ""


def test_apps_can_handle_requests_that_are_not_acceptable():
    # Given that I have an app
    # When I make a request with an Accept header that isn't supported
    response = client.get("/returns-dict", headers={
        "accept": "text/html",
    })

    # Then I should get back a 406 response
    assert response.status_code == 406
    assert response.data == "Not Acceptable"


def test_apps_can_render_tuples():
    # Given that I have an app
    # When I make a request to a handler that returns a tuple with a custom response code
    response = client.get("/returns-tuple")

    # Then I should get back that status code
    assert response.status_code == 201
    assert response.json() == {"x": 42}


def test_apps_can_return_files():
    # Given that I have an app
    # When I make a request to a handler that returns a file response
    response = client.get("/countries")

    # Then I should get back a 200 response
    assert response.status_code == 200
    assert response.headers["content-length"] == "15813"


@pytest.mark.parametrize("header,expected_status,expected_json", [
    (None, 200, {}),
    ("", 200, {}),
    ("a=1", 200, {"a": "1"}),
    ("a=1; b=2; a=3", 200, {"a": "3", "b": "2"}),
    ("a=1;b=2;a=3;;", 200, {"a": "3", "b": "2"}),
])
def test_apps_can_parse_cookie_headers(header, expected_status, expected_json):
    response = client.get("/reads-cookies", headers={
        "cookie": header,
    })
    assert response.status_code == expected_status
    assert response.json() == expected_json
