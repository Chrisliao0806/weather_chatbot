# weather_chatbot
## Overview

`weather_chatbot` is a Python project that provides an interactive weather forecasting chatbot. It fetches weather data from the Taiwan Central Weather Bureau Open Data API and uses a language model to answer user queries about the weather.

## Features

- Fetches weather data from the Taiwan Central Weather Bureau Open Data API.
- Uses a language model to interpret and respond to user queries in Chinese.
- Provides weather information for specific districts in Taipei.

## Requirements

- Python 3.7+
- `requests`
- `python-dotenv`
- `langchain_community`
- `langchain_core`
- `langchain_openai`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/weather_chatbot.git
    cd weather_chatbot
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory and add your API keys:
    ```env
    OPENAI_API_KEY=your_openai_api_key
    WEB_KEY=your_weather_api_key
    ```

## Usage

### Weather Crawler

The `crawler.py` script fetches weather data and saves it to a JSON file.

To run the crawler:
```sh
python crawler.py
```

### Weather Chatbot

The `main.py` script starts an interactive chatbot that answers weather-related questions.

To run the chatbot:
```sh
python main.py
```

You can ask questions like:
- "明天台北的天氣如何？"
- "這個禮拜北投區的天氣如何？"

## Project Structure

- `crawler.py`: Fetches and saves weather data from the API.
- `main.py`: Contains the chatbot logic and handles user interactions.
- `README.md`: Project documentation.

## License

This project is licensed under the MIT License.