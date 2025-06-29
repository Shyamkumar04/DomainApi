from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import whois
import re
import socket
from datetime import datetime
from dateutil.parser import parse as date_parse

app = Flask(__name__)
CORS(app)

SEARCH_PAGE_URL = "https://www.instra.com/en/domain-names/country-page/all-country"
POST_URL = "https://www.instra.com/en/domain-application/search-result"

DEFAULT_TLDS = ['.com', '.net', '.in', '.org', '.xyz', '.club', '.biz', '.top', '.pro', '.id', '.ru', '.asia', '.nl']

# -------------------------- WHOIS TOOLS -------------------------- #

def validate_domain(domain):
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    return re.match(pattern, domain) is not None

def normalize_date(date_value):
    if not date_value:
        return None
    try:
        if isinstance(date_value, list):
            date_value = date_value[0]
        if isinstance(date_value, str):
            return date_parse(date_value).strftime('%Y-%m-%d')
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
    except Exception:
        return None
    return None

def whois_lookup(domain):
    try:
        socket.setdefaulttimeout(8)
        w = whois.whois(domain)
        return {
            'is_taken': True,
            'created_date': normalize_date(w.get('creation_date')),
            'expiry_date': normalize_date(w.get('expiration_date')),
            'registered_by': (
                w.get('registrant_name') or 
                w.get('org') or 
                w.get('registrant_organization') or 
                w.get('registrar') or 
                None
            ),
            'name_servers': (
                [ns.strip() for ns in w.name_servers] 
                if w.name_servers and isinstance(w.name_servers, list)
                else []
            )
        }
    except (whois.parser.PywhoisError, ConnectionResetError, TimeoutError):
        return {'is_taken': False}
    except Exception as e:
        app.logger.error(f"WHOIS error for {domain}: {str(e)}")
        return {'is_taken': False}
    finally:
        socket.setdefaulttimeout(None)

@app.route('/check-domain', methods=['GET', 'POST'])
def check_domain():
    if request.method == 'GET':
        domain_input = request.args.get('domain', '').strip().lower()
        tlds_input = request.args.get('tlds', '').strip()
    else:
        data = request.get_json()
        domain_input = data.get('domain', '').strip().lower()
        tlds_input = data.get('tlds', '').strip()
    
    if not domain_input:
        return jsonify({'error': 'Domain parameter is required'}), 400
    if not validate_domain(domain_input):
        return jsonify({'error': 'Invalid domain format'}), 400

    if tlds_input:
        custom_tlds = ['.' + tld.strip().lstrip('.') for tld in tlds_input.split(',') if tld.strip()]
        tlds_to_use = list(set(custom_tlds))
    else:
        tlds_to_use = DEFAULT_TLDS

    domains_to_check = [domain_input]
    if '.' not in domain_input:
        domains_to_check = [domain_input + tld for tld in tlds_to_use]

    available = []
    registered = []

    for domain in domains_to_check:
        result = whois_lookup(domain)
        if result['is_taken']:
            registered.append({'domain': domain, **result})
        else:
            available.append(domain)

    return jsonify({
        'input': domain_input,
        'tlds_used': tlds_to_use,
        'available_domains': available,
        'registered_domains': registered
    })

# -------------------------- INSTRA SCRAPER -------------------------- #

def extract_domain_statuses(html_content):
    pattern = re.compile(
        r"document\.getElementById\('response_(.*?)'\)\.innerHTML\s*=\s*'.*?>(Available|Unavailable)</a>'",
        re.DOTALL
    )
    matches = pattern.findall(html_content)

    domain_status = {}
    for raw_domain, status in matches:
        domain = raw_domain.strip()
        if ')' in domain or ';' in domain:
            continue
        if domain.endswith('_mobile'):
            domain = domain.replace('_mobile', '')
        domain_status[domain] = status.strip()

    return [{'domain': d, 'status': s} for d, s in domain_status.items()]

@app.route('/api/instra-domain-check', methods=['POST'])
def instra_domain_check():
    domain = request.form.get('input_domain_name')
    tld = request.form.get('tld', '.com')

    if not domain:
        return jsonify({'error': 'input_domain_name is required'}), 400

    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": SEARCH_PAGE_URL,
        }

        # Step 1: Fetch CSRF token
        get_resp = session.get(SEARCH_PAGE_URL, headers=headers)
        soup = BeautifulSoup(get_resp.text, 'html.parser')
        csrf_token_input = soup.find('input', {'name': '__csrf_token'})
        if not csrf_token_input or not csrf_token_input.get('value'):
            return jsonify({'error': 'CSRF token not found'}), 500

        csrf_value = csrf_token_input['value']

        # Step 2: Submit search request
        form_data = {
            '__csrf_token': csrf_value,
            'input_domain_name': domain,
            'hidden_domains': f"|{tld}",
            'domains[]': tld
        }

        post_resp = session.post(POST_URL, headers=headers, data=form_data)
        html_content = post_resp.text
        result = extract_domain_statuses(html_content)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -------------------------- MAIN ENTRY -------------------------- #

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
