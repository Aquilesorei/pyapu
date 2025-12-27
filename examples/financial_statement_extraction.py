"""
Financial Statement Extraction Example

Demonstrates extracting structured data from financial reports.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


financial_schema = Object(
    description="Financial statement data",
    properties={
        "company_name": String,
        "report_type": String(description="e.g., Annual, Quarterly, 10-K"),
        "period": Object(properties={
            "start_date": String,
            "end_date": String,
            "fiscal_year": Number,
        }),
        "income_statement": Object(properties={
            "revenue": Number,
            "cost_of_goods_sold": Number,
            "gross_profit": Number,
            "operating_expenses": Number,
            "operating_income": Number,
            "net_income": Number,
            "earnings_per_share": Number,
        }),
        "balance_sheet": Object(properties={
            "total_assets": Number,
            "total_liabilities": Number,
            "total_equity": Number,
            "cash_and_equivalents": Number,
            "accounts_receivable": Number,
            "inventory": Number,
            "long_term_debt": Number,
        }),
        "cash_flow": Object(properties={
            "operating_activities": Number,
            "investing_activities": Number,
            "financing_activities": Number,
            "net_change_in_cash": Number,
        }),
        "key_ratios": Object(properties={
            "profit_margin": Number,
            "debt_to_equity": Number,
            "current_ratio": Number,
            "return_on_equity": Number,
        }),
        "currency": String,
        "auditor": String,
    }
)

financial_prompt = """
Extract financial data from this statement/report.

Guidelines:
- Extract figures from income statement, balance sheet, cash flow
- Note the reporting period
- Capture key financial ratios if present
- Identify the currency used
- Note the auditing firm
"""


def extract_financials(file_path: str):
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, financial_prompt, financial_schema)


if __name__ == "__main__":
    print("Financial Statement Extraction Example")
    print(f"Schema fields: {len(financial_schema.properties)}")
