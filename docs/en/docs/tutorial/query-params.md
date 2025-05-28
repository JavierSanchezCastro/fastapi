# Query Parameters

When you declare other function parameters that are not part of the path parameters, they are automatically interpreted as "query" parameters.

{* ../../docs_src/query_params/tutorial001.py hl[9] *}

The query is the set of key-value pairs that go after the `?` in a URL, separated by `&` characters.

For example, in the URL:

```
http://127.0.0.1:8000/items/?skip=0&limit=10
```

...the query parameters are:

* `skip`: with a value of `0`
* `limit`: with a value of `10`

As they are part of the URL, they are "naturally" strings.

But when you declare them with Python types (in the example above, as `int`), they are converted to that type and validated against it.

All the same process that applied for path parameters also applies for query parameters:

* Editor support (obviously)
* Data <abbr title="converting the string that comes from an HTTP request into Python data">"parsing"</abbr>
* Data validation
* Automatic documentation

## Defaults

As query parameters are not a fixed part of a path, they can be optional and can have default values.

In the example above they have default values of `skip=0` and `limit=10`.

So, going to the URL:

```
http://127.0.0.1:8000/items/
```

would be the same as going to:

```
http://127.0.0.1:8000/items/?skip=0&limit=10
```

But if you go to, for example:

```
http://127.0.0.1:8000/items/?skip=20
```

The parameter values in your function will be:

* `skip=20`: because you set it in the URL
* `limit=10`: because that was the default value

## Optional parameters

The same way, you can declare optional query parameters, by setting their default to `None`:

{* ../../docs_src/query_params/tutorial002_py310.py hl[7] *}

In this case, the function parameter `q` will be optional, and will be `None` by default.

/// check

Also notice that **FastAPI** is smart enough to notice that the path parameter `item_id` is a path parameter and `q` is not, so, it's a query parameter.

///

## Query parameter type conversion

You can also declare `bool` types, and they will be converted:

{* ../../docs_src/query_params/tutorial003_py310.py hl[7] *}

In this case, if you go to:

```
http://127.0.0.1:8000/items/foo?short=1
```

or

```
http://127.0.0.1:8000/items/foo?short=True
```

or

```
http://127.0.0.1:8000/items/foo?short=true
```

or

```
http://127.0.0.1:8000/items/foo?short=on
```

or

```
http://127.0.0.1:8000/items/foo?short=yes
```

or any other case variation (uppercase, first letter in uppercase, etc), your function will see the parameter `short` with a `bool` value of `True`. Otherwise as `False`.


## Multiple path and query parameters

You can declare multiple path parameters and query parameters at the same time, **FastAPI** knows which is which.

And you don't have to declare them in any specific order.

They will be detected by name:

{* ../../docs_src/query_params/tutorial004_py310.py hl[6,8] *}

## Required query parameters

When you declare a default value for non-path parameters (for now, we have only seen query parameters), then it is not required.

If you don't want to add a specific value but just make it optional, set the default as `None`.

But when you want to make a query parameter required, you can just not declare any default value:

{* ../../docs_src/query_params/tutorial005.py hl[6:7] *}

Here the query parameter `needy` is a required query parameter of type `str`.

If you open in your browser a URL like:

```
http://127.0.0.1:8000/items/foo-item
```

...without adding the required parameter `needy`, you will see an error like:

```JSON
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "query",
        "needy"
      ],
      "msg": "Field required",
      "input": null,
      "url": "https://errors.pydantic.dev/2.1/v/missing"
    }
  ]
}
```

As `needy` is a required parameter, you would need to set it in the URL:

```
http://127.0.0.1:8000/items/foo-item?needy=sooooneedy
```

...this would work:

```JSON
{
    "item_id": "foo-item",
    "needy": "sooooneedy"
}
```

And of course, you can define some parameters as required, some as having a default value, and some entirely optional:

{* ../../docs_src/query_params/tutorial006_py310.py hl[8] *}

In this case, there are 3 query parameters:

* `needy`, a required `str`.
* `skip`, an `int` with a default value of `0`.
* `limit`, an optional `int`.

## Query Parameter URL Decoding

By default, query parameters are "URL decoded". For example, if you have a URL like `http://example.com/?query=hello%20world`, the space `%20` is decoded and the query parameter `query` will have the value `hello world`.

This is typically the desired behavior. However, there might be cases where you need to receive the query parameter value exactly as it appears in the URL, without URL decoding. For instance, if the query parameter itself is expected to contain a URL-encoded string that you want to process or pass on as is.

You can control this behavior with the `decode_url` parameter in `Query`.

`decode_url` is a boolean parameter:

*   It defaults to `True`: query parameters are URL-decoded.
*   If you set `decode_url=False`, **FastAPI** will not URL-decode the query parameter. You will receive the raw string.

Here's an example:

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/items/")
async def read_items(
    raw_query: str = Query(..., decode_url=False),
    decoded_query: str = Query(...)  # Default decode_url=True
):
    return {"raw_query": raw_query, "decoded_query": decoded_query}

```

Let's say you call this endpoint with the URL:

`/items/?raw_query=https%3A%2F%2Fexample.com%3Fq%3Dtest&decoded_query=https%3A%2F%2Fexample.com%3Fq%3Dtest`

*   The `raw_query` parameter in your function will be the string `"https%3A%2F%2Fexample.com%3Fq%3Dtest"`.
*   The `decoded_query` parameter will be the string `"https://example.com?q=test"`.

You can test this behaviour. The example below uses `httpx` (which is used by `TestClient`).

```python
import httpx

# Note: In a real FastAPI app, you'd use TestClient
# from fastapi.testclient import TestClient
# client = TestClient(app)

encoded_url_part = "https%3A%2F%2Fexample.com%3Fq%3Dtest%26v%3D1"
url = f"http://127.0.0.1:8000/items/?raw_query={encoded_url_part}&decoded_query={encoded_url_part}"

# This is how you might call it with httpx directly
# response = httpx.get(url)
# print(response.json())

# Expected output (if server is running with the app above):
# {
#     "raw_query": "https%3A%2F%2Fexample.com%3Fq%3Dtest%26v%3D1",
#     "decoded_query": "https://example.com?q=test&v=1"
# }
```

This feature allows you to handle specific query parameters that might contain pre-encoded data or require manual decoding later in your application logic, giving you more control over the raw input from the URL.

/// tip

You could also use `Enum`s the same way as with [Path Parameters](path-params.md#predefined-values){.internal-link target=_blank}.

///
