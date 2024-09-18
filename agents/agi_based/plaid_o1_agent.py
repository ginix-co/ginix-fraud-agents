#!/usr/bin/env python3
"""
plaid_o1_agent.py

A Python script that integrates with Plaid to fetch financial transaction data
and uses OpenAI's o1-mini and o1-preview models through Chat Completions
to perform basic fraud analysis on connected accounts.

Prerequisites:
- Python 3.7+
- Install required libraries:
    pip install plaid-python openai python-dotenv scikit-learn

Setup:
1. Create a `.env` file in the same directory as this script with the following content:

    PLAID_CLIENT_ID=your_plaid_client_id
    PLAID_SECRET=your_plaid_secret
    PLAID_ENV=sandbox  # or 'development' or 'production'
    OPENAI_API_KEY=your_openai_api_key

2. Replace placeholder values with your actual Plaid and OpenAI credentials.

Usage:
    python plaid_o1_agent.py
"""

import os
import openai
from plaid import Client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix

# Load environment variables from .env file
load_dotenv()

# Plaid Configuration
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')  # Default to 'sandbox' if not set

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not all([PLAID_CLIENT_ID, PLAID_SECRET, OPENAI_API_KEY]):
    print("Missing one or more required environment variables. Please check your .env file.")
    exit(1)

# Initialize Plaid client
client = Client(
    client_id=PLAID_CLIENT_ID,
    secret=PLAID_SECRET,
    environment=PLAID_ENV
)

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

def get_transactions(access_token, days=30):
    """
    Fetches transactions for the given access token over the specified number of days.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        response = client.Transactions.get(
            access_token,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        transactions = response['transactions']
        print(f"Fetched {len(transactions)} transactions.")
        return transactions
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return []

def analyze_transaction(transaction):
    """
    Uses OpenAI's Chat Completion API to analyze a single transaction for potential fraud.
    """
    prompt = f"""
    You are a financial fraud detection assistant. Analyze the following transaction and determine if it is potentially fraudulent. Provide a brief explanation.

    Transaction Details:
    - Transaction ID: {transaction['transaction_id']}
    - Amount: ${transaction['amount']}
    - Date: {transaction['date']}
    - Merchant: {transaction['merchant_name']}
    - Category: {', '.join(transaction['category'])}
    - Location: {transaction['location']}

    Is this transaction potentially fraudulent? Yes or No. Explanation:
    """

    try:
        response = openai.ChatCompletion.create(
            model="o1-preview",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=60,
            temperature=0.3,
        )
        analysis = response.choices[0].message.content.strip()
        return analysis
    except Exception as e:
        print(f"Error analyzing transaction {transaction['transaction_id']}: {e}")
        return "No"

def perform_fraud_analysis(transactions):
    """
    Analyzes a list of transactions and returns those flagged as potentially fraudulent.
    """
    fraud_results = []
    for transaction in transactions:
        analysis = analyze_transaction(transaction)
        if "Yes" in analysis:
            fraud_results.append({
                'transaction_id': transaction['transaction_id'],
                'amount': transaction['amount'],
                'merchant_name': transaction['merchant_name'],
                'date': transaction['date'],
                'analysis': analysis
            })
    print(f"Detected {len(fraud_results)} potentially fraudulent transactions.")
    return fraud_results

def main():
    """
    Main function to execute the fraud analysis agent.
    """
    # Replace with your actual Plaid access token
    access_token = 'access-sandbox-...'  # TODO: Replace with a valid access token

    if access_token == 'access-sandbox-...':
        print("Please replace 'access-sandbox-...' with a valid Plaid access token.")
        exit(1)

    # Fetch transactions
    transactions = get_transactions(access_token, days=30)
    if not transactions:
        print("No transactions fetched. Exiting.")
        exit(1)

    # Convert transactions to DataFrame for feature engineering
    df = pd.DataFrame(transactions)

    # Feature Engineering
    label_encoder = LabelEncoder()
    df['location_encoded'] = label_encoder.fit_transform(df['location'])

    scaler = StandardScaler()
    df['amount_scaled'] = scaler.fit_transform(df[['amount']])

    # Select features
    features = ['amount_scaled', 'location_encoded']
    X = df[features]
    y = df['is_fraud']

    # Train Isolation Forest for anomaly detection
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    iso_forest.fit(X)

    # Perform fraud analysis using LLM
    fraud_results = perform_fraud_analysis(transactions)

    # Output fraud results
    if fraud_results:
        print("Potential Fraudulent Transactions Detected:")
        for fraud in fraud_results:
            print(f"Transaction ID: {fraud['transaction_id']}")
            print(f"Amount: ${fraud['amount']}")
            print(f"Merchant: {fraud['merchant_name']}")
            print(f"Date: {fraud['date']}")
            print(f"Analysis: {fraud['analysis']}\n")
    else:
        print("No suspicious transactions detected.")

if __name__ == "__main__":
    main()
