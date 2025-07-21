import services.logger.logger as logger
from services.db.remote.config import DB_CONFIG
import pymysql


class MysqlUtil:
    def __init__(self):
        self.DB_CONFIG = DB_CONFIG
        self.db = pymysql.connect(**self.DB_CONFIG)
        self.cursor = self.db.cursor(cursor=pymysql.cursors.DictCursor)

    # 获取单条数据
    def get_fetchone(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    # 获取多条数据
    def get_fetchall(self, sql, params=None):
        """
        执行SQL查询并返回所有结果。

        :param sql: SQL查询语句
        :param params: 查询参数（用于参数化查询）
        :return: 查询结果
        """
        try:
            if params:
                self.cursor.execute(sql, params)  # 使用参数化查询
            else:
                self.cursor.execute(sql)  # 无参数的查询
            return self.cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return []

    def sql_execute(self, sql):
        try:
            if self.db and self.cursor:
                self.cursor.execute(sql)
                affected_rows = self.cursor.rowcount
                self.db.commit()
                # logger.info(f"受影响的行数: {affected_rows}")
                return affected_rows
        except Exception as e:
            self.db.rollback()
            logger.error(sql)
            logger.error(e)
            logger.error("sql语句执行错误，已执行回滚操作")
            return False

    def sql_executemany(self, sql, params_list):
        """
        执行批量SQL更新操作。

        :param sql: SQL语句，使用%s作为参数占位符
        :param params_list: 参数列表，每个元素是一个元组，对应一条记录的参数
        :return: 受影响的行数
        """
        # logger.info("SQL Statement:")
        # for params in params_list:
        #     # 构建一个用于打印的 SQL 语句
        #     logger.info(sql % params)
        try:
            self.cursor.executemany(sql, params_list)
            self.db.commit()  # 提交事务
            return self.cursor.rowcount  # 返回受影响的行数
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            self.db.rollback()  # 回滚事务
            return 0

    def delete_data(self, delete_query):
        try:
            self.cursor.execute(delete_query)
            affected_rows = self.cursor.rowcount  # 获取受影响的行数
            self.db.commit()
            logger.info(f"删除成功，受影响的行数: {affected_rows}")
            return affected_rows
        except Exception as e:
            self.db.rollback()
            logger.error("删除失败:", e)

    @staticmethod
    def close(self):
        if self.cursor is not None:
            self.cursor.close()
        if self.db is not None:
            self.db.close()
