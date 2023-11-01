from src.models.response import Response


def update(data: str, remark: str):
    """
    这里主要是根据 target 进行修改内容
    """
    return Response(200, f"{data} {remark}")


def add(data: str, remark: str):
    """
    这里主要是向索引中添加内容
    """
    return Response(200, f"{data} {remark}")


def delete(data: str, remark: str):
    """
    这里主要是根据输入的信息进行索引内容的删除
    """
    return Response(200, f"{data} {remark}")
