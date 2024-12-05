# FINEST FIAT Payment Analytics Dashboard

A simple dashboard for analyzing payment transactions using Streamlit.

## Setup

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
streamlit run app.py
```

3. Upload your transaction data CSV file with the following columns:
- transaction_id: Unique identifier for each transaction
- type: Transaction type (Deposit/Withdrawal)
- country: Country where the transaction occurred
- channel: Payment channel used
- method: Payment method
- amount: Transaction amount
- fee_amount: Fee charged for the transaction
- status: Transaction status (Completed/Failed)
- created_at: Transaction creation timestamp
- completed_at: Transaction completion timestamp
- currency: Transaction currency

A sample data file (sample_data.csv) is provided for testing.

## Features

- Transaction Overview:
  - Total transaction volume
  - Total fee revenue
  - Success rate
  - Daily transaction volume trend

- Fee Analysis:
  - Fee revenue by channel
  - Average fee percentage by channel

- Channel Performance:
  - Success rate by channel
  - Average processing time by channel

## Usage

1. Launch the dashboard using the command above
2. Upload your CSV file using the file uploader
3. View the automatically generated visualizations and metrics
4. Use the "Show Raw Data" checkbox to view the underlying data
