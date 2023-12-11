from src.modules.database import DataBase

from src.modules.logging import logger

database = None


def initialize():
    global database
    if not database:
        logger.info("加载知识库中...")
        database = DataBase(
            "./data/",
            r"D:\Projects\Python\models\bge-large-zh"
        )
        logger.info("加载知识库完成!")


def get_database() -> DataBase:
    return database
