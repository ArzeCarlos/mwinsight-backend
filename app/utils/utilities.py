from datetime import datetime
time = datetime.now()

def generate_response_all(data, total_count):
    return {
        "metadata": {
            "total_count": total_count,
            "status": "success",
            "processedAt": time
        },
        "data": data
    }

def generate_response(data):
    return {
        "metadata": {
            "status": "success",
            "processedAt": time
        },
        "data": data
    }

def generate_response_delete_200(name):
    return {"metadata":{
            "status": "success",
            "processedAt": time,
            "message": f"{name} deleted successfully.",
        }
    }

def generate_response_update_200(data,name):
    return {
            "metadata": {
                "status": "success",
                "processedAt": time,
                "message": f"{name} updated successfully."
            },
            "data": data
    }

def generate_response_create_200(data,name):
    return {
            "metadata": {
                "status": "success",
                "processedAt": time,
                "message": f"{name} created successfully."
            },
            "data": data
    }

def generate_response_results_simulation_200(data,name):
    return {
            "metadata": {
                "status": "success",
                "processedAt": time,
                "message": f"{name} successfully."
            },
            "data": data
    }

def generate_response_delete_500(name):
    return {
        "metadata": {
            "status": "failed",
            "processedAt": time,
            "message": f"Error: Failed to delete {name} due to an internal server error."
        }
    }

def generate_failed_params():
    return {
        "metadata": {
        "status": "failed",
        "processedAt": time,
        "message": "No data has been sent in the body of the request."
        }
    }

def generate_failed_invalid_params():
    return {
        "metadata": {
                    "status": "failed",
                    "processedAt": time,
                    "message": "No valid fields have been sent in the body."
        }
    }

def generate_failed_invalid_post():
    return {
        "metadata": {
                    "status": "failed",
                    "processedAt": time,
                    "message": "Invalid url for post"
        }
    }

def generate_failed_url_not_found():
    return {
        "metadata": {
                    "status": "failed",
                    "processedAt": time,
                    "message": "URL not found"
        }
    }

def generate_failed_post_missparams(fields):
    return {
         "metadata": {
            "status": "failed",
            "processedAt": time,
            "message": f"Error: missing fields {', '.join(fields)}."
        }
    }

def generate_failed_msg_not_found_404(name):
    return {
        "metadata":{
            "status": "failed",
            "processedAt": time,
            "message": f"Error: {name} not found.",
        }
    }

def generate_failed_msg_not_found_200(name):
    return {
        "metadata":{
            "status": "success",
            "processedAt": time,
            "message": f"Error: {name} not found.",
            "data": [],
            "total_count": 0
        }
    }

def generate_failed_message_dberror():
    return {
        "metadata":{
            "status": "failed",
            "processedAt": time,
            "message": "Error: database error.",
        }
    }

def generate_failed_message_unknown(name,params):
    return {
        "metadata":{
            "status": "failed",
            "processedAt": time,
            "message": f"{name} unknown parameters.",
            "unknown": params
        }
    }

def generate_failed_invalid_fields(name="Default"):
    return {
        "metadata":{
            "status": "failed",
            "processedAt": time,
            "message": f"{name} invalid fields.",
        }
    }

def generate_failed_message_exception():
    return {
        "metadata":{
            "status": "failed",
            "processedAt": time,
            "message": "An unexpected error occurred while processing your request.",
        }
    }

def generate_failed_message_error_id():
    return {
        "metadata":{
            "status": "failed",
            "processedAt": time,
            "message": "Invalid ID parameter.",
        }
}