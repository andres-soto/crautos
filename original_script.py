import requests
from bs4 import BeautifulSoup
import re
import statistics
import math
import argparse

# --- CONFIGURATION ---
URL = 'https://crautos.com/autosusados/searchresults.cfm'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://crautos.com',
    'referer': 'https://crautos.com/autosusados/index.cfm/',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
}

# Brand ID to Name mapping (from the actual HTML select element)
BRAND_MAP = {
    '20': 'Acura', '124': 'Aion', '1': 'Alfa Romeo', '68': 'AMC', '2': 'Aro', '3': 'Asia',
    '56': 'Aston Martin', '4': 'Audi', '59': 'Austin', '117': 'BAIC', '109': 'Baw',
    '58': 'Bentley', '60': 'Bluebird', '5': 'BMW', '112': 'Brilliance', '61': 'Buick',
    '97': 'BYD', '62': 'Cadillac', '107': 'Chana', '108': 'Changan', '88': 'Chery',
    '6': 'Chevrolet', '7': 'Chrysler', '46': 'Citroen', '118': 'CMC', '8': 'Dacia',
    '9': 'Daewoo', '10': 'Daihatsu', '63': 'Datsun', '11': 'Dodge/RAM', '64': 'Donfeng (ZNA)',
    '65': 'Eagle', '106': 'Faw', '66': 'Ferrari', '12': 'Fiat', '13': 'Ford', '99': 'Foton',
    '67': 'Freightliner', '55': 'Geely', '57': 'Genesis', '39': 'Geo', '14': 'GMC',
    '54': 'Gonow', '49': 'Great Wall', '70': 'Hafei', '111': 'Haima', '121': 'Haval',
    '134': 'Haycan', '102': 'Heibao', '98': 'Higer', '71': 'Hino', '15': 'Honda',
    '72': 'Hummer', '16': 'Hyundai', '73': 'Infiniti', '40': 'International', '17': 'Isuzu',
    '74': 'Iveco', '75': 'JAC', '130': 'Jaecoo', '41': 'Jaguar', '18': 'Jeep', '125': 'Jetour',
    '76': 'Jinbei', '77': 'JMC', '113': 'Jonway', '131': 'Kaiyi', '101': 'Kenworth', '19': 'Kia',
    '42': 'Lada', '78': 'Lamborghini', '43': 'Lancia', '21': 'Land Rover', '22': 'Lexus',
    '69': 'Lifan', '83': 'Lincoln', '79': 'Lotus', '80': 'Mack', '82': 'Magiruz', '81': 'Mahindra',
    '120': 'Marcopolo', '84': 'Maserati', '116': 'Maxus', '23': 'Mazda', '24': 'Mercedes Benz',
    '85': 'Mercury', '86': 'MG', '51': 'Mini', '25': 'Mitsubishi', '133': 'Neta', '26': 'Nissan',
    '87': 'Oldsmobile', '129': 'Omoda', '50': 'Opel', '104': 'Peterbilt', '27': 'Peugeot',
    '123': 'Piaggio', '89': 'Plymouth', '100': 'Polarsun', '28': 'Pontiac', '29': 'Porsche',
    '48': 'Proton', '90': 'Rambler', '30': 'Renault', '105': 'Reva', '126': 'Rivian',
    '91': 'Rolls Royce', '31': 'Rover', '44': 'Saab', '38': 'Samsung', '92': 'Saturn',
    '93': 'Scania', '94': 'Scion', '47': 'Seat', '127': 'Shineray', '53': 'Skoda', '52': 'Smart',
    '114': 'Soueast', '32': 'Ssang Yong', '33': 'Subaru', '34': 'Suzuki', '115': 'Tesla',
    '95': 'Tianma', '96': 'Tiger Truck', '35': 'Toyota', '128': 'VGV', '36': 'Volkswagen',
    '37': 'Volvo', '103': 'Western Star', '135': 'Xiaomi', '122': 'Xpeng', '45': 'Yugo',
    '119': 'Zap', '132': 'Zeekr', '110': 'Zotye'
}

# Transmission Mapping
TRANS_MAP = {
    '1': 'Manual',
    '2': 'Automatic'
}

# Fuel Mapping
FUEL_MAP = {
    '1': 'Gasoline',
    '2': 'Diesel',
    '3': 'Hybrid',
    '4': 'Electric'
}

# Province Mapping
PROVINCE_MAP = {
    '1': 'Alajuela',
    '2': 'Cartago',
    '3': 'Guanacaste',
    '4': 'Heredia',
    '5': 'Limón',
    '6': 'Puntarenas',
    '7': 'San José'
}

# Body Style Mapping
STYLE_MAP = {
    '02': 'Sedan',
    '03': 'Station Wagon',
    '20': 'Hatchback',
    '04': 'Pick Up 2WD',
    '05': 'Pick Up 4WD',
    '06': 'Panel',
    '07': 'Minibus/Minivan',
    '08': 'SUV 2WD',
    '09': 'SUV 4WD/AWD',
    '15': 'RV',
    '10': 'Commercial 1.0-3.5 Ton',
    '11': 'Commercial 4.0-4.5 Ton',
    '12': 'Commercial 5.0-7.5 Ton',
    '13': 'Commercial 8.0-9.5 Ton',
    '14': 'Commercial 10.0+ Ton'
}

# Reverse mapping: Brand name to ID (case-insensitive)
BRAND_NAME_TO_ID = {v.lower(): k for k, v in BRAND_MAP.items()}

def resolve_brand(brand_input):
    """Resolves brand name to ID. Returns the ID as string."""
    if not brand_input:
        return None
    
    brand_input = brand_input.strip()
    
    # If it's already a number, return it as string
    if brand_input.isdigit():
        return brand_input
    
    # Try to find by brand name (case-insensitive)
    brand_lower = brand_input.lower()
    if brand_lower in BRAND_NAME_TO_ID:
        return BRAND_NAME_TO_ID[brand_lower]
    
    # Try partial match
    for name, brand_id in BRAND_NAME_TO_ID.items():
        if brand_lower in name or name in brand_lower:
            return brand_id
    
    return None

def suggest_brands(brand_input, max_suggestions=5):
    """Suggests similar brand names if exact match not found."""
    if not brand_input or brand_input.isdigit():
        return []
    
    brand_lower = brand_input.lower()
    suggestions = []
    
    # Find brands that contain the input or are contained in it
    for name, brand_id in BRAND_NAME_TO_ID.items():
        if brand_lower in name or name.startswith(brand_lower):
            suggestions.append((name, brand_id))
            if len(suggestions) >= max_suggestions:
                break
    
    return suggestions

def get_parameter_interactive(param_name, prompt, default='0', param_type='str'):
    """Gets a parameter interactively. Returns default if empty or on EOF."""
    try:
        value = input(f"{prompt} (default: {default}): ").strip()
        if not value:
            return default
        if param_type == 'int':
            try:
                return str(int(value))
            except ValueError:
                print(f"   Invalid number, using default: {default}")
                return default
        return value
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive environments or user interruption
        print(f"   Using default: {default}")
        return default

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Search for used cars on CRAutos and calculate price statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--brand', type=str, help='Brand ID or name (e.g., 16, Toyota, Hyundai)')
    parser.add_argument('--modelstr', type=str, help='Model name (e.g., ELANTRA, HILUX)')
    parser.add_argument('--yearfrom', type=str, help='Year from (e.g., 2012)')
    parser.add_argument('--yearto', type=str, help='Year to (e.g., 2012)')
    parser.add_argument('--pricefrom', type=str, help='Price from in colones (e.g., 100000)')
    parser.add_argument('--priceto', type=str, help='Price to in colones (e.g., 800000000)')
    parser.add_argument('--trans', type=str, help='Transmission (0=Any, 1=Manual, 2=Automatic)')
    parser.add_argument('--fuel', type=str, help='Fuel type (0=Any, 1=Gasoline, 2=Diesel, etc.)')
    parser.add_argument('--style', type=str, help='Body style (00=Any)')
    parser.add_argument('--province', type=str, help='Province (0=Any)')
    parser.add_argument('--recibe', type=str, help='Accepts trade-in (0=Any, 1=Yes)')
    parser.add_argument('--orderby', type=str, help='Sort order (0=Default)')
    
    return parser.parse_args()

def collect_search_parameters(args):
    """Collects search parameters from args or interactively."""
    params = {}
    
    print("\n" + "="*50)
    print("CRAutos Search Parameters")
    print("="*50)
    
    # Brand
    if args.brand:
        brand_id = resolve_brand(args.brand)
        if brand_id:
            params['brand'] = brand_id
            brand_name = BRAND_MAP.get(brand_id, f"Brand {brand_id}")
            print(f"✓ Brand: {brand_name} (ID: {brand_id})")
        else:
            print(f"⚠ Warning: Brand '{args.brand}' not found, will ask interactively")
            suggestions = suggest_brands(args.brand)
            if suggestions:
                print(f"   Did you mean: {', '.join([BRAND_MAP.get(sid, name) for name, sid in suggestions[:3]])}?")
            brand_input = get_parameter_interactive('brand', 'Brand (name or ID, e.g., Toyota, Hyundai, 16)', '0')
            brand_id = resolve_brand(brand_input)
            if brand_id and brand_id != '0':
                brand_name = BRAND_MAP.get(brand_id, f"Brand {brand_id}")
                print(f"   → Found: {brand_name} (ID: {brand_id})")
                params['brand'] = brand_id
            else:
                if brand_input and brand_input != '0':
                    suggestions = suggest_brands(brand_input)
                    if suggestions:
                        print(f"   Did you mean: {', '.join([BRAND_MAP.get(sid, name) for name, sid in suggestions[:3]])}?")
                    print(f"   ⚠ Brand '{brand_input}' not found. Using default (Any brand).")
                params['brand'] = '0'
    else:
        brand_input = get_parameter_interactive('brand', 'Brand (name or ID, e.g., Toyota, Hyundai, 16)', '0')
        brand_id = resolve_brand(brand_input)
        if brand_id and brand_id != '0':
            brand_name = BRAND_MAP.get(brand_id, f"Brand {brand_id}")
            print(f"   → Found: {brand_name} (ID: {brand_id})")
            params['brand'] = brand_id
        else:
            if brand_input and brand_input != '0':
                suggestions = suggest_brands(brand_input)
                if suggestions:
                    print(f"   Did you mean: {', '.join([BRAND_MAP.get(sid, name) for name, sid in suggestions[:3]])}?")
                print(f"   ⚠ Brand '{brand_input}' not found. Using default (Any brand).")
            params['brand'] = '0'
    
    # Model
    if args.modelstr:
        params['modelstr'] = args.modelstr  # Keep original case
        print(f"✓ Model: {params['modelstr']}")
    else:
        params['modelstr'] = get_parameter_interactive('modelstr', 'Model name', '')  # Keep original case
    
    # Year from
    if args.yearfrom:
        params['yearfrom'] = args.yearfrom
        print(f"✓ Year from: {params['yearfrom']}")
    else:
        params['yearfrom'] = get_parameter_interactive('yearfrom', 'Year from', '0', 'int')
    
    # Year to
    if args.yearto:
        params['yearto'] = args.yearto
        print(f"✓ Year to: {params['yearto']}")
    else:
        params['yearto'] = get_parameter_interactive('yearto', 'Year to', '0', 'int')
    
    # Transmission
    if args.trans:
        params['trans'] = args.trans
        print(f"✓ Transmission: {params['trans']}")
    else:
        params['trans'] = get_parameter_interactive('trans', 'Transmission (0=Any, 1=Manual, 2=Automatic)', '0', 'int')
    
    # Fuel
    if args.fuel:
        params['fuel'] = args.fuel
        print(f"✓ Fuel: {params['fuel']}")
    else:
        params['fuel'] = get_parameter_interactive('fuel', 'Fuel type (0=Any, 1=Gasoline, 2=Diesel)', '0', 'int')
    
    # Price from (set default, not asked interactively)
    if args.pricefrom:
        params['pricefrom'] = args.pricefrom
        print(f"✓ Price from: ¢ {int(params['pricefrom']):,}")
    else:
        params['pricefrom'] = '100000'  # Default: 100,000 colones
    
    # Price to (set default, not asked interactively)
    if args.priceto:
        params['priceto'] = args.priceto
        print(f"✓ Price to: ¢ {int(params['priceto']):,}")
    else:
        params['priceto'] = '800000000'  # Default: 800,000,000 colones
    
    # Style (set default, not asked interactively)
    if args.style:
        params['style'] = args.style
        print(f"✓ Style: {params['style']}")
    else:
        params['style'] = '00'  # Default: Any
    
    # Province (set default, not asked interactively)
    if args.province:
        params['province'] = args.province
        print(f"✓ Province: {params['province']}")
    else:
        params['province'] = '0'  # Default: Any
    
    # Recibe (trade-in) (set default, not asked interactively)
    if args.recibe:
        params['recibe'] = args.recibe
        print(f"✓ Accepts trade-in: {params['recibe']}")
    else:
        params['recibe'] = '0'  # Default: Any
    
    # Order by (set default, not asked interactively)
    if args.orderby:
        params['orderby'] = args.orderby
        print(f"✓ Sort order: {params['orderby']}")
    else:
        params['orderby'] = '0'  # Default
    
    print("="*50 + "\n")
    
    return params

def build_payload(params):
    """Builds the complete payload dictionary with all required fields."""
    payload = {
        'brand': params.get('brand', '0'),
        'modelstr': params.get('modelstr', ''),
        'style': params.get('style', '00'),
        'fuel': params.get('fuel', '0'),
        'trans': params.get('trans', '0'),
        'financed': '00',  # Fixed value
        'recibe': params.get('recibe', '0'),
        'province': params.get('province', '0'),
        'doors': '0',  # Fixed value
        'yearfrom': params.get('yearfrom', '0'),
        'yearto': params.get('yearto', '0'),
        'pricefrom': params.get('pricefrom', '100000'),
        'priceto': params.get('priceto', '800000000'),
        'orderby': params.get('orderby', '0'),
        'newused': '1',  # Fixed value (1 = used cars)
        'lformat': '0',  # Fixed value
        'l': '1'  # Fixed value
    }
    return payload

def get_page_data(page_number, payload, session=None):
    """Fetches a single page and returns the HTML soup."""
    if session is None:
        session = requests.Session()
    
    # Query parameters: p for page number, c for category (from working curl)
    params = {'p': page_number, 'c': '01160'}
    
    # Use POST as shown in the working curl command
    response = session.post(URL, headers=HEADERS, data=payload, params=params, allow_redirects=True)
    
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    
    # If POST fails, report error
    print(f"   Warning: Status code {response.status_code} for page {page_number}")
    return None

def parse_currency_text(text):
    """
    Parses a price string to extract the value and currency.
    Returns (value, currency_symbol) where value is int and currency_symbol is '$' or '¢'.
    """
    if not text:
        return None, None

    # Clean value
    clean_val = re.sub(r'[^\d]', '', text)
    if not clean_val:
        return None, None

    value = int(clean_val)

    # Determine currency
    if '$' in text:
        return value, '$'
    elif '¢' in text:
        return value, '¢'
    else:
        # If no symbol found, return None for currency
        return value, None

def extract_prices(soup):
    """
    Extracts both Colones and Dollar prices from the page.
    Returns a list of tuples: (colones_value, usd_value)
    Both values can be None if not found.
    """
    # Only extract prices from the main search results form, not from featured/related cars
    main_form = soup.find('form', {'name': 'form', 'action': re.compile(r'ucompare\.cfm')})
    
    if not main_form:
        # Fallback: try to find the main results section
        main_section = soup.find('section', class_='sptb')
        if main_section:
            forms = main_section.find_all('form')
            for form in forms:
                if form.get('action', '').endswith('ucompare.cfm'):
                    main_form = form
                    break
    
    page_prices = []

    if not main_form:
        # Fallback to finding price tags directly if form not found
        # Iterate over .precio tags and find sibling .preciodolares
        price_tags = soup.find_all('span', class_=re.compile(r'precio(-sm)?$'))
        seen_tags = set()

        for tag in price_tags:
            if tag in seen_tags:
                continue
            seen_tags.add(tag)

            # Find sibling or parent container logic
            parent = tag.parent
            dolar_tag = parent.find('span', class_=re.compile(r'preciodolares(-sm)?$'))
            if not dolar_tag and parent.parent:
                dolar_tag = parent.parent.find('span', class_=re.compile(r'preciodolares(-sm)?$'))

            p_val, p_curr = parse_currency_text(tag.get_text())
            d_val, d_curr = parse_currency_text(dolar_tag.get_text()) if dolar_tag else (None, None)

            colones = None
            usd = None

            # Assign based on currency
            if p_curr == '¢': colones = p_val
            elif p_curr == '$': usd = p_val

            if d_curr == '¢': colones = d_val
            elif d_curr == '$': usd = d_val

            # If no symbols, heuristics (unlikely needed based on observation)
            if colones is None and usd is None:
                if p_val is not None: colones = p_val # Default to colones

            if colones is not None or usd is not None:
                page_prices.append((colones, usd))

        return page_prices
    
    # Extract prices using checkboxes (actual search results)
    seen_car_ids = set()
    checkboxes = main_form.find_all('input', {'type': 'checkbox', 'name': 'c'})
    
    for checkbox in checkboxes:
        car_id = checkbox.get('value')
        if not car_id or car_id in seen_car_ids:
            continue
        seen_car_ids.add(car_id)
        
        parent = checkbox.find_parent(['div', 'td', 'tr', 'table'])
        if parent:
            price_tag = parent.find('span', class_=re.compile(r'precio(-sm)?$'))
            dolar_tag = parent.find('span', class_=re.compile(r'preciodolares(-sm)?$'))

            if not price_tag:
                continue

            p_val, p_curr = parse_currency_text(price_tag.get_text())
            d_val, d_curr = parse_currency_text(dolar_tag.get_text()) if dolar_tag else (None, None)

            colones = None
            usd = None

            # Assign based on currency symbol
            if p_curr == '¢': colones = p_val
            elif p_curr == '$': usd = p_val

            if d_curr == '¢': colones = d_val
            elif d_curr == '$': usd = d_val

            # Fallback if no symbol found (assume colones if nothing else)
            if colones is None and usd is None:
                if p_val is not None and p_curr is None:
                    colones = p_val

            if colones is not None or usd is not None:
                page_prices.append((colones, usd))

    # Fallback if no checkboxes found
    if not page_prices:
        price_tags = main_form.find_all('span', class_=re.compile(r'precio(-sm)?$'))
        seen_vals = set()

        for tag in price_tags:
            parent = tag.parent
            dolar_tag = parent.find('span', class_=re.compile(r'preciodolares(-sm)?$'))

            p_val, p_curr = parse_currency_text(tag.get_text())
            d_val, d_curr = parse_currency_text(dolar_tag.get_text()) if dolar_tag else (None, None)

            colones = None
            usd = None

            if p_curr == '¢': colones = p_val
            elif p_curr == '$': usd = p_val

            if d_curr == '¢': colones = d_val
            elif d_curr == '$': usd = d_val

            # Fallback if no symbol found (assume colones if nothing else)
            if colones is None and usd is None:
                if p_val is not None and p_curr is None:
                    colones = p_val

            pair = (colones, usd)
            if pair not in seen_vals and (colones is not None or usd is not None):
                page_prices.append(pair)
                seen_vals.add(pair)
    
    return page_prices

def format_search_description(params):
    """Creates a human-readable description of the search parameters."""
    parts = []
    
    brand_id = params.get('brand', '0')
    if brand_id != '0':
        brand_name = BRAND_MAP.get(brand_id, f"Brand {brand_id}")
        parts.append(brand_name)
    
    model = params.get('modelstr', '').strip()
    if model:
        parts.append(model)
    
    year_from = params.get('yearfrom', '0')
    year_to = params.get('yearto', '0')
    if year_from != '0' or year_to != '0':
        if year_from == year_to and year_from != '0':
            parts.append(year_from)
        elif year_from != '0' and year_to != '0':
            parts.append(f"{year_from}-{year_to}")
        elif year_from != '0':
            parts.append(f"{year_from}+")
        elif year_to != '0':
            parts.append(f"up to {year_to}")

    # Transmission
    trans = params.get('trans', '0')
    if trans != '0':
        trans_name = TRANS_MAP.get(trans, trans)
        parts.append(f"[{trans_name}]")

    # Fuel
    fuel = params.get('fuel', '0')
    if fuel != '0':
        fuel_name = FUEL_MAP.get(fuel, fuel)
        parts.append(f"[{fuel_name}]")

    # Style
    style = params.get('style', '00')
    if style != '00':
        style_name = STYLE_MAP.get(style, f"Style {style}")
        parts.append(f"[{style_name}]")

    # Province
    province = params.get('province', '0')
    if province != '0':
        prov_name = PROVINCE_MAP.get(province, province)
        parts.append(f"in {prov_name}")

    # Trade-in
    recibe = params.get('recibe', '0')
    if recibe == '1':
        parts.append("(Accepts Trade-in)")
    
    return " ".join(parts) if parts else "All vehicles"

def main():
    # Parse command-line arguments
    args = parse_arguments()
    
    # Collect search parameters
    params = collect_search_parameters(args)
    
    # Build payload
    payload = build_payload(params)
    
    print("🚀 Connecting to CRAutos...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, visit the index page to establish a session
    index_url = 'https://crautos.com/autosusados/index.cfm'
    try:
        session.get(index_url, headers=HEADERS)
    except Exception as e:
        print(f"   Warning: Could not visit index page: {e}")
    
    # 1. Get the first page to see how many total results there are
    first_page_soup = get_page_data(1, payload, session)
    if not first_page_soup:
        print("❌ Error: Could not access the website.")
        return

    # Find total ads (usually inside Form1 hidden input 'totalads')
    total_ads_input = first_page_soup.find('input', {'name': 'totalads'})
    if total_ads_input:
        total_ads = int(total_ads_input.get('value', 0))
    else:
        # Fallback to header text parsing (using 'string' instead of deprecated 'text')
        header = first_page_soup.find('h5', string=re.compile(r'de \d+'))
        if not header:
            # Try finding by text content
            headers = first_page_soup.find_all('h5')
            for h in headers:
                if re.search(r'de \d+', h.get_text()):
                    header = h
                    break
        total_ads = int(re.search(r'de (\d+)', header.get_text()).group(1)) if header else 0

    if total_ads == 0:
        print("Empty search results.")
        return

    # CRAutos shows 15 results per page
    total_pages = math.ceil(total_ads / 15)
    print(f"📊 Found {total_ads} vehicles across {total_pages} page(s).")

    all_prices = []
    
    # 2. Loop through all pages
    for p in range(1, total_pages + 1):
        print(f"   Reading page {p}...")
        soup = get_page_data(p, payload, session) if p > 1 else first_page_soup
        all_prices.extend(extract_prices(soup))

    # 3. Final Calculation
    if not all_prices:
        print("Could not find any prices to calculate.")
        return

    colones_prices = [p[0] for p in all_prices if p[0] is not None]
    usd_prices = [p[1] for p in all_prices if p[1] is not None]

    search_desc = format_search_description(params)
    
    print("\n" + "="*50)
    print(f"RESULTS FOR: {search_desc}")
    print(f"Total processed: {len(all_prices)} cars")
    print("-" * 50)

    if colones_prices:
        min_c = min(colones_prices)
        max_c = max(colones_prices)
        avg_c = int(statistics.mean(colones_prices))
        print(f"Colones: Min ¢ {min_c:,} | Max ¢ {max_c:,} | Avg ¢ {avg_c:,}")
    else:
        print("Colones: No prices found.")

    if usd_prices:
        min_u = min(usd_prices)
        max_u = max(usd_prices)
        avg_u = int(statistics.mean(usd_prices))
        print(f"Dollars: Min $ {min_u:,.0f} | Max $ {max_u:,.0f} | Avg $ {avg_u:,.0f}")
    else:
         print("Dollars: No prices found.")

    print("="*50)

if __name__ == "__main__":
    main()
