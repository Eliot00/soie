import pytest

from soie.requests import QueryParams


def test_query_params():
    query = QueryParams(b"name=John&age=31")
    assert query["name"] == "John"
    assert query["age"] == "31"

    with pytest.raises(KeyError):
        query["error"]


def test_path_params_convertor():
    pass
