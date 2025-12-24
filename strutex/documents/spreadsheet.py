import logging
from typing import Dict
import pandas as pd

logger = logging.getLogger(__name__)


def excel_to_csv_sheets(file_path: str) -> Dict[str, str]:
    """
    Reads an Excel file (.xlsx, .xls) and converts each sheet into a CSV string.

    :param file_path: Path to the Excel file.
    :return: A dictionary where the key is the Sheet Name and the value is the CSV content.
    """
    try:
        # Read all sheets (sheet_name=None returns a dict of DataFrames)
        # engine='openpyxl' is used implicitly for .xlsx
        xls_dict = pd.read_excel(file_path, sheet_name=None)

        processed_sheets = {}
        for sheet_name, df in xls_dict.items():
            # Convert to CSV string
            # index=False avoids adding a useless index column (saves tokens)
            csv_content = df.to_csv(index=False)
            processed_sheets[sheet_name] = csv_content

        return processed_sheets

    except Exception as e:
        logger.error(f"Failed to convert Excel file {file_path}: {e}")
        raise RuntimeError(f"Error reading Excel file: {e}") from e