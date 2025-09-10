import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline
import joblib
from nltk.corpus import stopwords
import nltk
import os


class IntentClassifier:
    def __init__(self, model_path='intent_classifier.joblib', data_path='data/intents.csv'):
        # Download required NLTK data
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')

        self.model_path = model_path
        self.data_path = data_path

        # Try to load existing model
        if os.path.exists(model_path):
            try:
                self.pipeline = joblib.load(model_path)
                print(f"Loaded existing model from {model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                self._initialize_and_train()
        else:
            print(f"No model found at {model_path}, training new model...")
            self._initialize_and_train()

    def _initialize_pipeline(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                stop_words=stopwords.words('english'),
                min_df=2,
                max_df=0.95,
                ngram_range=(1, 2)
            )),
            ('clf', MultinomialNB())
        ])

    def _initialize_and_train(self):
        self._initialize_pipeline()
        try:
            metrics = self.train(self.data_path)
            print("Model trained successfully!")
            print(f"Accuracy: {metrics['accuracy']:.2f}")
            self.save_model()
        except Exception as e:
            print(f"Error during training: {e}")
            raise

    def predict(self, text):
        # Ensure we have a model before prediction
        if not hasattr(self, 'pipeline'):
            raise ValueError(
                "No model available for prediction. Please train or load a model first.")

        # Get prediction probabilities
        pred_proba = self.pipeline.predict_proba([text])[0]
        max_confidence = np.max(pred_proba)

        if max_confidence > 0.4:  # Confidence threshold
            return self.pipeline.predict([text])[0]
        else:
            return "unknown"

    def train(self, data_path=None, test_size=0.2, random_state=42):
        if data_path is None:
            data_path = self.data_path

        # Load and prepare the data
        df = pd.read_csv(data_path)
        X = df['text'].values
        y = df['intent'].values

        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y
        )

        # Train the pipeline
        self.pipeline.fit(X_train, y_train)

        # Make predictions on test set
        y_pred = self.pipeline.predict(X_test)

        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred),
            'confusion_matrix': confusion_matrix(y_test, y_pred),
            'unique_intents': np.unique(y)
        }

        return metrics

    def save_model(self, path=None):
        if path is None:
            path = self.model_path
        joblib.dump(self.pipeline, path)
        print(f"Model saved to {path}")

    def load_model(self, path=None):
        if path is None:
            path = self.model_path
        self.pipeline = joblib.load(path)
        print(f"Model loaded from {path}")
