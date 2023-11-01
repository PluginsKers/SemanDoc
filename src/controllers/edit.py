from src.models.response import Response


def update(data: str, remark: str):
    """
    This function is primarily used to modify content based on the target.
    """
    return Response(200, f"{data} {remark}")


def add(data: str, remark: str):
    """
    This function is primarily used to add content to the index.
    """
    return Response(200, f"{data} {remark}")


def delete(data: str, remark: str):
    """
    This function is primarily used to delete indexed content based on the input information.
    """
    return Response(200, f"{data} {remark}")
