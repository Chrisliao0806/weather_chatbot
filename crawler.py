import datetime
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


class WeatherCrawler:
    """
    A class used to fetch and save weather data from the Taiwan Central Weather Bureau Open Data API.

    Attributes
    ----------
    url : str
        The URL endpoint for the weather data API.
    params : dict
        The parameters to be sent with the API request, including the authorization key, location ID, and response format.

    Methods
    -------
    update_time():
        Returns the current date in the format YYYY-MM-DD.
    fetch_data():
        Sends a GET request to the weather data API and returns the response data as a JSON object if successful, otherwise returns None.
    save_weather_json(output_filename="weather.json"):
        Fetches the weather data and saves it to a JSON file with the specified filename. Returns True if successful, otherwise returns False.
    """

    def __init__(self, dataset_id="F-D0047-093"):
        self.url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{dataset_id}"
        self.params = {
            "Authorization": os.getenv("WEB_KEY"),
            "locationId": "F-D0047-061",
            "format": "JSON",
        }

    def update_time(self):
        """
        Updates the current time.

        Returns:
            str: The current date in the format "YYYY-MM-DD".
        """
        return datetime.datetime.now().strftime("%Y-%m-%d")

    def fetch_data(self):
        """
        Fetches data from the specified URL with the given parameters.

        Makes a GET request to the URL stored in the instance variable `self.url`
        with the parameters stored in `self.params`.
        If the request is successful (status code 200), it returns the response data in JSON format.
        If the request fails, it returns None.

        Returns:
            dict or None: The response data in JSON format if the request is successful,
            otherwise None.
        """
        response = requests.get(self.url, params=self.params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None

    def save_weather_json(self, output_filename="weather.json"):
        """
        Fetches weather data and saves it to a JSON file.

        Args:
            output_filename (str): The name of the file to save the weather data to.
            Defaults to "weather.json".

        Returns:
            bool: True if the data was successfully fetched and saved, False otherwise.
        """
        data = self.fetch_data()["records"]["Locations"][0]
        if data:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        else:
            return False


if __name__ == "__main__":
    crawler = WeatherCrawler()
    success = crawler.save_weather_json()
    if success:
        print("Weather data saved successfully.")
    else:
        print("Failed to save weather data.")
