
def parse_numeric(value):
    if isinstance(value, str):
        return float(value.replace(",", "").replace("£", "").strip())
    elif isinstance(value, (int, float)):
        return float(value)
    return None
