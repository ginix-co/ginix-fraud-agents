{\rtf1\ansi\ansicpg1252\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww35640\viewh19180\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 #!/usr/bin/env python3\
"""\
plaid_o1_agent.py\
\
A Python script that integrates with Plaid to fetch financial transaction data\
and uses OpenAI's o1-mini and o1-preview models to perform basic fraud analysis\
on connected accounts.\
\
Prerequisites:\
- Python 3.7+\
- Install required libraries:\
    pip install plaid-python openai python-dotenv\
\
Setup:\
1. Create a `.env` file in the same directory as this script with the following content:\
\
    PLAID_CLIENT_ID=your_plaid_client_id\
    PLAID_SECRET=your_plaid_secret\
    PLAID_ENV=sandbox  # or 'development' or 'production'\
    OPENAI_API_KEY=your_openai_api_key\
\
2. Replace placeholder values with your actual Plaid and OpenAI credentials.\
\
Usage:\
    python plaid_o1_agent.py\
"""\
\
import os\
import sys\
import openai\
import logging\
from datetime import datetime, timedelta\
from plaid import Client\
from plaid.errors import PlaidError\
from dotenv import load_dotenv\
\
# Configure logging\
logging.basicConfig(\
    level=logging.INFO,\
    format='%(asctime)s [%(levelname)s] %(message)s',\
    handlers=[\
        logging.StreamHandler(sys.stdout)\
    ]\
)\
\
# Load environment variables from .env file\
load_dotenv()\
\
# Plaid Configuration\
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')\
PLAID_SECRET = os.getenv('PLAID_SECRET')\
PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')  # Default to 'sandbox' if not set\
\
# OpenAI Configuration\
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')\
\
if not all([PLAID_CLIENT_ID, PLAID_SECRET, OPENAI_API_KEY]):\
    logging.error("Missing one or more required environment variables. Please check your .env file.")\
    sys.exit(1)\
\
# Initialize Plaid client\
client = Client(\
    client_id=PLAID_CLIENT_ID,\
    secret=PLAID_SECRET,\
    environment=PLAID_ENV\
)\
\
# Initialize OpenAI client\
openai.api_key = OPENAI_API_KEY\
\
def create_link_token():\
    """\
    Creates a Plaid Link token.\
    In a real application, this token should be sent to the frontend to initialize Plaid Link.\
    """\
    try:\
        response = client.LinkToken.create(\{\
            'user': \{\
                'client_user_id': 'unique_user_id_123',  # Replace with a unique user ID\
            \},\
            'client_name': 'giniX Fraud Analysis',\
            'products': ['transactions'],\
            'country_codes': ['US'],\
            'language': 'en',\
        \})\
        link_token = response['link_token']\
        logging.info(f"Link Token Created: \{link_token\}")\
        return link_token\
    except PlaidError as e:\
        logging.error(f"Error creating Link Token: \{e\}")\
        return None\
\
def exchange_public_token(public_token):\
    """\
    Exchanges a public token for an access token.\
    """\
    try:\
        exchange_response = client.Item.public_token.exchange(public_token)\
        access_token = exchange_response['access_token']\
        item_id = exchange_response['item_id']\
        logging.info(f"Access Token Obtained: \{access_token\}")\
        logging.info(f"Item ID: \{item_id\}")\
        return access_token, item_id\
    except PlaidError as e:\
        logging.error(f"Error exchanging public token: \{e\}")\
        return None, None\
\
def get_transactions(access_token, days=30):\
    """\
    Fetches transactions for the given access token over the specified number of days.\
    """\
    try:\
        end_date = datetime.now()\
        start_date = end_date - timedelta(days=days)\
        response = client.Transactions.get(\
            access_token,\
            start_date=start_date.strftime('%Y-%m-%d'),\
            end_date=end_date.strftime('%Y-%m-%d')\
        )\
        transactions = response['transactions']\
        logging.info(f"Fetched \{len(transactions)\} transactions.")\
        return transactions\
    except PlaidError as e:\
        logging.error(f"Error fetching transactions: \{e\}")\
        return []\
\
def analyze_transaction(transaction):\
    """\
    Uses OpenAI's LLM to analyze a single transaction for potential fraud.\
    """\
    prompt = f"""\
    You are a financial fraud detection assistant. Analyze the following transaction and determine if it is potentially fraudulent. Provide a brief explanation.\
\
    Transaction Details:\
    - Transaction ID: \{transaction['transaction_id']\}\
    - Amount: $\{transaction['amount']\}\
    - Date: \{transaction['date']\}\
    - Merchant: \{transaction['merchant_name']\}\
    - Category: \{', '.join(transaction['category'])\}\
    - Location: \{transaction['location']\}\
\
    Is this transaction potentially fraudulent? Yes or No. Explanation:\
    """\
\
    try:\
        response = openai.Completion.create(\
            engine="o1-preview",  # Replace with the correct model name if different\
            prompt=prompt,\
            max_tokens=60,\
            temperature=0.3,\
            n=1,\
            stop=None,\
        )\
        analysis = response.choices[0].text.strip()\
        logging.debug(f"Analysis for Transaction \{transaction['transaction_id']\}: \{analysis\}")\
        return analysis\
    except Exception as e:\
        logging.error(f"Error analyzing transaction \{transaction['transaction_id']\}: \{e\}")\
        return "No"\
\
def perform_fraud_analysis(transactions):\
    """\
    Analyzes a list of transactions and returns those flagged as potentially fraudulent.\
    """\
    fraud_results = []\
    for transaction in transactions:\
        analysis = analyze_transaction(transaction)\
        if "Yes" in analysis:\
            fraud_results.append(\{\
                'transaction_id': transaction['transaction_id'],\
                'amount': transaction['amount'],\
                'merchant_name': transaction['merchant_name'],\
                'date': transaction['date'],\
                'analysis': analysis\
            \})\
    logging.info(f"Detected \{len(fraud_results)\} potentially fraudulent transactions.")\
    return fraud_results\
\
def monitor_transaction(transaction, iso_forest, label_encoder, scaler):\
    """\
    Monitors a single transaction in real-time for anomalies using Isolation Forest.\
    """\
    try:\
        # Preprocess transaction\
        transaction_encoded = label_encoder.transform([transaction['location']])[0]\
        transaction_scaled = scaler.transform([[transaction['amount']]])[0][0]\
        transaction_features = ' '.join(map(str, [transaction_scaled, transaction_encoded]))\
\
        # Get embedding using o1-mini\
        embedding = get_embeddings([transaction_features])[0]\
\
        # Predict anomaly\
        score = iso_forest.decision_function([embedding])[0]\
        anomaly = iso_forest.predict([embedding])[0]\
\
        if anomaly == -1:\
            logging.warning(f"Alert: Suspicious transaction detected! Transaction ID: \{transaction['transaction_id']\}")\
            print(f"Alert: Suspicious transaction detected! Transaction ID: \{transaction['transaction_id']\}")\
        else:\
            logging.info(f"Transaction ID: \{transaction['transaction_id']\} is normal.")\
            print(f"Transaction ID: \{transaction['transaction_id']\} is normal.")\
    except Exception as e:\
        logging.error(f"Error monitoring transaction \{transaction['transaction_id']\}: \{e\}")\
\
def get_embeddings(data):\
    """\
    Generates embeddings for the provided data using OpenAI's o1-mini model.\
    """\
    try:\
        response = openai.Embedding.create(\
            input=data,\
            model="o1-mini"  # Replace with the correct model name if different\
        )\
        embeddings = [embedding['embedding'] for embedding in response['data']]\
        return embeddings\
    except Exception as e:\
        logging.error(f"Error generating embeddings: \{e\}")\
        return []\
\
def setup_isolation_forest(X_train_embeddings, contamination=0.05):\
    """\
    Sets up and trains the Isolation Forest model for anomaly detection.\
    """\
    from sklearn.ensemble import IsolationForest\
\
    try:\
        iso_forest = IsolationForest(contamination=contamination, random_state=42)\
        iso_forest.fit(X_train_embeddings)\
        logging.info("Isolation Forest model trained successfully.")\
        return iso_forest\
    except Exception as e:\
        logging.error(f"Error training Isolation Forest: \{e\}")\
        return None\
\
def main():\
    """\
    Main function to execute the fraud analysis agent.\
    """\
    # Step 1: (Optional) Create a Link Token\
    # link_token = create_link_token()\
    # print(f"Use this link token in your frontend to connect accounts: \{link_token\}")\
\
    # Step 2: Exchange Public Token for Access Token\
    # public_token = 'public-sandbox-...'  # Obtain this from your frontend after user connects their account\
    # access_token, item_id = exchange_public_token(public_token)\
\
    # For demonstration purposes, we'll assume you already have an access_token\
    access_token = 'access-sandbox-...'  # Replace with your actual access token\
\
    if not access_token or access_token == 'access-sandbox-...':\
        logging.error("Please replace 'access-sandbox-...' with a valid Plaid access token.")\
        sys.exit(1)\
\
    # Step 3: Fetch Transactions\
    transactions = get_transactions(access_token, days=30)\
    if not transactions:\
        logging.error("No transactions fetched. Exiting.")\
        sys.exit(1)\
\
    # Step 4: Feature Engineering for Isolation Forest\
    from sklearn.preprocessing import LabelEncoder, StandardScaler\
\
    # Prepare data for Isolation Forest\
    locations = [txn['location'] for txn in transactions]\
    amounts = [[txn['amount']] for txn in transactions]\
\
    label_encoder = LabelEncoder()\
    location_encoded = label_encoder.fit_transform(locations)\
\
    scaler = StandardScaler()\
    amount_scaled = scaler.fit_transform(amounts)\
\
    # Combine features\
    import numpy as np\
    combined_features = np.hstack((amount_scaled, location_encoded.reshape(-1, 1)))\
\
    # Generate embeddings for Isolation Forest using o1-mini\
    combined_features_list = combined_features.tolist()\
    combined_features_str = [' '.join(map(str, row)) for row in combined_features_list]\
    embeddings = get_embeddings(combined_features_str)\
\
    if not embeddings:\
        logging.error("Failed to generate embeddings. Exiting.")\
        sys.exit(1)\
\
    # Step 5: Train Isolation Forest\
    iso_forest = setup_isolation_forest(embeddings)\
    if not iso_forest:\
        logging.error("Isolation Forest setup failed. Exiting.")\
        sys.exit(1)\
\
    # Step 6: Perform Fraud Analysis using LLM\
    fraud_results = perform_fraud_analysis(transactions)\
\
    # Step 7: Output Fraud Results\
    if fraud_results:\
        logging.info("Potential Fraudulent Transactions Detected:")\
        for fraud in fraud_results:\
            logging.info(f"Transaction ID: \{fraud['transaction_id']\}")\
            logging.info(f"Amount: $\{fraud['amount']\}")\
            logging.info(f"Merchant: \{fraud['merchant_name']\}")\
            logging.info(f"Date: \{fraud['date']\}")\
            logging.info(f"Analysis: \{fraud['analysis']\}\\n")\
    else:\
        logging.info("No suspicious transactions detected.")\
\
    # Step 8: Example of Real-time Monitoring\
    # new_transaction = \{\
    #     'transaction_id': 'new_txn_001',\
    #     'amount': 600,  # Potentially fraudulent amount\
    #     'merchant_name': 'Unknown Merchant',\
    #     'date': '2024-04-25',\
    #     'category': ['Shops'],\
    #     'location': 'Location_A'\
    # \}\
    # monitor_transaction(new_transaction, iso_forest, label_encoder, scaler)\
\
if __name__ == "__main__":\
    main()\
}