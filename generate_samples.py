import os
import pandas as pd
import numpy as np

os.makedirs("sample_data", exist_ok=True)
np.random.seed(42)

# ==========================================
# 1. E-Commerce Orders Dataset
# ==========================================
n1 = 250
dates1 = pd.date_range("2023-01-01", "2023-12-31", periods=n1).strftime("%Y-%m-%d")
categories = ["Technology", "Office Supplies", "Furniture"]
subcats = {
    "Technology": ["Phones", "Laptops", "Accessories"],
    "Office Supplies": ["Paper", "Binders", "Storage"],
    "Furniture": ["Chairs", "Tables", "Bookcases"]
}
regions = ["East", "West", "Central", "South"]
segments = ["Consumer", "Corporate", "Home Office"]

chosen_cat = np.random.choice(categories, n1)
chosen_subcat = [np.random.choice(subcats[c]) for c in chosen_cat]
chosen_region = np.random.choice(regions, n1)
chosen_segment = np.random.choice(segments, n1)

sales = np.random.gamma(shape=3.0, scale=80.0, size=n1).round(2)
sales[12] = 4850.0  # Anomaly outlier
sales[88] = 3920.0  # Anomaly outlier

profit = (sales * np.random.uniform(0.1, 0.35, n1) - np.random.uniform(5, 40, n1)).round(2)
quantity = np.random.randint(1, 10, n1)
discount = np.random.choice([0.0, 0.05, 0.1, 0.15, 0.2], n1)

df_ecommerce = pd.DataFrame({
    "order_id": [f"ORD-{1000 + i}" for i in range(n1)],
    "order_date": dates1,
    "customer_segment": chosen_segment,
    "region": chosen_region,
    "category": chosen_cat,
    "sub_category": chosen_subcat,
    "sales_amount": sales,
    "profit": profit,
    "quantity": quantity,
    "discount": discount
})
df_ecommerce.to_csv("sample_data/ecommerce_orders.csv", index=False)
print("Saved sample_data/ecommerce_orders.csv")

# ==========================================
# 2. SaaS Subscriptions Dataset
# ==========================================
n2 = 200
dates2 = pd.date_range("2023-03-01", "2024-02-28", periods=n2).strftime("%Y-%m-%d")
plans = ["Starter", "Growth", "Enterprise"]
billing = ["Monthly", "Annual"]
countries = ["United States", "Germany", "United Kingdom", "Canada", "France", "Japan"]

chosen_plan = np.random.choice(plans, n2, p=[0.5, 0.35, 0.15])
chosen_billing = np.random.choice(billing, n2, p=[0.7, 0.3])
chosen_country = np.random.choice(countries, n2)

mrr_map = {"Starter": 49.0, "Growth": 199.0, "Enterprise": 899.0}
base_mrr = np.array([mrr_map[p] for p in chosen_plan])
seats = np.random.randint(1, 8, n2)
seats[chosen_plan == "Enterprise"] += np.random.randint(10, 50, sum(chosen_plan == "Enterprise"))

mrr = (base_mrr + seats * 12.5 + np.random.normal(0, 10, n2)).round(2)
mrr[25] = 7800.0  # Anomaly enterprise deal

tickets = np.random.poisson(lam=2, size=n2)
churn_score = np.clip(np.random.beta(2, 5, n2) * 100, 5, 95).round(1)

df_saas = pd.DataFrame({
    "subscription_id": [f"SUB-{5000 + i}" for i in range(n2)],
    "signup_date": dates2,
    "plan_tier": chosen_plan,
    "billing_cycle": chosen_billing,
    "country": chosen_country,
    "mrr_usd": mrr,
    "active_seats": seats,
    "support_tickets_raised": tickets,
    "churn_risk_score": churn_score
})
df_saas.to_csv("sample_data/saas_subscriptions.csv", index=False)
print("Saved sample_data/saas_subscriptions.csv")

# ==========================================
# 3. Hospital Admissions Dataset
# ==========================================
n3 = 220
dates3 = pd.date_range("2023-05-01", "2024-04-30", periods=n3).strftime("%Y-%m-%d")
depts = ["Emergency", "Cardiology", "Orthopedics", "Pediatrics", "Oncology"]
insurance = ["Medicare", "Private", "Medicaid", "Self-Pay"]

chosen_dept = np.random.choice(depts, n3)
chosen_ins = np.random.choice(insurance, n3)
age = np.random.randint(18, 85, n3)
stay_days = np.random.geometric(p=0.25, size=n3)

cost = (stay_days * np.random.uniform(900, 1800, n3) + np.random.normal(500, 100, n3)).round(2)
cost[10] = 45000.0  # Major surgical outlier

rating = np.random.choice([1, 2, 3, 4, 5], n3, p=[0.05, 0.1, 0.2, 0.4, 0.25])

df_hospital = pd.DataFrame({
    "admission_code": [f"ADM-{8000 + i}" for i in range(n3)],
    "admit_date": dates3,
    "department": chosen_dept,
    "insurance_type": chosen_ins,
    "patient_age": age,
    "length_of_stay_days": stay_days,
    "total_treatment_cost": cost,
    "satisfaction_rating": rating
})
df_hospital.to_csv("sample_data/hospital_admissions.csv", index=False)
print("Saved sample_data/hospital_admissions.csv")
