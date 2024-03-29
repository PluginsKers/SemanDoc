from flask import Blueprint
from webargs.flaskparser import use_kwargs
from webargs import (
    fields,
    ValidationError
)

from src.modules import Response
from src.controllers.search_controllers import (
    get_documents,
    chat_with_kb
)

search_blueprint = Blueprint("search", __name__)


def parse_int_or_default(val):
    try:
        # Attempt to convert the value to an integer
        return int(val)
    except ValueError:
        # If the conversion fails (e.g., empty string), return a default value
        if val == "":
            return 6
        raise ValidationError("Invalid value for integer.")


search_args = {
    "query": fields.Str(required=True, validate=lambda val: len(val) > 0),
    # Default value is 6
    "k": fields.Function(deserialize=parse_int_or_default, missing=6, allow_none=True),
    "filter": fields.Dict(missing=None, allow_none=True),  # Default is None
    "score_threshold": fields.Float(missing=1, allow_none=True),
    "powerset": fields.Bool(missing=True, allow_none=True),
}

chat_args = {
    "message": fields.Str(required=True, validate=lambda val: len(val) > 0),
    "dep_name": fields.Str(missing=None, allow_none=True),  # Default is None
}


@search_blueprint.route("/", methods=['POST'])
@use_kwargs(search_args, location="json")
def search_route(query: str, k: int, filter: dict, score_threshold: float, powerset: bool):
    try:
        docs_dict = get_documents(
            query_text=query,
            k=k,
            filter=filter,
            score_threshold=score_threshold,
            powerset=powerset
        )
        return Response("Query successful.", 200, docs_dict)

    except ValidationError as error:
        return Response(f"Parameter error: {error.messages}", 400)
    except Exception as error:
        return Response(f"Internal server error: {error}", 500)


@search_blueprint.route("/chat", methods=['POST'])
@use_kwargs(chat_args, location="json")
def chat_route(message: str, dep_name: str):
    try:
        res = chat_with_kb(message, dep_name)
        return Response("Respones successful.", 200, {"response": res})
    except ValidationError as error:
        return Response(f"Parameter error: {error.messages}", 400)
    except Exception as error:
        return Response(f"Internal server error: {error}", 500)
