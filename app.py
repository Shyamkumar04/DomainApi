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

# TLD Pricing Info
TLD_PRICES = {
".pro": {"registration": "0.98", "renewal": "15.99"},
".id": {"registration": "12.98", "renewal": "15.99"},
".asia": {"registration": "2.03", "renewal": "11.29"},
".in": {"registration": "7.99", "renewal": "7.99"},
".top": {"registration": "0.88", "renewal": "0.88"},
".nl": {"registration": "3.99", "renewal": "5.16"},
".ru": {"registration": "5.88", "renewal": "7.88"},
".org.uk": {"registration": "4.94", "renewal": "4.94"},
".uk": {"registration": "4.94", "renewal": "4.94"},
".me.uk": {"registration": "4.94", "renewal": "4.94"},
".co.uk": {"registration": "4.94", "renewal": "4.94"},
".date": {"registration": "4.16", "renewal": "5.16"},
".trade": {"registration": "4.16", "renewal": "5.16"},
".party": {"registration": "4.16", "renewal": "5.16"},
".bid": {"registration": "4.16", "renewal": "5.16"},
".stream": {"registration": "4.16", "renewal": "5.16"},
".win": {"registration": "4.16", "renewal": "5.16"},
".download": {"registration": "4.16", "renewal": "5.16"},
".loan": {"registration": "4.16", "renewal": "5.16"},
".men": {"registration": "4.16", "renewal": "5.16"},
".fyi": {"registration": "5.18", "renewal": "5.18"},
".us": {"registration": "6.5", "renewal": "6.5"},
".work": {"registration": "7.18", "renewal": "7.18"},
".rodeo": {"registration": "7.18", "renewal": "7.18"},
".casa": {"registration": "7.68", "renewal": "7.68"},
".nom.co": {"registration": "8", "renewal": "8"},
".net.co": {"registration": "8", "renewal": "8"},
".cc": {"registration": "8", "renewal": "8"},
".com.co": {"registration": "8", "renewal": "8"},
".contact": {"registration": "9.18", "renewal": "9.18"},
".pictures": {"registration": "9.18", "renewal": "9.18"},
".futbol": {"registration": "9.18", "renewal": "9.18"},
".observer": {"registration": "9.18", "renewal": "9.18"},
".business": {"registration": "9.18", "renewal": "9.18"},
".com": {"registration": "9.77", "renewal": "9.77"},
".org": {"registration": "7.5", "renewal": "10.11"},
".review": {"registration": "10.16", "renewal": "10.16"},
".science": {"registration": "10.16", "renewal": "10.16"},
".faith": {"registration": "10.16", "renewal": "10.16"},
".racing": {"registration": "10.16", "renewal": "10.16"},
".webcam": {"registration": "10.16", "renewal": "10.16"},
".xyz": {"registration": "10.18", "renewal": "10.18"},
".company": {"registration": "10.18", "renewal": "10.18"},
".mov": {"registration": "10.18", "renewal": "10.18"},
".nexus": {"registration": "10.18", "renewal": "10.18"},
".foo": {"registration": "10.18", "renewal": "10.18"},
".boston": {"registration": "10.18", "renewal": "10.18"},
".dad": {"registration": "10.18", "renewal": "10.18"},
".day": {"registration": "10.18", "renewal": "10.18"},
".rsvp": {"registration": "10.18", "renewal": "10.18"},
".page": {"registration": "10.18", "renewal": "10.18"},
".boo": {"registration": "10.18", "renewal": "10.18"},
".markets": {"registration": "11.18", "renewal": "11.18"},
".net": {"registration": "11.84", "renewal": "11.84"},
".dev": {"registration": "12.18", "renewal": "12.18"},
".miami": {"registration": "12.18", "renewal": "12.18"},
".club": {"registration": "12.18", "renewal": "12.18"},
".vip": {"registration": "12.18", "renewal": "12.18"},
".trading": {"registration": "13.18", "renewal": "13.18"},
".rocks": {"registration": "13.18", "renewal": "13.18"},
".jetzt": {"registration": "14.18", "renewal": "14.18"},
".app": {"registration": "14.18", "renewal": "14.18"},
".group": {"registration": "14.18", "renewal": "14.18"},
".irish": {"registration": "14.18", "renewal": "14.18"},
".gratis": {"registration": "14.18", "renewal": "14.18"},
".place": {"registration": "14.18", "renewal": "14.18"},
".reisen": {"registration": "14.18", "renewal": "14.18"},
".luxe": {"registration": "15.18", "renewal": "15.18"},
".kim": {"registration": "15.18", "renewal": "15.18"},
".pink": {"registration": "15.18", "renewal": "15.18"},
".cloud": {"registration": "15.18", "renewal": "15.18"},
".rip": {"registration": "15.18", "renewal": "15.18"},
".red": {"registration": "15.18", "renewal": "15.18"},
".blue": {"registration": "15.18", "renewal": "15.18"},
".biz": {"registration": "15.18", "renewal": "15.18"},
".management": {"registration": "16.18", "renewal": "16.18"},
".equipment": {"registration": "16.18", "renewal": "16.18"},
".soccer": {"registration": "16.18", "renewal": "16.18"},
".promo": {"registration": "16.18", "renewal": "16.18"},
".report": {"registration": "16.18", "renewal": "16.18"},
".pet": {"registration": "16.18", "renewal": "16.18"},
".schule": {"registration": "16.18", "renewal": "16.18"},
".supply": {"registration": "16.18", "renewal": "16.18"},
".supplies": {"registration": "16.18", "renewal": "16.18"},
".center": {"registration": "17.18", "renewal": "17.18"},
".gallery": {"registration": "17.18", "renewal": "17.18"},
".football": {"registration": "17.18", "renewal": "17.18"},
".photos": {"registration": "17.18", "renewal": "17.18"},
".graphics": {"registration": "17.18", "renewal": "17.18"},
".bet": {"registration": "17.18", "renewal": "17.18"},
".lighting": {"registration": "17.18", "renewal": "17.18"},
".run": {"registration": "17.18", "renewal": "17.18"},
".directory": {"registration": "17.18", "renewal": "17.18"},
".city": {"registration": "17.18", "renewal": "17.18"},
".pro": {"registration": "17.68", "renewal": "17.68"},
".info": {"registration": "17.68", "renewal": "17.68"},
".today": {"registration": "18.18", "renewal": "18.18"},
".soy": {"registration": "18.18", "renewal": "18.18"},
".dance": {"registration": "18.18", "renewal": "18.18"},
".agency": {"registration": "18.18", "renewal": "18.18"},
".institute": {"registration": "18.18", "renewal": "18.18"},
".support": {"registration": "18.18", "renewal": "18.18"},
".wiki": {"registration": "19.18", "renewal": "19.18"},
".ltd": {"registration": "19.18", "renewal": "19.18"},
".ink": {"registration": "19.18", "renewal": "19.18"},
".email": {"registration": "19.18", "renewal": "19.18"},
".accountant": {"registration": "20.16", "renewal": "20.16"},
".cricket": {"registration": "20.16", "renewal": "20.16"},
".technology": {"registration": "20.18", "renewal": "20.18"},
".love": {"registration": "20.18", "renewal": "20.18"},
".prof": {"registration": "20.18", "renewal": "20.18"},
".phd": {"registration": "20.18", "renewal": "20.18"},
".blog": {"registration": "20.18", "renewal": "20.18"},
".games": {"registration": "20.18", "renewal": "20.18"},
".international": {"registration": "20.18", "renewal": "20.18"},
".band": {"registration": "20.18", "renewal": "20.18"},
".esq": {"registration": "20.18", "renewal": "20.18"},
".solutions": {"registration": "20.18", "renewal": "20.18"},
".space": {"registration": "20.18", "renewal": "20.18"},
".how": {"registration": "20.18", "renewal": "20.18"},
".website": {"registration": "20.18", "renewal": "20.18"},
".news": {"registration": "21.18", "renewal": "21.18"},
".ninja": {"registration": "21.18", "renewal": "21.18"},
".live": {"registration": "21.18", "renewal": "21.18"},
".systems": {"registration": "21.18", "renewal": "21.18"},
".tips": {"registration": "21.18", "renewal": "21.18"},
".network": {"registration": "21.68", "renewal": "21.68"},
".gives": {"registration": "21.68", "renewal": "21.68"},
".immo": {"registration": "21.68", "renewal": "21.68"},
".foundation": {"registration": "21.68", "renewal": "21.68"},
".immobilien": {"registration": "21.68", "renewal": "21.68"},
".education": {"registration": "21.68", "renewal": "21.68"},
".discount": {"registration": "21.68", "renewal": "21.68"},
".gripe": {"registration": "21.68", "renewal": "21.68"},
".sarl": {"registration": "21.68", "renewal": "21.68"},
".haus": {"registration": "21.68", "renewal": "21.68"},
".moda": {"registration": "21.68", "renewal": "21.68"},
".cab": {"registration": "21.68", "renewal": "21.68"},
".yoga": {"registration": "22.18", "renewal": "22.18"},
".garden": {"registration": "22.18", "renewal": "22.18"},
".beer": {"registration": "22.18", "renewal": "22.18"},
".mobi": {"registration": "22.18", "renewal": "22.18"},
".wedding": {"registration": "22.18", "renewal": "22.18"},
".horse": {"registration": "22.18", "renewal": "22.18"},
".fishing": {"registration": "22.18", "renewal": "22.18"},
".compare": {"registration": "22.18", "renewal": "22.18"},
".broker": {"registration": "22.18", "renewal": "22.18"},
".select": {"registration": "22.18", "renewal": "22.18"},
".cooking": {"registration": "22.18", "renewal": "22.18"},
".fashion": {"registration": "22.18", "renewal": "22.18"},
".surf": {"registration": "22.18", "renewal": "22.18"},
".vodka": {"registration": "22.18", "renewal": "22.18"},
".fit": {"registration": "22.18", "renewal": "22.18"},
".cheap": {"registration": "23.18", "renewal": "23.18"},
".limited": {"registration": "23.18", "renewal": "23.18"},
".wtf": {"registration": "23.18", "renewal": "23.18"},
".auction": {"registration": "23.18", "renewal": "23.18"},
".contractors": {"registration": "23.18", "renewal": "23.18"},
".team": {"registration": "23.18", "renewal": "23.18"},
".kaufen": {"registration": "23.18", "renewal": "23.18"},
".cash": {"registration": "23.18", "renewal": "23.18"},
".singles": {"registration": "23.18", "renewal": "23.18"},
".democrat": {"registration": "23.18", "renewal": "23.18"},
".clothing": {"registration": "23.18", "renewal": "23.18"},
".tools": {"registration": "23.18", "renewal": "23.18"},
".forsale": {"registration": "23.18", "renewal": "23.18"},
".shopping": {"registration": "23.18", "renewal": "23.18"},
".boutique": {"registration": "23.18", "renewal": "23.18"},
".town": {"registration": "23.18", "renewal": "23.18"},
".florist": {"registration": "23.18", "renewal": "23.18"},
".gifts": {"registration": "23.18", "renewal": "23.18"},
".photography": {"registration": "23.18", "renewal": "23.18"},
".bargains": {"registration": "23.18", "renewal": "23.18"},
".family": {"registration": "23.18", "renewal": "23.18"},
".co": {"registration": "24", "renewal": "24"},
".life": {"registration": "24.18", "renewal": "24.18"},
".studio": {"registration": "24.18", "renewal": "24.18"},
".tv": {"registration": "25", "renewal": "25"},
".mba": {"registration": "25.18", "renewal": "25.18"},
".properties": {"registration": "25.18", "renewal": "25.18"},
".world": {"registration": "25.18", "renewal": "25.18"},
".pub": {"registration": "25.18", "renewal": "25.18"},
".rehab": {"registration": "25.18", "renewal": "25.18"},
".style": {"registration": "25.18", "renewal": "25.18"},
".training": {"registration": "25.18", "renewal": "25.18"},
".money": {"registration": "25.18", "renewal": "25.18"},
".productions": {"registration": "25.18", "renewal": "25.18"},
".sale": {"registration": "25.18", "renewal": "25.18"},
".rentals": {"registration": "25.18", "renewal": "25.18"},
".school": {"registration": "25.18", "renewal": "25.18"},
".vision": {"registration": "25.18", "renewal": "25.18"},
".rest": {"registration": "25.18", "renewal": "25.18"},
".services": {"registration": "25.18", "renewal": "25.18"},
".works": {"registration": "25.18", "renewal": "25.18"},
".plus": {"registration": "25.18", "renewal": "25.18"},
".online": {"registration": "25.18", "renewal": "25.18"},
".parts": {"registration": "25.18", "renewal": "25.18"},
".site": {"registration": "25.18", "renewal": "25.18"},
".social": {"registration": "25.18", "renewal": "25.18"},
".video": {"registration": "25.18", "renewal": "25.18"},
".vacations": {"registration": "25.18", "renewal": "25.18"},
".software": {"registration": "25.18", "renewal": "25.18"},
".repair": {"registration": "25.18", "renewal": "25.18"},
".republican": {"registration": "25.18", "renewal": "25.18"},
".academy": {"registration": "25.18", "renewal": "25.18"},
".zone": {"registration": "25.18", "renewal": "25.18"},
".builders": {"registration": "25.18", "renewal": "25.18"},
".fitness": {"registration": "25.18", "renewal": "25.18"},
".gmbh": {"registration": "25.18", "renewal": "25.18"},
".farm": {"registration": "25.18", "renewal": "25.18"},
".fail": {"registration": "25.18", "renewal": "25.18"},
".guide": {"registration": "25.18", "renewal": "25.18"},
".express": {"registration": "25.18", "renewal": "25.18"},
".exchange": {"registration": "25.18", "renewal": "25.18"},
".events": {"registration": "25.18", "renewal": "25.18"},
".estate": {"registration": "25.18", "renewal": "25.18"},
".enterprises": {"registration": "25.18", "renewal": "25.18"},
".engineer": {"registration": "25.18", "renewal": "25.18"},
".direct": {"registration": "25.18", "renewal": "25.18"},
".deals": {"registration": "25.18", "renewal": "25.18"},
".fun": {"registration": "25.18", "renewal": "25.18"},
".cool": {"registration": "25.18", "renewal": "25.18"},
".cards": {"registration": "25.18", "renewal": "25.18"},
".catering": {"registration": "25.18", "renewal": "25.18"},
".chat": {"registration": "25.18", "renewal": "25.18"},
".bike": {"registration": "25.18", "renewal": "25.18"},
".community": {"registration": "25.18", "renewal": "25.18"},
".computer": {"registration": "25.18", "renewal": "25.18"},
".coffee": {"registration": "25.18", "renewal": "25.18"},
".construction": {"registration": "25.18", "renewal": "25.18"},
".land": {"registration": "25.18", "renewal": "25.18"},
".associates": {"registration": "26.18", "renewal": "26.18"},
".guru": {"registration": "27.18", "renewal": "27.18"},
".care": {"registration": "27.18", "renewal": "27.18"},
".vet": {"registration": "27.18", "renewal": "27.18"},
".digital": {"registration": "27.18", "renewal": "27.18"},
".domains": {"registration": "28.18", "renewal": "28.18"},
".watch": {"registration": "28.18", "renewal": "28.18"},
".church": {"registration": "28.18", "renewal": "28.18"},
".marketing": {"registration": "28.18", "renewal": "28.18"},
".show": {"registration": "28.18", "renewal": "28.18"},
".fish": {"registration": "28.18", "renewal": "28.18"},
".cafe": {"registration": "28.18", "renewal": "28.18"},
".market": {"registration": "28.18", "renewal": "28.18"},
".industries": {"registration": "28.18", "renewal": "28.18"},
".house": {"registration": "28.18", "renewal": "28.18"},
".media": {"registration": "28.18", "renewal": "28.18"},
".actor": {"registration": "29.18", "renewal": "29.18"},
".consulting": {"registration": "30.18", "renewal": "30.18"},
".forex": {"registration": "30.18", "renewal": "30.18"},
".degree": {"registration": "32.18", "renewal": "32.18"},
".viajes": {"registration": "35.18", "renewal": "35.18"},
".memorial": {"registration": "35.68", "renewal": "35.68"},
".villas": {"registration": "35.68", "renewal": "35.68"},
".surgery": {"registration": "35.68", "renewal": "35.68"},
".plumbing": {"registration": "38.18", "renewal": "38.18"},
".bingo": {"registration": "38.18", "renewal": "38.18"},
".voyage": {"registration": "38.18", "renewal": "38.18"},
".diamonds": {"registration": "38.18", "renewal": "38.18"},
".maison": {"registration": "38.18", "renewal": "38.18"},
".wine": {"registration": "38.18", "renewal": "38.18"},
".cruises": {"registration": "38.18", "renewal": "38.18"},
".lease": {"registration": "38.18", "renewal": "38.18"},
".camp": {"registration": "38.18", "renewal": "38.18"},
".coupons": {"registration": "38.18", "renewal": "38.18"},
".hockey": {"registration": "38.18", "renewal": "38.18"},
".delivery": {"registration": "38.18", "renewal": "38.18"},
".condos": {"registration": "38.18", "renewal": "38.18"},
".flights": {"registration": "38.18", "renewal": "38.18"},
".limo": {"registration": "38.18", "renewal": "38.18"},
".financial": {"registration": "38.18", "renewal": "38.18"},
".ventures": {"registration": "38.18", "renewal": "38.18"},
".reviews": {"registration": "40.18", "renewal": "40.18"},
".attorney": {"registration": "40.18", "renewal": "40.18"},
".dentist": {"registration": "40.18", "renewal": "40.18"},
".design": {"registration": "40.18", "renewal": "40.18"},
".apartments": {"registration": "40.18", "renewal": "40.18"},
".camera": {"registration": "40.18", "renewal": "40.18"},
".lawyer": {"registration": "40.18", "renewal": "40.18"},
".university": {"registration": "40.18", "renewal": "40.18"},
".solar": {"registration": "40.18", "renewal": "40.18"},
".tech": {"registration": "40.18", "renewal": "40.18"},
".store": {"registration": "40.18", "renewal": "40.18"},
".mortgage": {"registration": "40.18", "renewal": "40.18"},
".theater": {"registration": "41.18", "renewal": "41.18"},
".kitchen": {"registration": "41.18", "renewal": "41.18"},
".dog": {"registration": "41.18", "renewal": "41.18"},
".insure": {"registration": "41.18", "renewal": "41.18"},
".glass": {"registration": "41.18", "renewal": "41.18"},
".finance": {"registration": "41.18", "renewal": "41.18"},
".vin": {"registration": "41.18", "renewal": "41.18"},
".toys": {"registration": "41.18", "renewal": "41.18"},
".restaurant": {"registration": "41.18", "renewal": "41.18"},
".shoes": {"registration": "41.18", "renewal": "41.18"},
".tours": {"registration": "41.18", "renewal": "41.18"},
".holiday": {"registration": "41.18", "renewal": "41.18"},
".hospital": {"registration": "41.18", "renewal": "41.18"},
".salon": {"registration": "41.18", "renewal": "41.18"},
".tienda": {"registration": "41.18", "renewal": "41.18"},
".cleaning": {"registration": "42.18", "renewal": "42.18"},
".clinic": {"registration": "42.18", "renewal": "42.18"},
".taxi": {"registration": "42.18", "renewal": "42.18"},
".coach": {"registration": "42.18", "renewal": "42.18"},
".codes": {"registration": "42.18", "renewal": "42.18"},
".fund": {"registration": "42.18", "renewal": "42.18"},
".expert": {"registration": "42.18", "renewal": "42.18"},
".jewelry": {"registration": "42.18", "renewal": "42.18"},
".golf": {"registration": "42.18", "renewal": "42.18"},
".dating": {"registration": "42.18", "renewal": "42.18"},
".holdings": {"registration": "42.18", "renewal": "42.18"},
".pizza": {"registration": "42.18", "renewal": "42.18"},
".recipes": {"registration": "42.18", "renewal": "42.18"},
".engineering": {"registration": "42.18", "renewal": "42.18"},
".black": {"registration": "42.68", "renewal": "42.68"},
".tennis": {"registration": "43.18", "renewal": "43.18"},
".lgbt": {"registration": "43.18", "renewal": "43.18"},
".io": {"registration": "45", "renewal": "45"},
".legal": {"registration": "45.18", "renewal": "45.18"},
".dental": {"registration": "45.18", "renewal": "45.18"},
".rent": {"registration": "45.18", "renewal": "45.18"},
".college": {"registration": "45.18", "renewal": "45.18"},
".partners": {"registration": "46.18", "renewal": "46.18"},
".careers": {"registration": "46.18", "renewal": "46.18"},
".tax": {"registration": "46.18", "renewal": "46.18"},
".capital": {"registration": "46.18", "renewal": "46.18"},
".claims": {"registration": "46.18", "renewal": "46.18"},
".healthcare": {"registration": "46.18", "renewal": "46.18"},
".press": {"registration": "49.18", "renewal": "49.18"},
".bar": {"registration": "50.18", "renewal": "50.18"},
".health": {"registration": "50.18", "renewal": "50.18"},
".fans": {"registration": "50.18", "renewal": "50.18"},
".green": {"registration": "52.68", "renewal": "52.68"},
".host": {"registration": "65.18", "renewal": "65.18"},
".reise": {"registration": "66.18", "renewal": "66.18"},
".ceo": {"registration": "70.18", "renewal": "70.18"},
".tires": {"registration": "70.18", "renewal": "70.18"},
".gold": {"registration": "75.18", "renewal": "75.18"},
".energy": {"registration": "75.18", "renewal": "75.18"},
".accountants": {"registration": "75.18", "renewal": "75.18"},
".loans": {"registration": "75.18", "renewal": "75.18"},
".credit": {"registration": "75.18", "renewal": "75.18"},
".investments": {"registration": "80.18", "renewal": "80.18"},
".doctor": {"registration": "80.18", "renewal": "80.18"},
".furniture": {"registration": "80.18", "renewal": "80.18"},
".fm": {"registration": "85", "renewal": "85"},
".casino": {"registration": "110.18", "renewal": "110.18"},
".creditcard": {"registration": "125.18", "renewal": "125.18"},
".movie": {"registration": "215.18", "renewal": "215.18"},
".realty": {"registration": "280.18", "renewal": "280.18"},
".new": {"registration": "400.18", "renewal": "400.18"},
".theatre": {"registration": "500.18", "renewal": "500.18"},
".storage": {"registration": "500.18", "renewal": "500.18"},
".security": {"registration": "2000.18", "renewal": "2000.18"},
}


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
    import re

    pattern = re.compile(
        r"document\.getElementById\('response_(.*?)'\)\.innerHTML\s*=\s*.*?>(Available|Unavailable)",
        re.IGNORECASE | re.DOTALL
    )
    matches = pattern.findall(html_content)

    domain_status = {}

    for raw_key, status in matches:
        domain = raw_key.strip()

        # 🧼 Step 1: Remove _mobile suffix
        domain = domain.replace("_mobile", "")

        # 🧼 Step 2: Remove any JS-style injection like ').style.color = ...
        domain = re.sub(r"\)\.style\.color.*", "", domain)
        domain = re.sub(r"document\.getElementById\(.*", "", domain)

        # 🧼 Step 3: Final cleanup
        domain = domain.replace("'", "").replace(";", "").strip()

        if domain:  # ensure non-empty
            domain_status[domain] = status.strip().capitalize()

    # 🎯 Final formatting with pricing if available
    results = []
    for domain, status in domain_status.items():
        tld = "." + domain.split('.')[-1].lower()
        item = {
            "domain": domain,
            "status": status
        }
        if tld in TLD_PRICES:
            item["price"] = {
                "registration": TLD_PRICES[tld]["registration"],
                "renewal": TLD_PRICES[tld]["renewal"]
            }
        results.append(item)

    return results

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
