from src.models.response import Response


def error(location, remark):
    """
    Support error marks
    """
    return Response(200, f"收到 {location} {remark}")


def reward(location, remark):
    """
    Support reward marks
    """
    return Response(200, f"收到 {location} {remark}")
