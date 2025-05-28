from typing import List, Optional, Union

from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
import pytest

app = FastAPI()

# Scenario 1: Test decode_url=False
@app.get("/decode_false/str")
async def get_decode_false_str(param: str = Query(..., decode_url=False)):
    return {"param": param}

@app.get("/decode_false/list")
async def get_decode_false_list(param_list: List[str] = Query(..., decode_url=False)):
    return {"param_list": param_list}

# Scenario 2: Test decode_url=True (Explicit)
@app.get("/decode_true/str")
async def get_decode_true_str(param: str = Query(..., decode_url=True)):
    return {"param": param}

@app.get("/decode_true/list")
async def get_decode_true_list(param_list: List[str] = Query(..., decode_url=True)):
    return {"param_list": param_list}

# Scenario 3: Test Default Behavior (Implicit decode_url=True)
@app.get("/decode_default/str")
async def get_decode_default_str(param: str = Query(...)):
    return {"param": param}

@app.get("/decode_default/list")
async def get_decode_default_list(param_list: List[str] = Query(...)):
    return {"param_list": param_list}

# Scenario 4: Mixed Parameters
@app.get("/mixed_params")
async def get_mixed_params(
    raw_param: str = Query(..., decode_url=False),
    decoded_param: str = Query(...),
    raw_list: List[str] = Query(default=[], decode_url=False),
    decoded_list: List[str] = Query(default=[]),
):
    return {
        "raw_param": raw_param,
        "decoded_param": decoded_param,
        "raw_list": raw_list,
        "decoded_list": decoded_list,
    }

# Scenario 5: Edge Cases for decode_url=False
@app.get("/edge_decode_false/empty_value")
async def get_edge_decode_false_empty_value(param: str = Query(decode_url=False)):
    return {"param": param}

@app.get("/edge_decode_false/no_value_char")
async def get_edge_decode_false_no_value_char(param: str = Query(decode_url=False)):
    # For query like /?param or /?param&other=val
    return {"param": param}
    
@app.get("/edge_decode_false/optional_missing")
async def get_edge_decode_false_optional_missing(
    param: Optional[str] = Query(None, decode_url=False)
):
    return {"param": param}

@app.get("/edge_decode_false/optional_present")
async def get_edge_decode_false_optional_present(
    param: Optional[str] = Query(None, decode_url=False)
):
    return {"param": param}

@app.get("/edge_decode_false/required_missing")
async def get_edge_decode_false_required_missing(
    param: str = Query(..., decode_url=False)
):
    return {"param": param} # Should not reach here

client = TestClient(app)

# --- Test Cases ---

# Scenario 1: Test decode_url=False
def test_decode_url_false_str():
    response = client.get("/decode_false/str?param=https%3A%2F%2Fexample.com%3Fq%3Dtest%26v%3D1")
    assert response.status_code == 200
    assert response.json() == {"param": "https%3A%2F%2Fexample.com%3Fq%3Dtest%26v%3D1"}

def test_decode_url_false_list():
    response = client.get("/decode_false/list?param_list=one%2Ftwo&param_list=three%20four%2Bplus")
    assert response.status_code == 200
    assert response.json() == {"param_list": ["one%2Ftwo", "three%20four%2Bplus"]}

# Scenario 2: Test decode_url=True (Explicit)
def test_decode_url_true_str():
    response = client.get("/decode_true/str?param=https%3A%2F%2Fexample.com%3Fq%3Dtest")
    assert response.status_code == 200
    assert response.json() == {"param": "https://example.com?q=test"}

def test_decode_url_true_list():
    response = client.get("/decode_true/list?param_list=one%2Ftwo&param_list=three%20four%2Bplus")
    assert response.status_code == 200
    assert response.json() == {"param_list": ["one/two", "three four+plus"]}

# Scenario 3: Test Default Behavior (Implicit decode_url=True)
def test_decode_default_str():
    response = client.get("/decode_default/str?param=https%3A%2F%2Fexample.com%3Fq%3Dtest")
    assert response.status_code == 200
    assert response.json() == {"param": "https://example.com?q=test"}

def test_decode_default_list():
    response = client.get("/decode_default/list?param_list=one%2Ftwo&param_list=three%20four%2Bplus")
    assert response.status_code == 200
    assert response.json() == {"param_list": ["one/two", "three four+plus"]}

# Scenario 4: Mixed Parameters
def test_mixed_params():
    url = (
        "/mixed_params?raw_param=a%2Fb%2Fc&decoded_param=x%2Fy%2Fz"
        "&raw_list=r1%2Fr1&raw_list=r2%20r2"
        "&decoded_list=d1%2Fd1&decoded_list=d2%20d2"
    )
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {
        "raw_param": "a%2Fb%2Fc",
        "decoded_param": "x/y/z",
        "raw_list": ["r1%2Fr1", "r2%20r2"],
        "decoded_list": ["d1/d1", "d2 d2"],
    }

def test_mixed_params_only_decoded_present():
    url = ("/mixed_params?decoded_param=x%2Fy%2Fz&decoded_list=d1%2Fd1")
    # raw_param is required, so this should fail if not provided
    response = client.get(url)
    assert response.status_code == 422 # Missing raw_param
    assert "raw_param" in response.json()["detail"][0]["loc"]
    
    # Test with raw_param present, but lists empty (using default)
    url = ("/mixed_params?raw_param=a%2Fb&decoded_param=x%2Fy")
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {
        "raw_param": "a%2Fb",
        "decoded_param": "x/y",
        "raw_list": [],
        "decoded_list": [],
    }


# Scenario 5: Edge Cases for decode_url=False
def test_edge_decode_false_empty_value():
    response = client.get("/edge_decode_false/empty_value?param=")
    assert response.status_code == 200
    assert response.json() == {"param": ""}

def test_edge_decode_false_no_value_char_just_key():
    response = client.get("/edge_decode_false/no_value_char?param")
    assert response.status_code == 200
    assert response.json() == {"param": ""} # Based on _get_raw_query_param_value logic

def test_edge_decode_false_no_value_char_with_other_param():
    response = client.get("/edge_decode_false/no_value_char?param&other=123")
    assert response.status_code == 200
    assert response.json() == {"param": ""}

def test_edge_decode_false_optional_missing():
    response = client.get("/edge_decode_false/optional_missing") # No param sent
    assert response.status_code == 200
    assert response.json() == {"param": None}

def test_edge_decode_false_optional_present_empty():
    response = client.get("/edge_decode_false/optional_present?param=")
    assert response.status_code == 200
    assert response.json() == {"param": ""}
    
def test_edge_decode_false_optional_present_value():
    response = client.get("/edge_decode_false/optional_present?param=a%2Fb")
    assert response.status_code == 200
    assert response.json() == {"param": "a%2Fb"}

def test_edge_decode_false_required_missing():
    response = client.get("/edge_decode_false/required_missing") # No param sent
    assert response.status_code == 422
    json_response = response.json()
    assert json_response["detail"][0]["type"] == "missing" # Pydantic v2
    assert json_response["detail"][0]["loc"] == ["query", "param"]

# Scenario 6: Pydantic model fields (Covered by mixed params with multiple scalar Query)
# As per instructions, specific test for Query(MyModel, decode_url=False) is skipped.
# The "Mixed Parameters" test (scenario 4) already demonstrates multiple scalar Query 
# parameters with different decode_url settings working together.

# Example of how Query parameters within a dependency model would be handled
# (Not directly testing decode_url inside the model fields, but how they are sourced)
class DepParams:
    def __init__(
        self,
        raw_q: str = Query("default_raw", decode_url=False),
        decoded_q: str = Query("default_decoded"),
    ):
        self.raw_q = raw_q
        self.decoded_q = decoded_q

@app.get("/depends_model_params")
async def get_depends_model_params(params: DepParams = Depends()):
    return {"raw_q": params.raw_q, "decoded_q": params.decoded_q}

def test_depends_model_params_default():
    response = client.get("/depends_model_params")
    assert response.status_code == 200
    assert response.json() == {"raw_q": "default_raw", "decoded_q": "default_decoded"}

def test_depends_model_params_provided():
    response = client.get("/depends_model_params?raw_q=a%2Fb&decoded_q=x%2Fy")
    assert response.status_code == 200
    assert response.json() == {"raw_q": "a%2Fb", "decoded_q": "x/y"}

def test_depends_model_params_only_raw_provided():
    response = client.get("/depends_model_params?raw_q=a%2Fb")
    assert response.status_code == 200
    assert response.json() == {"raw_q": "a%2Fb", "decoded_q": "default_decoded"}

def test_depends_model_params_only_decoded_provided():
    response = client.get("/depends_model_params?decoded_q=x%2Fy")
    assert response.status_code == 200
    assert response.json() == {"raw_q": "default_raw", "decoded_q": "x/y"}

# Test for plus sign encoding
@app.get("/plus_sign/decode_false")
async def get_plus_sign_decode_false(param: str = Query(..., decode_url=False)):
    return {"param": param}

@app.get("/plus_sign/decode_true")
async def get_plus_sign_decode_true(param: str = Query(..., decode_url=True)):
    return {"param": param}

def test_plus_sign_decode_false():
    # Browsers (and TestClient) typically convert space to '+' in query strings.
    # '+' itself should be percent-encoded as %2B if it's meant to be a literal plus.
    # If we send 'foo+bar', with decode_url=False, we expect 'foo+bar'
    response = client.get("/plus_sign/decode_false?param=foo+bar")
    assert response.status_code == 200
    assert response.json() == {"param": "foo+bar"}

    # If we send 'foo%2Bbar', with decode_url=False, we expect 'foo%2Bbar'
    response = client.get("/plus_sign/decode_false?param=foo%2Bbar")
    assert response.status_code == 200
    assert response.json() == {"param": "foo%2Bbar"}
    
    # Test with actual space %20
    response = client.get("/plus_sign/decode_false?param=foo%20bar")
    assert response.status_code == 200
    assert response.json() == {"param": "foo%20bar"}


def test_plus_sign_decode_true():
    # If we send 'foo+bar', with decode_url=True, '+' is interpreted as space
    response = client.get("/plus_sign/decode_true?param=foo+bar")
    assert response.status_code == 200
    assert response.json() == {"param": "foo bar"}

    # If we send 'foo%2Bbar', with decode_url=True, it's decoded to 'foo+bar'
    response = client.get("/plus_sign/decode_true?param=foo%2Bbar")
    assert response.status_code == 200
    assert response.json() == {"param": "foo+bar"}

    # Test with actual space %20
    response = client.get("/plus_sign/decode_true?param=foo%20bar")
    assert response.status_code == 200
    assert response.json() == {"param": "foo bar"}

# Test alias with decode_url=False
@app.get("/alias/decode_false")
async def get_alias_decode_false(
    param: str = Query(..., alias="param-alias", decode_url=False)
):
    return {"param-alias": param}

def test_alias_with_decode_false():
    response = client.get("/alias/decode_false?param-alias=a%2Fb%2Fc")
    assert response.status_code == 200
    assert response.json() == {"param-alias": "a%2Fb%2Fc"}

    # Test missing alias
    response = client.get("/alias/decode_false?param=a%2Fb%2Fc")
    assert response.status_code == 422 # param-alias is missing

# Test alias with decode_url=True
@app.get("/alias/decode_true")
async def get_alias_decode_true(
    param: str = Query(..., alias="param-alias", decode_url=True)
):
    return {"param-alias": param}

def test_alias_with_decode_true():
    response = client.get("/alias/decode_true?param-alias=a%2Fb%2Fc")
    assert response.status_code == 200
    assert response.json() == {"param-alias": "a/b/c"}

# Test alias with default (implicit decode_url=True)
@app.get("/alias/decode_default")
async def get_alias_decode_default(
    param: str = Query(..., alias="param-alias")
):
    return {"param-alias": param}

def test_alias_with_decode_default():
    response = client.get("/alias/decode_default?param-alias=a%2Fb%2Fc")
    assert response.status_code == 200
    assert response.json() == {"param-alias": "a/b/c"}

# Test for empty list with decode_url=False
@app.get("/empty_list/decode_false")
async def get_empty_list_decode_false(
    param_list: List[str] = Query(default=[], decode_url=False)
):
    return {"param_list": param_list}

def test_empty_list_decode_false_no_param():
    response = client.get("/empty_list/decode_false")
    assert response.status_code == 200
    assert response.json() == {"param_list": []}

def test_empty_list_decode_false_with_empty_param():
    # ?param_list=
    # This is interpreted by Starlette as one item "" if param_list is defined.
    # If decode_url=False, raw value is "".
    # If List[str], then _validate_value_with_model_field gets field.validate([""], ...)
    # This should become [""]
    response = client.get("/empty_list/decode_false?param_list=")
    assert response.status_code == 200
    assert response.json() == {"param_list": [""]}

# Test for empty list with decode_url=True
@app.get("/empty_list/decode_true")
async def get_empty_list_decode_true(
    param_list: List[str] = Query(default=[], decode_url=True)
):
    return {"param_list": param_list}

def test_empty_list_decode_true_no_param():
    response = client.get("/empty_list/decode_true")
    assert response.status_code == 200
    assert response.json() == {"param_list": []}
    
def test_empty_list_decode_true_with_empty_param():
    response = client.get("/empty_list/decode_true?param_list=")
    assert response.status_code == 200
    assert response.json() == {"param_list": [""]}

# Test for default_factory
from uuid import UUID, uuid4
@app.get("/default_factory/decode_false")
async def get_default_factory_decode_false(
    param: UUID = Query(default_factory=uuid4, decode_url=False)
):
    # decode_url=False is not very meaningful for UUID which doesn't typically have URL encoded chars
    # but testing the combination
    return {"param": str(param)}

def test_default_factory_decode_false_missing():
    response = client.get("/default_factory/decode_false")
    assert response.status_code == 200
    # Check that param is a valid UUID string, actual value is non-deterministic
    assert UUID(response.json()["param"])

def test_default_factory_decode_false_provided():
    # UUIDs don't typically contain characters that are URL-encoded.
    # Sending a simple string that happens to be a valid UUID representation.
    # Since decode_url=False, it will be taken as is.
    # Pydantic will then try to validate this raw string as a UUID.
    test_uuid_str = "12345678-1234-5678-1234-567812345678"
    response = client.get(f"/default_factory/decode_false?param={test_uuid_str}")
    assert response.status_code == 200
    assert response.json() == {"param": test_uuid_str}

    # Test with a value that might look like it needs decoding, but shouldn't be
    # (though this isn't a valid UUID)
    # This will cause a 422 from Pydantic validation for the UUID type
    response = client.get("/default_factory/decode_false?param=not%2Duuid")
    assert response.status_code == 422


@app.get("/default_factory/decode_true")
async def get_default_factory_decode_true(
    param: UUID = Query(default_factory=uuid4, decode_url=True)
):
    return {"param": str(param)}

def test_default_factory_decode_true_missing():
    response = client.get("/default_factory/decode_true")
    assert response.status_code == 200
    assert UUID(response.json()["param"])

def test_default_factory_decode_true_provided():
    test_uuid_str = "12345678-1234-5678-1234-567812345678"
    response = client.get(f"/default_factory/decode_true?param={test_uuid_str}") # No encoding needed
    assert response.status_code == 200
    assert response.json() == {"param": test_uuid_str}

    # Example with URL encoding, though not typical for UUIDs
    # Say we send param=some%20value - this is not a UUID
    # Pydantic validation for UUID type will fail it.
    response = client.get("/default_factory/decode_true?param=not%2Duuid")
    assert response.status_code == 422 # Pydantic validation error for UUID type

# Required parameter with decode_url=False and alias
@app.get("/required_alias_decode_false")
async def get_required_alias_decode_false(
    param: str = Query(alias="real-param-name", decode_url=False) # Implicitly required
):
    return {"param": param}

def test_required_alias_decode_false_present():
    response = client.get("/required_alias_decode_false?real-param-name=hello%2Fworld")
    assert response.status_code == 200
    assert response.json() == {"param": "hello%2Fworld"}

def test_required_alias_decode_false_missing_original_name():
    response = client.get("/required_alias_decode_false?param=hello%2Fworld")
    assert response.status_code == 422 # real-param-name is missing

def test_required_alias_decode_false_missing_aliased_name():
    response = client.get("/required_alias_decode_false")
    assert response.status_code == 422

# Test with include_in_schema=False
@app.get("/include_in_schema_false/decode_false")
async def get_include_in_schema_false_decode_false(
    param: str = Query("default", decode_url=False, include_in_schema=False)
):
    return {"param": param}

def test_include_in_schema_false_decode_false():
    response = client.get("/include_in_schema_false/decode_false?param=val%2F1")
    assert response.status_code == 200
    assert response.json() == {"param": "val%2F1"}

    response = client.get("/include_in_schema_false/decode_false")
    assert response.status_code == 200
    assert response.json() == {"param": "default"} # Default value is used


@app.get("/include_in_schema_false/decode_true")
async def get_include_in_schema_false_decode_true(
    param: str = Query("default", decode_url=True, include_in_schema=False)
):
    return {"param": param}

def test_include_in_schema_false_decode_true():
    response = client.get("/include_in_schema_false/decode_true?param=val%2F1")
    assert response.status_code == 200
    assert response.json() == {"param": "val/1"}

    response = client.get("/include_in_schema_false/decode_true")
    assert response.status_code == 200
    assert response.json() == {"param": "default"}

# Test deprecated flag (should not affect decoding)
@app.get("/deprecated/decode_false")
async def get_deprecated_decode_false(
    param: str = Query(..., decode_url=False, deprecated=True)
):
    return {"param": param}

def test_deprecated_decode_false():
    response = client.get("/deprecated/decode_false?param=test%2deprecated")
    assert response.status_code == 200
    assert response.json() == {"param": "test%2deprecated"}

@app.get("/deprecated/decode_true")
async def get_deprecated_decode_true(
    param: str = Query(..., decode_url=True, deprecated=True)
):
    return {"param": param}

def test_deprecated_decode_true():
    response = client.get("/deprecated/decode_true?param=test%2deprecated")
    assert response.status_code == 200
    assert response.json() == {"param": "test/deprecated"}

# Test with very long string
@app.get("/long_string/decode_false")
async def get_long_string_decode_false(param: str = Query(..., decode_url=False)):
    return {"param": param}

def test_long_string_decode_false():
    long_raw_val = "a%2Fb%2Fc" * 1000
    response = client.get(f"/long_string/decode_false?param={long_raw_val}")
    assert response.status_code == 200
    assert response.json() == {"param": long_raw_val}


@app.get("/long_string/decode_true")
async def get_long_string_decode_true(param: str = Query(..., decode_url=True)):
    return {"param": param}

def test_long_string_decode_true():
    long_encoded_val = "a%2Fb%2Fc" * 1000
    long_decoded_val = "a/b/c" * 1000
    response = client.get(f"/long_string/decode_true?param={long_encoded_val}")
    assert response.status_code == 200
    assert response.json() == {"param": long_decoded_val}

# Test with special characters that are not typically percent-encoded in query strings
# but might be if explicitly done. E.g. '*', '(', ')', '!'
# RFC 3986 reserves: ! * ' ( ) ; : @ & = + $ , / ? # [ ]
# Percent encoding these would be: %21 %2A %27 %28 %29 %3B %3A %40 %26 %3D %2B %24 %2C %2F %3F %23 %5B %5D
@app.get("/special_chars/decode_false")
async def get_special_chars_decode_false(param: str = Query(..., decode_url=False)):
    return {"param": param}

def test_special_chars_decode_false():
    # Test with chars that are "unreserved" but sometimes encoded
    # If sent raw (e.g. param=(value)), should be received as (value)
    # If sent encoded (e.g. param=%28value%29), should be received as %28value%29
    raw_val = "param=(value)*!'"
    encoded_val = "param=%28value%29%2A%21%27" # ( ) * ! '
    
    response = client.get(f"/special_chars/decode_false?param={raw_val}")
    assert response.status_code == 200
    assert response.json() == {"param": raw_val}
    
    response = client.get(f"/special_chars/decode_false?param={encoded_val}")
    assert response.status_code == 200
    assert response.json() == {"param": encoded_val}


@app.get("/special_chars/decode_true")
async def get_special_chars_decode_true(param: str = Query(..., decode_url=True)):
    return {"param": param}

def test_special_chars_decode_true():
    raw_val = "param=(value)*!'" # These are valid in query string, TestClient won't encode them
    encoded_val = "param=%28value%29%2A%21%27"
    decoded_val_from_encoded = "(value)*!'"
    
    response = client.get(f"/special_chars/decode_true?param={raw_val}")
    assert response.status_code == 200
    # Starlette's QueryParams typically doesn't decode these if they are valid path characters
    # and not percent-encoded. So raw_val should pass as is.
    assert response.json() == {"param": raw_val} 
                                    
    response = client.get(f"/special_chars/decode_true?param={encoded_val}")
    assert response.status_code == 200
    assert response.json() == {"param": decoded_val_from_encoded}

# Test with default value for list
@app.get("/list_default/decode_false")
async def list_default_decode_false(
    param_list: List[str] = Query(default=["default%2Fval"], decode_url=False)
):
    return {"param_list": param_list}

def test_list_default_decode_false_missing():
    response = client.get("/list_default/decode_false")
    assert response.status_code == 200
    assert response.json() == {"param_list": ["default%2Fval"]}

def test_list_default_decode_false_provided():
    response = client.get("/list_default/decode_false?param_list=new%2Fval&param_list=another%2Fone")
    assert response.status_code == 200
    assert response.json() == {"param_list": ["new%2Fval", "another%2Fone"]}


@app.get("/list_default/decode_true")
async def list_default_decode_true(
    param_list: List[str] = Query(default=["default/val"], decode_url=True)
):
    return {"param_list": param_list}

def test_list_default_decode_true_missing():
    response = client.get("/list_default/decode_true")
    assert response.status_code == 200
    # Default value for list Query is often tricky with Pydantic.
    # The default value itself is taken as is, not processed as a query string.
    assert response.json() == {"param_list": ["default/val"]}


def test_list_default_decode_true_provided():
    response = client.get("/list_default/decode_true?param_list=new%2Fval&param_list=another%2Fone")
    assert response.status_code == 200
    assert response.json() == {"param_list": ["new/val", "another/one"]}

# Test numeric types with decode_url=False (should not affect them unless their str form has encodable chars)
@app.get("/numeric/decode_false")
async def numeric_decode_false(
    p_int: int = Query(..., decode_url=False),
    p_float: float = Query(..., decode_url=False)
):
    return {"p_int": p_int, "p_float": p_float}

def test_numeric_decode_false():
    # Numeric values usually don't contain chars that need encoding.
    # decode_url=False means the string "123" or "1.23" is passed to Pydantic for conversion.
    response = client.get("/numeric/decode_false?p_int=123&p_float=1.23")
    assert response.status_code == 200
    assert response.json() == {"p_int": 123, "p_float": 1.23}

    # If we try to send encoded stuff, Pydantic validation for int/float will fail.
    response = client.get("/numeric/decode_false?p_int=1%323&p_float=1%2E23")
    assert response.status_code == 422 # Pydantic cannot parse "1%323" as int

@app.get("/numeric/decode_true")
async def numeric_decode_true(
    p_int: int = Query(..., decode_url=True),
    p_float: float = Query(..., decode_url=True)
):
    return {"p_int": p_int, "p_float": p_float}

def test_numeric_decode_true():
    response = client.get("/numeric/decode_true?p_int=123&p_float=1.23")
    assert response.status_code == 200
    assert response.json() == {"p_int": 123, "p_float": 1.23}

    # If we send something that *could* be decoded to a number, it would work.
    # E.g. if '12%33' was sent and decoded to '123'
    # But TestClient/requests might auto-decode query params before sending,
    # or FastAPI/Starlette might decode before Query.
    # Let's assume standard simple numbers.
    # If we send something that decodes to a non-number, Pydantic fails.
    response = client.get("/numeric/decode_true?p_int=1%323&p_float=1%2E23") # "123", "1.23" after decoding
    assert response.status_code == 200 
    assert response.json() == {"p_int": 123, "p_float": 1.23}

    response = client.get("/numeric/decode_true?p_int=notanint&p_float=notafloat")
    assert response.status_code == 422
