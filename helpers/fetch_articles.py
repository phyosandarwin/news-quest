from pycountry import countries
from typing import Any, Dict, List, Optional
from datetime import datetime
import requests

# indicate country filters 
def get_country_code(name: str) -> str:
    try:
        return countries.get(name=name).alpha_2
    except AttributeError:
        raise ValueError(f'No country code found for "{name}"')

def get_country_names(codes: List[str]) -> List[str]:
    return [countries.get(alpha_2=code).name for code in codes]

COUNTRY_CODES = [
    'ae', 'ar', 'at', 'au', 'be', 'bg', 'br', 'ca', 'ch', 'cn', 'co', 'cu', 'cz', 'de', 'eg', 'fr', 'gb',
    'gr', 'hk', 'hu', 'id', 'ie', 'il', 'in', 'it', 'jp', 'kr', 'lt', 'lv', 'ma', 'mx', 'my', 'ng', 'nl',
    'no', 'nz', 'ph', 'pl', 'pt', 'ro', 'rs', 'ru', 'sa', 'se', 'sg', 'si', 'sk', 'th', 'tr', 'tw', 'ua',
    'us', 've', 'za'
]
COUNTRY_NAMES = get_country_names(COUNTRY_CODES)

# indicate date of article 
def format_date(date_string: str) -> Optional[str]:
    try:
        date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, TypeError):
        return None
    return date.strftime('%d %B %Y')

def fetch_everything(topic, fields, newsapi):
    url = f'https://newsapi.org/v2/everything?q={topic}&sortBy=relevancy&pageSize=10&searchIn={fields}&language=en&apiKey={newsapi}'
    response = requests.get(url)
    return response.json()

def fetch_headlines(category, countrycode, newsapi):
    url = f'https://newsapi.org/v2/top-headlines?country={countrycode}&pageSize=10&category={category}&apiKey={newsapi}'
    response = requests.get(url)
    return response.json()