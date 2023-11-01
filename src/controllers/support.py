from src.models.response import Response


def error(location, remark):
    """
    这里主要是上报错误
    """
    return Response(200, f"收到 {location} {remark}")


def reward(location, remark):
    """
    这里主要是回复点赞，奖励标记
    """
    return Response(200, f"收到 {location} {remark}")
