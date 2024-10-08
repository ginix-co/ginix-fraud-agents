from sklearn.ensemble import RandomForestClassifier
import numpy as np

class MLBasedFraudAgent:
    def __init__(self):
        # Initialize a pre-trained machine learning model
        self.model = RandomForestClassifier()

    def train(self, X_train, y_train):
        """
        Train the model on transaction data.
        
        Args:
            X_train (np.array): Feature matrix of transaction data.
            y_train (np.array): Labels indicating fraud (1) or legitimate (0).
        """
        self.model.fit(X_train, y_train)

    def analyze_transaction(self, transaction_features):
        """
        Predict if a transaction is fraud or legitimate using the trained model.
        
        Args:
            transaction_features (np.array): Features of the transaction.
        
        Returns:
            bool: True if fraud is predicted, False otherwise.
        """
        prediction = self.model.predict([transaction_features])
        return bool(prediction[0])

# Example usage
if __name__ == "__main__":
    agent = MLBasedFraudAgent()
    # Train the agent with some data (dummy data here)
    X_train = np.array([[5000], [15000], [300], [7000]])  # Example feature set
    y_train = np.array([0, 1, 0, 0])  # Fraud (1) or Legitimate (0)
    agent.train(X_train, y_train)

    transaction_features = np.array([12000])  # A new transaction to analyze
    if agent.analyze_transaction(transaction_features):
        print("Fraud detected!")
    else:
        print("Transaction is legitimate.")
