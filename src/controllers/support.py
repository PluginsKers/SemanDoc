from src.models.response import Response


def error(location, remark):
    """
    Support error marks
    """
    return Response(location, remark).success()


def reward(location, remark):
    """
    Support reward marks
    """
    return Response(location, remark).success()
