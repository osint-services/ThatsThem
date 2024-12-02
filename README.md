# thatsthem
An (unofficial) free API for That's Them (thatsthem.com) with rotating proxies and bot detection evasion

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