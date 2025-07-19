from datetime import datetime

def generate_batch_id(prefix: str = "batch") -> str:
    now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]  # Millisecond precision
    return f"{prefix}_{now}"