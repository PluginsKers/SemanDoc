import json
from flask import Blueprint

# Use webargs for argument validation
from webargs import fields, ValidationError
from webargs.flaskparser import use_kwargs

from src.modules.response import Response
from src.controllers.query_controller import query_documents

query_blueprint = Blueprint("query", __name__)

# Define argument validation rules
query_args = {
    "query": fields.Str(required=True, validate=lambda val: len(val) > 0),
    "k": fields.Int(missing=10),  # Default value is 10
    "filter": fields.Str(missing=None),  # Default is None
}


@query_blueprint.route("/", methods=["GET"])
@use_kwargs(query_args, location="query")
async def query_route(query: str, k: int, filter: str):
    try:
        filter_dict = None
        if filter:
            filter_dict = json.loads(filter)
            if not isinstance(filter_dict, dict):
                raise ValidationError(
                    "The 'filter' parameter must be a valid JSON object."
                )

        res = await query_documents(query, k, filter_dict)
        return Response("Query successful.", 200, data=res)

    except ValidationError as error:
        return Response(f"Parameter error: {error.messages}", 400)
    except Exception as error:
        return Response(f"Internal server error: {error}", 500)
