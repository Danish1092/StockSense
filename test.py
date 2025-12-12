import os
import requests

# Load Brave API key from environment variable or .env file
def get_brave_api_key():
    return os.getenv('BRAVE_API_KEY', 'BSAnsapKix69APjf0yk68lPZf2rsR51')


def brave_search(query, api_key=None):
    if api_key is None:
        api_key = get_brave_api_key()
    url = 'https://api.search.brave.com/res/v1/web/search'
    headers = {
        'Accept': 'application/json',
        'X-Subscription-Token': api_key
    }
    params = {
        'q': query,
        'count': 5
    }
    response = requests.get(url, headers=headers, params=params)
    return response


def main():
    query = 'What was the official TCS FY2024-2025 profit?'  # Updated query for TCS profit
    response = brave_search(query)
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("Response JSON:")
        print(data)
    except Exception as e:
        print("Failed to parse JSON response:", e)
        print("Raw Response:")
        print(response.text)


if __name__ == "__main__":
    main()
