{\rtf1\ansi\ansicpg1252\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import os\
import pandas as pd\
import numpy as np\
from datetime import datetime, timedelta\
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent\
from langchain.agents import AgentType\
from langchain_openai import ChatOpenAI\
from dotenv import load_dotenv\
\
# Load environment variables and set OpenAI API key\
load_dotenv()\
openai_api_key = os.getenv("OPENAI_API_KEY")\
if not openai_api_key:\
    raise ValueError("OpenAI API key not found. Please set it in your environment variables.")\
\
# Setting up the OpenAI API key in the agent\
os.environ["OPENAI_API_KEY"] = openai_api_key\
\
# Set a random seed for reproducibility\
np.random.seed(42)\
\
# --- Step 1: Generate Sample Transaction Data ---\
\
def generate_transaction_data():\
    """\
    Generate a sample dataset representing financial transactions, including amount, location, and time.\
    """\
    n_rows = 1000\
    start_date = datetime(2022, 1, 1)\
    dates = [start_date + timedelta(days=i) for i in range(n_rows)]\
    \
    locations = ['New York', 'Los Angeles', 'San Francisco', 'Miami', 'Chicago', 'London', 'Berlin', 'Paris']\
    merchants = ['Amazon', 'Walmart', 'Target', 'Starbucks', 'eBay', 'Apple', 'Nike', 'BestBuy']\
    \
    data = \{\
        'Date': dates,\
        'TransactionID': np.arange(1, n_rows + 1),\
        'Amount': np.random.uniform(10, 10000, n_rows).round(2),\
        'AccountAge': np.random.randint(1, 365*10, n_rows),  # Account age in days\
        'Location': np.random.choice(locations, n_rows),\
        'Merchant': np.random.choice(merchants, n_rows),\
        'IsFlaggedFraud': np.random.choice([0, 1], n_rows, p=[0.95, 0.05]),  # 5% flagged as fraud\
    \}\
    \
    df = pd.DataFrame(data).sort_values('Date')\
    return df\
\
# Create the sample transaction data\
df = generate_transaction_data()\
\
# Display sample data info\
print("\\nFirst few rows of the generated transaction data:")\
print(df.head())\
print("\\nDataFrame info:")\
df.info()\
\
# --- Step 2: Create the Fraud Analysis Agent ---\
\
def create_fraud_agent(df):\
    """\
    Create a Pandas DataFrame agent that can analyze the transaction dataset and answer fraud-related questions.\
    """\
    agent = create_pandas_dataframe_agent(\
        ChatOpenAI(model="gpt-4", temperature=0),\
        df,\
        verbose=True,\
        allow_dangerous_code=True,\
        agent_type=AgentType.OPENAI_FUNCTIONS,\
    )\
    return agent\
\
# Initialize the agent\
agent = create_fraud_agent(df)\
print("Fraud Analyst Agent is ready. You can now ask fraud-related questions about the data.")\
\
# --- Step 3: Define the Question-Asking Function ---\
\
def ask_fraud_agent(question):\
    """\
    Function to ask fraud-related questions to the agent and display the response.\
    """\
    response = agent.run(\{\
        "input": question,\
        "agent_scratchpad": f"Human: \{question\}\\nAI: To answer this question, I need to use Python to analyze the dataframe. I'll use the python_repl_ast tool.\\n\\nAction: python_repl_ast\\nAction Input: ",\
    \})\
    print(f"Question: \{question\}")\
    print(f"Answer: \{response\}")\
    print("---")\
\
# --- Step 4: Example Fraud-Related Questions ---\
\
# Ask example fraud analysis questions\
ask_fraud_agent("What is the total amount of flagged fraudulent transactions?")\
ask_fraud_agent("Which merchant has the highest number of flagged fraud transactions?")\
ask_fraud_agent("Identify the transaction with the largest amount flagged as fraud.")\
ask_fraud_agent("What is the average amount of fraudulent transactions?")\
ask_fraud_agent("Are there any suspicious patterns in locations with high fraud rates?")\
}