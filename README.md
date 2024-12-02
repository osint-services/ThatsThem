# thatsthem
An (unofficial) free API for That's Them (thatsthem.com) with rotating proxies and bot detection evasion. 
This is a fork of https://github.com/andrewcampi/thatsthem

Converted to a Python microservice that can search for information based on the targets name, address, email or phone number.

## Requirements
- Python 3.9 or higher

### Tech Stack
- The REST API framework being used is [FastAPI](https://fastapi.tiangolo.com/)
- The REST client being used is [httpx](https://www.python-httpx.org/)

### Setup
1. Create Python virtual environment. `python -m venv venv`
2. Activate virtual environment. `source venv/bin/activate`
3. Install dependencies. `pip install -r requirements.txt`
4. Start server. `fastapi dev main.py` 

### Endpoints
- GET `/tt/email/{email}` - Pass the email that you would like searched, returns all results found for that email.
- GET `/tt/phone/{phone}` - Pass the phone that you would like searched (XXX-XXX-XXXX), returns all results found for that phone number.
- GET `/tt/name/{name}?location={location}` - Pass the name that you would like searched and the location as an optional query parameter.


```json
{
    "results":
    [
        {
            "name":"John M. Doe",
            "timestamp":"Last updated 1 year ago.",
            "lives_in":"Bowie, AK",
            "home": { "address":"12345 Milky Way.Bowie, AK20715+1610" }
        }
    ]
}
```
