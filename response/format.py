
def response_format_success(data):
    return {"data":data, "message":data, "status":True}

def response_format_error(data):
    return {"data":data, "message":data, "status":False}