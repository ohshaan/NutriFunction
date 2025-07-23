import streamlit as st
import pandas as pd
import numpy as np
import requests

API_KEY = "fZcCLgWhgSEoOuIGI5Fu6gw2GCM3XL5neF5wcnn0"

@st.cache_data
def load_lms():
    return pd.read_excel('bmi-boys-z-who-2007-exp.xlsx')

@st.cache_data
def load_rda():
    return pd.read_csv('usda_rda_table.csv')

lms_df = load_lms()
rda_df = load_rda()

MENU_DISHES = [
    "CREAM OF PUMPKIN SOUP", "Beef Stroganoff", "CHICKEN BARBEQUE", "WHITE RICE",
    "ROASTED GARLIC POTATO", "CHICKPEAS CURRY", "CHICKEN PRIMAVERA PASTA", "CHICKEN N' SWEETCORN SOUP",
    "CHICKEN CASSEROLE", "ROAST VEGETABLE", "DAL FRY", "CHICKEN PENNE ARRABIATTA",
    "FRENCH ONION SOUP", "BAKED MACARONI", "BUTTERED VEGETABLE", "PASTA WITH RED SAUCE WITH GRILLED CHICKEN",
    "PASTA WITH WHITE SAUCE WITH GRILLED CHICKEN", "CHICKEN MANCHOW SOUP", "GRILLED CHICKEN WITH PEPPER SAUCE",
    "FISH IN GOURMET SAUCE", "GRILLED VEGETABLE", "VEGETABLE AU GRATIN", "GRILLED BEEF IN MUSHROOM SAUCE",
    "CHICKEN AFRITADA", "HERB AND GARLIC POTATO", "CREAMY BAKED VEGETABLE", "CHICKEN ALFREDO PASTA",
    "HOT N' SOUR SOUP", "GRILLED CHICKEN WITH LEMON AND BUTTER", "CORN N' PEPPER RICE", "DAL MAHKNI",
    "SPAGHETTI BOLOGNESE", "MEXICAN BEANS SOUP", "BAKED BOLOGNESE RIGATONI", "POTATO WEDGES",
    "RED BEANS CURRY", "VEGETABLE SWEET CORN SOUP", "BEEF STEW", "FISH IN DILL CREAMY SAUCE",
    "STEAMED VEGETABLE", "THAI RED CURRY VEGETABLE", "CREAMY CHICKEN CARBONARA", "LENTIL SOUP",
    "BUTTER CHICKEN", "POTATO AND CARROT CURRY", "CHERRY TOMATO SAUCE PASTA", "CHICKEN FAJITA",
    "LAYONNAISE POTATO", "STIR FRY VEGETABLE", "BEEF VEGETABLE SOUP", "PASTA WITH WHITE SAUCE",
    "PASTA WITH RED SAUCE", "SPAGHETTI MIXED SAUCE WITH CHICKEN", "VEGETABLE JALFREZI",
    "ZUCCHINI BAKED CASSEROLE", "BAMIA CURRY", "CREAM OF POTATO SOUP", "BEEF WITH BROCCOLI",
    "GRILLED CHICKEN IN CAJUN SAUCE", "FISH IN LEMON BUTTER SAUCE", "ROASTED GARLIC POTATO",
    "VEGETABLE CURRY", "CREAMY BROCCOLI PASTA", "CHICKEN MONGOLIAN", "CARROT AND ONION RICE",
    "ROASTED VEGETABLES", "VEGETABLES CURRY"
]

USDA_RDA_MAP = {
    "Calorie Level Assessed": ["energy", "energy (kcal)", "calories"],
    "Protein": ["protein"],
    "Carbohydrate": ["carbohydrate, by difference"],
    "Dietary Fiber": ["fiber, total dietary", "dietary fiber"],
    "Total Fat": ["total lipid (fat)", "total fat"],
    "Saturated Fat": ["fatty acids, total saturated", "saturated fat"],
    "Linoleic Acid": ["pufa 18:2", "18:2 n-6", "linoleic acid"],
    "Linolenic Acid": ["pufa 18:3", "18:3 n-3", "linolenic acid"],
    "Calcium": ["calcium, ca"],
    "Iron": ["iron, fe"],
    "Magnesium": ["magnesium, mg"],
    "Phosphorus": ["phosphorus, p"],
    "Potassium": ["potassium, k"],
    "Sodium": ["sodium, na"],
    "Zinc": ["zinc, zn"],
    "Copper": ["copper, cu"],
    "Manganese": ["manganese, mn"],
    "Selenium": ["selenium, se"],
    "Vitamin A": ["vitamin a, rae", "retinol", "vitamin a"],
    "Vitamin E": ["vitamin e (alpha-tocopherol)", "vitamin e"],
    "Vitamin D": ["vitamin d (d2 + d3)", "vitamin d"],
    "Vitamin C": ["vitamin c, total ascorbic acid", "vitamin c"],
    "Thiamin": ["thiamin"],
    "Riboflavin": ["riboflavin"],
    "Niacin": ["niacin"],
    "Vitamin B-6": ["vitamin b-6"],
    "Vitamin B-12": ["vitamin b-12"],
    "Choline": ["choline, total"],
    "Vitamin K": ["vitamin k (phylloquinone)", "vitamin k"],
    "Folate": ["folate, total", "folic acid", "folate, food", "folate, dfe"]
}

MEAL_SPLITS = {'Breakfast': 0.25, 'Lunch': 0.35, 'Dinner': 0.35, 'Snack': 0.05}

# ---- Debug Collector ----
debug_logs = []

def search_usda_food(query):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"query": query, "api_key": API_KEY, "pageSize": 1}
    r = requests.get(url, params=params)
    debug_logs.append({
        "type": "search",
        "query": query,
        "status_code": r.status_code,
        "url": r.url,
        "response": r.json() if "application/json" in r.headers.get("Content-Type", "") else r.text
    })
    if r.status_code == 200 and r.json().get("foods"):
        return r.json()["foods"][0]
    return None

def get_usda_nutrients(fdc_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params)
    debug_logs.append({
        "type": "food_detail",
        "fdc_id": fdc_id,
        "status_code": r.status_code,
        "url": r.url,
        "response": r.json() if "application/json" in r.headers.get("Content-Type", "") else r.text
    })
    if r.status_code == 200:
        return r.json()
    return None

def extract_nutrients(food_json, rda_fields=USDA_RDA_MAP):
    nutrients = {}
    food_nutrients = food_json.get("foodNutrients", [])
    # Handle both new and legacy USDA schemas
    for field, name_variants in rda_fields.items():
        found = False
        for n in food_nutrients:
            if "nutrient" in n:
                n_name = n["nutrient"].get("name", "").strip().lower()
                n_val = n.get("amount")
                n_unit = n["nutrient"].get("unitName", "")
            else:
                n_name = n.get("nutrientName", "").strip().lower()
                n_val = n.get("value")
                n_unit = n.get("unitName", "")
            for variant in name_variants:
                if variant.lower() in n_name and n_val is not None:
                    nutrients[field] = (n_val, n_unit)
                    found = True
                    break
            if found:
                break
        if not found:
            nutrients[field] = (0.0, "")
    return nutrients

def get_lms_for_age(age_months):
    row = lms_df.loc[lms_df['Month'] == age_months]
    if row.empty:
        raise ValueError("No LMS data found for this age (in months).")
    return float(row['L'].iloc[0]), float(row['M'].iloc[0]), float(row['S'].iloc[0])

def get_rda_col(age_years, sex='M'):
    if age_years < 4:
        return '1-3_yrs'
    elif age_years < 9:
        return '4-8_yrs_M' if sex == 'M' else '4-8_yrs_F'
    elif age_years < 14:
        return '9-13_yrs_M' if sex == 'M' else '9-13_yrs_F'
    elif age_years < 19:
        return '14-18_yrs_M' if sex == 'M' else '14-18_yrs_F'
    elif age_years < 31:
        return '19-30_yrs_M' if sex == 'M' else '19-30_yrs_F'
    elif age_years < 51:
        return '31-50_yrs_M' if sex == 'M' else '31-50_yrs_F'
    else:
        return '51+_yrs_M' if sex == 'M' else '51+_yrs_F'

def get_user_rda(age_years, sex, meal_type):
    rda_col = get_rda_col(age_years, sex)
    user_rda = {}
    for idx, row in rda_df.iterrows():
        nutrient = row['Nutrient']
        value = row[rda_col]
        try:
            value = float(str(value).split('/')[0].split('-')[0])
            user_rda[nutrient] = value * MEAL_SPLITS[meal_type]
        except:
            continue
    return user_rda

def get_bmi_zscore(age_years, height_cm, weight_kg):
    age_months = int(round(age_years * 12))
    L, M, S = get_lms_for_age(age_months)
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if L == 0:
        z = np.log(bmi / M) / S
    else:
        z = ((bmi / M) ** L - 1) / (L * S)
    return bmi, z, M

# --- Categorize nutrients ---
MACRO_LIST = [
    "Calorie Level Assessed", "Protein", "Carbohydrate", "Total Fat", "Saturated Fat", "Dietary Fiber"
]
MICRO_LIST = [
    "Calcium", "Iron", "Magnesium", "Phosphorus", "Potassium", "Sodium", "Zinc", "Copper",
    "Manganese", "Selenium", "Vitamin A", "Vitamin D", "Vitamin E", "Vitamin K", "Vitamin C",
    "Thiamin", "Riboflavin", "Niacin", "Vitamin B-6", "Vitamin B-12", "Folate", "Choline"
]
MAIN_LIST = [
    "Linoleic Acid", "Linolenic Acid"
]

# ---- Streamlit Tabs ----
tab_main, tab_debug = st.tabs(["Meal Analysis", "Debug"])

with tab_main:
    st.title("Genio Lunch Analyzer POC")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age (years)", min_value=4.0, max_value=18.0, value=10.0, step=0.5)
        height = st.number_input("Height (cm)", min_value=80.0, max_value=220.0, value=140.0, step=0.5)
        weight = st.number_input("Weight (kg)", min_value=15.0, max_value=150.0, value=35.0, step=0.5)
    with col2:
        meal_type = st.selectbox("Meal", list(MEAL_SPLITS.keys()))
        dishes = st.multiselect("Select Dishes from Menu", options=MENU_DISHES, default=[MENU_DISHES[0]])

    if st.button("Analyze Meal"):
        bmi, z, median_bmi = get_bmi_zscore(age, height, weight)
        st.markdown(f"**Your BMI:** {bmi:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; **Median BMI for Age:** {median_bmi:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; **BMI Z-score:** {z:.2f}")
        if z > 1.5:
            st.warning("⚠️  Your BMI-for-age is > 1.5 SD above the median. Please consult a healthcare provider.")
        elif z < -1.5:
            st.warning("⚠️  Your BMI-for-age is > 1.5 SD below the median. Please consult a healthcare provider.")
        else:
            st.info("Your BMI-for-age is within the healthy range (±1.5 SD).")

        user_rda = get_user_rda(age, 'M', meal_type)
        total_nutrients = {k: 0.0 for k in user_rda}

        for dish in dishes:
            usda_match = search_usda_food(dish)
            if usda_match:
                desc = usda_match.get('description', dish)
                fdc_id = usda_match['fdcId']
                food_data = get_usda_nutrients(fdc_id)
                food_nutrients = extract_nutrients(food_data)
                for nutr in user_rda:
                    val = food_nutrients.get(nutr, (0.0, ""))[0]
                    total_nutrients[nutr] += val if val is not None else 0.0
            else:
                st.error(f"No USDA match found for {dish}")

        comp_table = []
        for nutr in user_rda:
            intake = total_nutrients.get(nutr, 0)
            rda = user_rda[nutr]
            percent = (intake / rda * 100) if rda else 0
            comp_table.append({
                "Nutrient": nutr,
                "RDA (Meal)": f"{rda:.1f}",
                "Intake": f"{intake:.1f}",
                "% of RDA Met": f"{percent:.1f}%"
            })

        # --- Progress bars with categories ---
        def show_progress_section(title, filter_list):
            with st.expander(title, expanded=True):
                for row in comp_table:
                    if row["Nutrient"] not in filter_list:
                        continue
                    percent = float(row["% of RDA Met"].replace('%', ''))
                    bar_val = min(percent / 100, 1.0)  # max out at 100%
                    color = "#4caf50" if percent >= 100 else "#2196f3"
                    st.markdown(
                        f"**{row['Nutrient']}**: {row['Intake']}/{row['RDA (Meal)']} "
                        f"({percent:.1f}%)"
                    )
                    st.markdown(
                        f"""
                        <div style="background: #e0e0e0; border-radius: 5px; height: 18px; width: 100%;">
                          <div style="background: {color}; width: {bar_val*100:.1f}%; height: 18px; border-radius: 5px;"></div>
                        </div>
                        """, unsafe_allow_html=True
                    )

        st.subheader("Meal Nutrient Coverage")
        show_progress_section("Macro Nutrients", MACRO_LIST)
        show_progress_section("Micro Nutrients", MICRO_LIST)
        show_progress_section("Main Fatty Acids & Others", MAIN_LIST)

    st.caption("POC: All values are approximate. For clinical advice, consult a professional.")

with tab_debug:
    st.header("Debug Output")
    for log in debug_logs:
        st.write(f"---\nRequest Type: {log['type']}")
        st.write(f"Query/ID: {log.get('query', log.get('fdc_id', ''))}")
        st.write(f"Status Code: {log['status_code']}")
        st.write(f"URL: {log['url']}")
        if isinstance(log["response"], dict):
            st.json(log["response"])
        else:
            st.write(log["response"])
