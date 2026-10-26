# Line 1:  Import json for serializing/deserializing JSON-RPC messages (the wire format).
import json

# Line 2:  Import uuid to generate unique request IDs (JSON-RPC requires each request have a unique ID).
import uuid

# Line 5:  Define standard JSON-RPC 2.0 error codes as named constants for readability.
PARSE_ERROR = -32700  # Line 6:  Server failed to parse the request as valid JSON.
INVALID_REQUEST = (
    -32600
)  # Line 7:  Request object is malformed (missing required fields).
METHOD_NOT_FOUND = -32601  # Line 8:  The requested method doesn't exist on the server.
INVALID_PARAMS = -32602  # Line 9:  Method exists but parameters are wrong type/shape.
INTERNAL_ERROR = -32603  # Line 10: Server encountered an unexpected internal error.


# Line 13:  Define a helper function to build a JSON-RPC 2.0 request dictionary.
def build_request(method, params=None):
    # Line 14:  Generate a unique ID for this request (JSON-RPC spec requires a unique id per request).
    req_id = str(uuid.uuid4())
    # Line 15:  Build the request dict following JSON-RPC 2.0 spec: jsonrpc, method, params, id.
    request = {
        "jsonrpc": "2.0",  # Line 16:  Protocol version identifier (must be exactly "2.0").
        "method": method,  # Line 17:  The name of the method to invoke on the server.
        "params": params
        or {},  # Line 18:  Parameters to pass to the method (empty dict if none).
        "id": req_id,  # Line 19:  Unique identifier so response can be matched to request.
    }
    # Line 20:  Return the complete request dictionary ready to be "sent" over the wire.
    return request


# Line 23:  Define a helper function to build a successful JSON-RPC 2.0 response.
def build_success_response(request_id, result):
    # Line 24:  Build the response dict with jsonrpc version, the result, and matching id.
    response = {
        "jsonrpc": "2.0",  # Line 25:  Protocol version (must match request).
        "result": result,  # Line 26:  The actual result data from the method execution.
        "id": request_id,  # Line 27:  Echo back the request ID so client can correlate.
    }
    # Line 28:  Return the success response dict.
    return response


# Line 31:  Define a helper function to build an error JSON-RPC 2.0 response.
def build_error_response(request_id, code, message):
    # Line 32:  Build the response dict with jsonrpc version, error object, and matching id.
    response = {
        "jsonrpc": "2.0",  # Line 33:  Protocol version (must match request).
        "error": {  # Line 34:  Error object containing code and human-readable message.
            "code": code,  # Line 35:  Numeric error code from the standard set above.
            "message": message,  # Line 36:  Human-readable explanation of what went wrong.
        },
        "id": request_id,  # Line 37:  Echo back the request ID (or null if unparseable).
    }
    # Line 38:  Return the error response dict.
    return response


# Line 41:  Define a function to parse and validate an incoming JSON-RPC request.
def parse_request(raw):
    # Line 42:  Try to decode the raw data as JSON (simulates reading from a network socket).
    try:
        # Line 43:  Attempt JSON deserialization; will raise if not valid JSON.
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        # Line 45:  If JSON parsing failed, return a parse error response with null id.
        return None, build_error_response(
            None, PARSE_ERROR, "Could not parse request as JSON."
        )

    # Line 48:  Validate that the required JSON-RPC fields are present.
    if not isinstance(data, dict):
        # Line 49:  Top-level must be an object (dict), not a list or string.
        return None, build_error_response(
            None, INVALID_REQUEST, "Request must be a JSON object."
        )
    # Line 51:  Check for the jsonrpc version field (must be exactly "2.0").
    if data.get("jsonrpc") != "2.0":
        # Line 52:  Missing or wrong version — this is not a valid JSON-RPC 2.0 request.
        return None, build_error_response(
            None, INVALID_REQUEST, "Missing or invalid 'jsonrpc' field (must be '2.0')."
        )
    # Line 54:  Check for the method field (must be a non-empty string).
    if not data.get("method") or not isinstance(data["method"], str):
        # Line 55:  Missing or invalid method name — can't dispatch without knowing what to call.
        return None, build_error_response(
            None, INVALID_REQUEST, "Missing or invalid 'method' field."
        )

    # Line 58:  All validations passed — return the parsed data and no error.
    return data, None


# Line 61:  Define a function to parse an incoming JSON-RPC response (used by client).
def parse_response(raw):
    # Line 62:  Try to decode the raw response as JSON.
    try:
        # Line 63:  Deserialize the response; raise if malformed.
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        # Line 65:  FIX: Return error object directly (same shape as valid JSON-RPC errors).
        #          Previously returned {"error": {...}} which broke the "code" in parsed check.
        return {"code": PARSE_ERROR, "message": "Response is not valid JSON."}

    # Line 68:  Check if the response contains an error field (JSON-RPC: either result OR error).
    if "error" in data:
        # Line 69:  Return the error object directly so caller can inspect code and message.
        return data["error"]
    # Line 71:  No error field means success — return the result payload.
    return data.get("result")
