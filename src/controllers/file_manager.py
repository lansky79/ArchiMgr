import os
import logging
import pandas as pd

class FileManager:
    @staticmethod
    def import_categories(excel_file, db):
        logging.info(f"开始导入分类: {excel_file}")
        try:
            df = pd.read_excel(excel_file)
            # 导入逻辑
        except Exception as e:
            logging.error(f"导入分类失败: {e}")
            raise 