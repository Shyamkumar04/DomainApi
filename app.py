from flask import Flask, request, jsonify
from flask_cors import CORS
import whois
import re
import socket
from datetime import datetime
from dateutil.parser import parse as date_parse

app = Flask(__name__)
CORS(app)

# Default TLDs
DEFAULT_TLDS = ['.com', '.net', '.in', '.org', '.xyz', '.club', '.biz', '.top', '.pro', '.id', '.ru', '.asia', '.nl']

def validate_domain(domain):
    """Validate domain format"""
    if not domain:
        return False
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    return re.match(pattern, domain) is not None

def normalize_date(date_value):
    """Normalize various date formats to YYYY-MM-DD"""
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
    """Perform WHOIS lookup with error handling"""
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
    else:  # POST
        data = request.get_json()
        domain_input = data.get('domain', '').strip().lower()
        tlds_input = data.get('tlds', '').strip()
    
    # Validate domain
    if not domain_input:
        return jsonify({'error': 'Domain parameter is required'}), 400
    if not validate_domain(domain_input):
        return jsonify({'error': 'Invalid domain format'}), 400
    
    # Process TLDs
    if tlds_input:
        custom_tlds = ['.' + tld.strip().lstrip('.') for tld in tlds_input.split(',') if tld.strip()]
        tlds_to_use = list(set(custom_tlds))  # Remove duplicates
    else:
        tlds_to_use = DEFAULT_TLDS
    
    # Generate domains to check
    domains_to_check = [domain_input]
    if '.' not in domain_input:
        domains_to_check = [domain_input + tld for tld in tlds_to_use]
    
    available = []
    registered = []
    
    for domain in domains_to_check:
        result = whois_lookup(domain)
        if result['is_taken']:
            registered.append({
                'domain': domain,
                **result
            })
        else:
            available.append(domain)
    
    return jsonify({
        'input': domain_input,
        'tlds_used': tlds_to_use,
        'available_domains': available,
        'registered_domains': registered
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
