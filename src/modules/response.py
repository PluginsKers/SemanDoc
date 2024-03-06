import json
import logging
from flask import Response as FlaskResponse

# Configure logger for this module
logger = logging.getLogger(__name__)


class Response(FlaskResponse):
    def __init__(
        self,
        message=None,
        status_code=None,
        headers=None,
        data=None,
        content_type: str = "application/json",
        **kwargs
    ):
        # Serialize message if it's a dictionary
        if isinstance(message, dict):
            message = json.dumps(message)

        # Set default status code if not provided
        if status_code is None:
            status_code = 404

        # Prepare the response dictionary
        response_dict = {"code": status_code, "msg": message}

        # Include data in the response if provided
        if data is not None:
            if isinstance(data, (dict, list)):
                response_dict["data"] = data
            else:
                # Attempt to parse the data as JSON
                try:
                    logger.info("Attempting to format output")
                    formatted_data = json.loads(data)
                    response_dict["data"] = formatted_data
                except json.JSONDecodeError:
                    logger.warning("Failed to format response")
                    response_dict["data"] = json.dumps(
                        data, ensure_ascii=False)

        # Initialize the parent Flask Response with the formatted JSON response
        super().__init__(
            json.dumps(response_dict, ensure_ascii=False),
            response_dict['code'],
            headers,
            content_type,
            **kwargs
        )
