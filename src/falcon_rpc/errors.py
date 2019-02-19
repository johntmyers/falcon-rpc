"""Error strings """

# raised on unhandled exceptions, like a 500 for REST
FATAL = 'fatal_error'

# method format invalid
BAD_METHOD = 'invalid_method_format'

UNK_FAMILY = 'unknown_family'

UNK_METHOD = 'unknown_method'

# for JSON payloads, if there is no body
MISSING_BODY = 'missing_body'

# for JSON payloads, if it's not actually JSON
BAD_JSON = 'invalid_json'
