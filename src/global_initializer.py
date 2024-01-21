from src.modules.docstore import DocStore

from src.modules.logging import logger

database = None


def initialize():
    global database
    if not database:
        logger.info("加载知识库中...")
        database = DocStore(
            "./data/",
            r"D:\Projects\Python\nlp\models\bge-large-zh"
        )
        logger.info("加载知识库完成!")


def get_docstore() -> DocStore:
    return database
