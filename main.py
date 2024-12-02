import cloudscraper
import re
import httpx
import random

from bs4 import BeautifulSoup
from fastapi import FastAPI

app = FastAPI()

proxies = httpx.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all").text
proxy_list = [proxy.strip() for proxy in proxies.strip().split('\n')]


def format_query(query):
    # Strip leading and trailing whitespace
    query = query.strip()
    
    # Remove all special characters (keeping only letters and spaces)
    query = re.sub(r'[^a-zA-Z\s]', '', query)
    
    # Split the string into words on spaces
    words = query.split()
    
    # Capitalize the first letter of each word and join with dashes
    formatted_query = '-'.join(word.capitalize() for word in words)
    
    return formatted_query


def unescape(text):
    # Remove junk from string.
    text = text.replace('\\', '').replace('\n', '').replace('\r', '').strip()
    text = text.strip()
    if len(text) == 0:
        return None 
    return text


def extract_name_records(html_source):
    soup = BeautifulSoup(html_source, 'html.parser')
    results = []

    records = soup.find_all('div', class_='record')
    for record in records:
        result = {}
        try:
            result['name'] = unescape(record.find('div', class_='name').text.strip())
        except AttributeError:
            result['name'] = None

        try:
            result['timestamp'] = unescape(record.find('div', class_='timestamp').text.strip())
        except AttributeError:
            result['timestamp'] = None

        try:
            result['lives_in'] = unescape(record.find('div', class_='resides').text.replace('Lives in', '').strip())
        except AttributeError:
            result['lives_in'] = None

        try:
            age_div = record.find('div', class_='age')
            if age_div:
                age_text = unescape(age_div.text.strip())
                result['birthday'] = re.search(r'Born on (.+?) \(', age_text).group(1)
                age_match = re.search(r'\((\d+) years old\)', age_text)
                if age_match:
                    result['age'] = int(age_match.group(1))
        except AttributeError:
            pass

        try:
            home_div = record.find('div', class_='location')
            if home_div:
                result['home'] = {}
                result['home']['address'] = unescape(home_div.find('span', class_='address').text.strip())

                home_facts = home_div.find('dl', class_='subfields')
                if home_facts:
                    for subfield in home_facts.find_all('div', class_='subfield'):
                        key = unescape(subfield.find('dt').text.strip().lower().replace(' ', '_'))
                        value = unescape(subfield.find('dd').text.strip())
                        if key == 'year_built':
                            year_match = re.search(r'\d+', value)
                            if year_match:
                                result['home'][key] = int(year_match.group())
                        else:
                            if not "_(" in key:
                                result['home'][key] = value
        except AttributeError:
            result['home'] = {}

        previous_addresses = []
        try:
            previous_address_divs = record.find_all('div', class_='location')[1:]  # Adjusted to skip the first which is current address
            for address_div in previous_address_divs:
                address = {}
                try:
                    address['address'] = unescape(address_div.find('span', class_='address').text.strip())
                    updated_match = re.search(r'\d+', unescape(address_div.find('span', class_='timestamp').text.replace('Recorded in', '').strip()))
                    if updated_match:
                        address['updated'] = int(updated_match.group())
                except AttributeError:
                    continue
                previous_addresses.append(address)
        except AttributeError:
            pass
        if previous_addresses:
            result['previous_addresses'] = previous_addresses

        try:
            phone_li = record.find('li', class_='phone')
            if phone_li:
                result['phone'] = unescape(phone_li.find('span', class_='number').text.strip())
        except AttributeError:
            result['phone'] = None

        try:
            email_li = record.find('li', class_='email')
            if email_li:
                result['email'] = unescape(email_li.find('span', class_='inbox').text.strip())
        except AttributeError:
            result['email'] = None

        results.append(result)

    return {'results': results}


def extract_phone_records(html_source):
    soup = BeautifulSoup(html_source, 'html.parser')
    
    records = []
    
    record_divs = soup.find_all('div', class_='record')
    
    for record_div in record_divs:
        record = {}
        
        name_element = record_div.find('div', class_='name')
        if name_element:
            record['name'] = unescape(name_element.text.strip())
        else:
            record['name'] = None
        
        resides_element = record_div.find('div', class_='resides')
        if resides_element:
            record['lives_in'] = unescape(resides_element.text.replace('Lives in', '').strip())
        else:
            record['lives_in'] = None
        
        age_element = record_div.find('div', class_='age')
        if age_element:
            age_text = unescape(age_element.text.strip())
            birthday_match = re.search(r'Born on (.+?) \(', age_text)
            if birthday_match:
                record['birthday'] = birthday_match.group(1)
            else:
                record['birthday'] = None
            
            age_match = re.search(r'\((\d+) years old\)', age_text)
            if age_match:
                record['age'] = int(age_match.group(1))
            else:
                record['age'] = None
        else:
            record['birthday'] = None
            record['age'] = None
        
        home_element = record_div.find('div', class_='location')
        if home_element:
            home_link = home_element.find('a', class_='web')
            if home_link:
                record['home'] = unescape(home_link.text.strip())
            else:
                record['home'] = None
        else:
            record['home'] = None
        
        email_elements = record_div.find_all('div', class_='email')
        if email_elements:
            record['emails'] = [unescape(element.find('a', class_='web').text.strip()) for element in email_elements]
        else:
            record['emails'] = None
        
        associate_elements = record_div.find_all('div', class_='associate')
        if associate_elements:
            record['associates'] = []
            for element in associate_elements:
                associate = {}
                link = element.find('a', class_='web')
                if link:
                    name_age_text = link.text.strip()
                    name_match = re.search(r'(.+)\s+\((\d+)\)', name_age_text)
                    if name_match:
                        associate['name'] = unescape(name_match.group(1))
                        associate['age'] = int(name_match.group(2))
                    else:
                        associate['name'] = unescape(name_age_text)
                        associate['age'] = None
                    record['associates'].append(associate)
        else:
            record['associates'] = None
        
        ip_elements = record_div.find_all('div', class_='ipActivity')
        if ip_elements:
            record['ips'] = []
            for element in ip_elements:
                ip = {}
                ip['address'] = unescape(element.find('a', class_='web').text.strip())
                ip_text = element.text.strip()
                timestamp_match = re.search(r'\((.+?)\)', ip_text)
                if timestamp_match:
                    ip['timestamp'] = timestamp_match.group(1)
                else:
                    ip['timestamp'] = None
                record['ips'].append(ip)
        else:
            record['ips'] = None
        
        records.append(record)
    
    return {'records': records}


def extract_email_records(html_source):
    soup = BeautifulSoup(html_source, 'html.parser')
    
    records = []
    
    record_divs = soup.find_all('div', class_='record')
    
    for record_div in record_divs:
        record = {}
        
        name_element = record_div.find('div', class_='name')
        if name_element:
            record['name'] = unescape(name_element.text.strip())
        else:
            record['name'] = None
        
        resides_element = record_div.find('div', class_='resides')
        if resides_element:
            record['lives_in'] = unescape(resides_element.text.replace('Lives in', '').strip())
        else:
            record['lives_in'] = None
        
        age_element = record_div.find('div', class_='age')
        if age_element:
            age_text = unescape(age_element.text.strip())
            birthday_match = re.search(r'Born on (.+?) \(', age_text)
            if birthday_match:
                record['birthday'] = birthday_match.group(1)
            else:
                record['birthday'] = None
            
            age_match = re.search(r'\((\d+) years old\)', age_text)
            if age_match:
                record['age'] = int(age_match.group(1))
            else:
                record['age'] = None
        else:
            record['birthday'] = None
            record['age'] = None
        
        home_element = record_div.find('div', class_='location')
        if home_element:
            home_link = home_element.find('a', class_='web')
            if home_link:
                record['home'] = unescape(home_link.text.strip())
            else:
                record['home'] = None
        else:
            record['home'] = None
        
        previous_addresses = []
        previous_address_divs = record_div.find_all('div', class_='location')
        for address_div in previous_address_divs[1:]:
            address = {}
            address_link = address_div.find('a', class_='web')
            if address_link:
                address['address'] = unescape(address_link.text.strip())
            else:
                address['address'] = None
            
            timestamp_element = address_div.find('span', class_='timestamp')
            if timestamp_element:
                address['timestamp'] = unescape(timestamp_element.text.strip())
            else:
                address['timestamp'] = None
            
            previous_addresses.append(address)
        
        if previous_addresses:
            record['previous_addresses'] = previous_addresses
        else:
            record['previous_addresses'] = None
        
        phone_element = record_div.find('div', class_='phone')
        if phone_element:
            phone_link = phone_element.find('a', class_='web')
            if phone_link:
                record['phone'] = unescape(phone_link.text.strip())
            else:
                record['phone'] = None
        else:
            record['phone'] = None
        
        records.append(record)
    
    return {'records': records}


def search_by_name(name, location):
    scraper = cloudscraper.CloudScraper()
    
    name = format_query(name)
    location = format_query(location)
    
    url = f"https://thatsthem.com/name/{name}/{location}"
    
    proxy = random.choice(proxy_list)
    response = scraper.get(url, proxies={"http": proxy})

    if "Found 0 results" in response.text:
        return {}
    
    if "Limit Reached" not in response.text:
        records = extract_name_records(response.text)
        return records
    
    return {}


def search_by_phone(phone_number):
    scraper = cloudscraper.CloudScraper()
    
    url = f"https://thatsthem.com/phone/{phone_number}"

    proxy = random.choice(proxy_list)
    response = scraper.get(url, proxies={"http": proxy})

    if "Found 0 results" in response.text:
        return {}
    
    if "Limit Reached" not in response.text:
        records = extract_phone_records(response.text)
        return records
    
    return {}


def search_by_email(email_address):
    scraper = cloudscraper.CloudScraper()
    
    url = f"https://thatsthem.com/email/{email_address}"

    proxy = random.choice(proxy_list)
    response = scraper.get(url, proxies={"http": proxy})

    if "Found 0 results" in response.text:
        return {}
    
    if "Limit Reached" not in response.text:
        records = extract_email_records(response.text)
        return records
    
    return {}

@app.get('/tt/email/{email}')
def email_search(email: str):
    return search_by_email(email_address=email)

@app.get('/tt/phone/{phone}')
def phone_search(phone: str):
    print(phone)
    return search_by_phone(phone_number=phone)

@app.get('/tt/name/{name}')
def name_search(name: str, location: str = ""):
    return search_by_name(name=name, location=location)
