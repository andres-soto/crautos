import streamlit as st
import statistics
import math
import requests
from crautos_stats import (
    BRAND_MAP,
    BRAND_NAME_TO_ID,
    TRANS_MAP,
    FUEL_MAP,
    build_payload,
    get_page_data,
    extract_prices,
    HEADERS
)

def main():
    # Set page title and layout
    st.set_page_config(page_title="Buscador de Precios CR", layout="centered")

    st.title('🔎 Buscador de Precios CR')

    # ------------------
    # INPUTS
    # ------------------

    # Brand: Selectbox with sorted brand names
    # BRAND_MAP values are names like 'Toyota', 'Honda'
    # Sort them alphabetically
    brand_names = sorted(list(BRAND_MAP.values()), key=str.lower)
    selected_brand_name = st.selectbox("Marca", brand_names)

    # Model: Text input
    model_str = st.text_input('Modelo', placeholder='Ej. Hilux, Elantra, Rav4')

    # Year: Select slider
    # Range from 1980 to next year
    year_options = list(range(1980, 2027))
    # Default range e.g. 2010-2020
    year_range = st.select_slider(
        'Año',
        options=year_options,
        value=(2010, 2020)
    )
    year_from, year_to = year_range

    # Transmission: Radio
    # Map friendly names to IDs. 0=Any, 1=Manual, 2=Automatic
    trans_options = ["Cualquiera", "Manual", "Automática"]
    trans_selection = st.radio('Transmisión', options=trans_options, horizontal=True)

    trans_map_reverse = {
        "Cualquiera": '0',
        "Manual": '1',
        "Automática": '2'
    }
    trans_val = trans_map_reverse[trans_selection]

    # Fuel: Radio
    # Map friendly names to IDs. 0=Any, 1=Gasoline, 2=Diesel, 3=Hybrid, 4=Electric
    # FUEL_MAP: {'1': 'Gasoline', '2': 'Diesel', '3': 'Hybrid', '4': 'Electric'}
    fuel_options = ["Cualquiera", "Gasolina", "Diesel", "Híbrido", "Eléctrico"]
    fuel_selection = st.radio('Combustible', options=fuel_options, horizontal=True)

    fuel_map_reverse = {
        "Cualquiera": '0',
        "Gasolina": '1',
        "Diesel": '2',
        "Híbrido": '3',
        "Eléctrico": '4'
    }
    fuel_val = fuel_map_reverse[fuel_selection]

    # ------------------
    # ACTION
    # ------------------

    if st.button('CALCULAR PRECIOS', use_container_width=True):

        # Resolve Brand ID
        # BRAND_NAME_TO_ID has keys in lowercase
        brand_id = BRAND_NAME_TO_ID.get(selected_brand_name.lower())

        if not brand_id:
            st.error(f"Error resolving brand ID for {selected_brand_name}")
            return

        # Prepare Params
        params = {
            'brand': brand_id,
            'modelstr': model_str,
            'yearfrom': str(year_from),
            'yearto': str(year_to),
            'trans': trans_val,
            'fuel': fuel_val,
            # Defaults for others
            'pricefrom': '100000',
            'priceto': '800000000',
            'style': '00',
            'province': '0',
            'recibe': '0',
            'orderby': '0'
        }

        # Build Payload
        payload = build_payload(params)

        # Perform Scraping
        with st.spinner('Buscando en crautos...'):
            session = requests.Session()
            # Visit index to set cookies (though helper might not require it if headers are good, but good practice)
            try:
                session.get('https://crautos.com/autosusados/index.cfm', headers=HEADERS)
            except Exception as e:
                pass # Continue even if index fails, maybe search works

            # 1. Get first page
            first_page_soup = get_page_data(1, payload, session)

            if not first_page_soup:
                st.error("No se pudo conectar a crautos.com")
                return

            # Find total ads
            # Replicating logic from crautos_stats.py
            total_ads = 0
            total_ads_input = first_page_soup.find('input', {'name': 'totalads'})
            if total_ads_input:
                try:
                    total_ads = int(total_ads_input.get('value', 0))
                except:
                    total_ads = 0
            else:
                 # Fallback regex
                 import re
                 header = first_page_soup.find('h5', string=re.compile(r'de \d+'))
                 if not header:
                    headers = first_page_soup.find_all('h5')
                    for h in headers:
                        if re.search(r'de \d+', h.get_text()):
                            header = h
                            break
                 if header:
                     m = re.search(r'de (\d+)', header.get_text())
                     if m:
                         total_ads = int(m.group(1))

            if total_ads == 0:
                st.warning("No se encontraron resultados con estos criterios.")
                return

            st.success(f"Encontrados {total_ads} vehículos.")

            total_pages = math.ceil(total_ads / 15)

            all_prices = []

            # Progress bar if many pages
            progress_bar = st.progress(0)

            # 2. Loop through pages
            for p in range(1, total_pages + 1):
                # Update progress
                progress_bar.progress(p / total_pages)

                if p == 1:
                    soup = first_page_soup
                else:
                    soup = get_page_data(p, payload, session)

                if soup:
                    prices = extract_prices(soup)
                    all_prices.extend(prices)

            progress_bar.empty()

            if not all_prices:
                st.warning("No se pudieron extraer precios de los resultados.")
                return

            # 3. Calculate Stats
            min_price = min(all_prices)
            max_price = max(all_prices)
            avg_price = int(statistics.mean(all_prices))

            # Display Results
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Precio Mínimo", f"¢ {min_price:,}")
            with col2:
                st.metric("Promedio", f"¢ {avg_price:,}")
            with col3:
                st.metric("Precio Máximo", f"¢ {max_price:,}")

if __name__ == "__main__":
    main()
