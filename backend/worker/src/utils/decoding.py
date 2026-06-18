def decode_bytes(value) -> str:
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return str(value)

def decode_fields(raw_fields) -> dict:
    # Decodes byte values from a Redis stream message into readable string
    if not isinstance(raw_fields, dict):
        return {"raw_fallback_content": str(raw_fields)}
    
    return {(decode_bytes(k)): (decode_bytes(v)) for k, v in raw_fields.items()}
