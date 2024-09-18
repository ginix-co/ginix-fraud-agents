
### 2. **Code Samples for Agents**
You’ll want to include some basic agent templates to make it easy for Fraud Analysts to get started.

#### **Rule-Based Fraud Detection Agent (rule_agent_template.py)**
```python
class RuleBasedFraudAgent:
    def __init__(self, threshold=10000):
        # Define fraud detection rules, such as transaction limits
        self.threshold = threshold

    def analyze_transaction(self, transaction):
        """
        Analyzes a transaction and flags it as fraud if it exceeds the threshold.
        
        Args:
            transaction (dict): A dictionary containing transaction data.
        
        Returns:
            bool: True if fraud is detected, False otherwise.
        """
        if transaction['amount'] > self.threshold:
            return True  # Flag as fraud
        return False  # Legitimate transaction

# Example usage
if __name__ == "__main__":
    agent = RuleBasedFraudAgent(threshold=10000)
    transaction = {'amount': 15000, 'account_id': 12345}
    if agent.analyze_transaction(transaction):
        print("Fraud detected!")
    else:
        print("Transaction is legitimate.")
