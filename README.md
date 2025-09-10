# Flight Booking Assistant 🛫

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![GitHub repo size](https://img.shields.io/github/repo-size/kasundularaam/flight-booking-assistant?style=flat-square)](https://github.com/kasundularaam/flight-booking-assistant)
[![GitHub last commit](https://img.shields.io/github/last-commit/kasundularaam/flight-booking-assistant?style=flat-square)](https://github.com/kasundularaam/flight-booking-assistant/commits)
[![GitHub stars](https://img.shields.io/github/stars/kasundularaam/flight-booking-assistant?style=flat-square)](https://github.com/kasundularaam/flight-booking-assistant/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/kasundularaam/flight-booking-assistant?style=flat-square)](https://github.com/kasundularaam/flight-booking-assistant/network)
[![GitHub issues](https://img.shields.io/github/issues/kasundularaam/flight-booking-assistant?style=flat-square)](https://github.com/kasundularaam/flight-booking-assistant/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/kasundularaam/flight-booking-assistant?style=flat-square)](https://github.com/kasundularaam/flight-booking-assistant/pulls)

A conversational AI chatbot for Berry Airlines that helps users search, book, and manage flight reservations through natural language interactions. The system uses machine learning for intent classification and provides a seamless booking experience via command-line interface.

## Features ✨

- **Natural Language Understanding**: Powered by TF-IDF vectorization and Naive Bayes classification
- **Intent Recognition**: Automatically classifies user messages into actionable intents
- **Transaction Management**: Handles complex multi-step booking flows with state management
- **User Authentication**: Secure login and user management system
- **Flight Search & Booking**: Search available flights and complete bookings
- **Persistent Storage**: SQLite database for flight data and user information
- **Confidence-based Responses**: Handles uncertain inputs gracefully

## Tech Stack 🔧

- **Python 3.x**
- **scikit-learn** - Machine learning for intent classification
- **pandas & numpy** - Data manipulation and analysis
- **NLTK** - Natural language processing
- **joblib** - Model serialization
- **SQLite** - Database management

## Project Structure 📁

```
flight-booking-assistant/
├── data/
│   ├── flights.csv          # Flight data
│   └── intents.csv          # Training data for intent classification
├── db/
│   └── airline.db           # SQLite database
├── services/
│   ├── auth.py              # Authentication service
│   ├── booking.py           # Booking management
│   └── flight.py            # Flight search operations
├── transactions/
│   ├── auth_flow.py         # Authentication transaction flow
│   ├── booking.py           # Booking transaction flow
│   ├── factory.py           # Transaction factory pattern
│   └── transaction.py       # Base transaction class
├── utils/
│   └── database.py          # Database utilities
├── intent_classifier.py    # ML intent classification model
├── main.py                  # Main chatbot application
└── requirements.txt         # Python dependencies
```

## Installation 🚀

1. **Clone the repository**
   ```bash
   git clone https://github.com/kasundularaam/flight-booking-assistant.git
   cd flight-booking-assistant
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download NLTK data** (automatically handled on first run)
   ```python
   import nltk
   nltk.download('stopwords')
   ```

## Usage 💬

1. **Start the chatbot**
   ```bash
   python main.py
   ```

2. **Interact with the bot**
   ```
   Bot: Hello! Welcome to Berry Airlines. How can I help you today?
   You: I want to book a flight to New York
   Bot: I'd be happy to help you book a flight to New York...
   ```

3. **Exit the conversation**
   - Type `exit`, `quit`, or `bye`
   - Or press `Ctrl+C`

## Intent Classification 🧠

The system recognizes various user intents including:
- Flight booking requests
- Authentication/login
- Flight status inquiries
- General information requests

The classifier uses:
- **TF-IDF Vectorization** with stop words removal
- **Multinomial Naive Bayes** for classification
- **Confidence threshold** (>40%) for reliable predictions
- **N-gram features** (unigrams and bigrams)

## Model Training 📊

The intent classifier automatically:
- Trains on startup if no model exists
- Loads existing trained models for faster startup
- Saves trained models using joblib
- Provides training metrics and accuracy reports

To retrain the model:
```python
from intent_classifier import IntentClassifier
classifier = IntentClassifier()
metrics = classifier.train('data/intents.csv')
```

## Transaction System 🔄

The chatbot uses a transaction-based architecture:
- **State Management**: Maintains conversation context
- **Factory Pattern**: Creates appropriate transaction handlers
- **Cleanup**: Automatically cleans up completed transactions
- **Error Handling**: Graceful error recovery and fallbacks

## Database Schema 🗄️

The SQLite database (`db/airline.db`) stores:
- Flight information and schedules
- User accounts and authentication data
- Booking records and transactions
- System configuration

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Author 👨‍💻

**Kasun Dularaam**
- GitHub: [@kasundularaam](https://github.com/kasundularaam)

---

⭐ Star this repo if you found it helpful!