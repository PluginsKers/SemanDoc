from src.models.response import Response


def search(query: str, result_type: str, iterations: int, model: str):
    """
    This function handles the search business logic and typically involves
    building a thread-safe process for working with index files.

    Args:
        - query (str): The search query.
        - result_type (str): The type of result to return (json, txt, jsonl).
        - iterations (int): The number of search iterations.
        - model (str): The model to use for searching.

    Returns:
        - Response: A Response object containing the search results.
    """

    # Check if the result_type is valid
    if result_type not in ["json", "txt", "jsonl"]:
        raise ValueError(
            "Invalid result_type. Should be 'json', 'txt', or 'jsonl'")

    # Generate a successful response
    response = Response("1", "1", "3", query, result_type,
                        str(iterations), model)
    return response.success()
