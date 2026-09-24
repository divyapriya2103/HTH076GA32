import pandas as pd
from schema_inference import infer_schema, get_columns_by_role
from nlp_query import parse_question
from query_engine import execute_query
from explain import generate_explanation, detect_anomalies

def run_tests():
    print("=" * 60)
    print("RUNNING SCHEMA-AGNOSTIC DATA ANALYST VERIFICATION SUITE")
    print("=" * 60)

    datasets = [
        {
            "name": "E-Commerce Retail",
            "path": "sample_data/ecommerce_orders.csv",
            "expected_date": "order_date",
            "expected_measure": "sales_amount",
            "expected_dim": "region",
            "expected_id": "order_id",
            "sample_questions": [
                "What is the total sales amount?",
                "Total sales amount by region",
                "Top 3 categories by sales amount",
                "Monthly sales amount trend",
                "Average sales amount in West"
            ]
        },
        {
            "name": "SaaS Subscriptions",
            "path": "sample_data/saas_subscriptions.csv",
            "expected_date": "signup_date",
            "expected_measure": "mrr_usd",
            "expected_dim": "plan_tier",
            "expected_id": "subscription_id",
            "sample_questions": [
                "What is the total mrr?",
                "Average mrr by plan tier",
                "Top 3 countries by mrr",
                "MRR trend over time",
                "Total mrr for Enterprise"
            ]
        },
        {
            "name": "Hospital Admissions",
            "path": "sample_data/hospital_admissions.csv",
            "expected_date": "admit_date",
            "expected_measure": "total_treatment_cost",
            "expected_dim": "department",
            "expected_id": "admission_code",
            "sample_questions": [
                "Total treatment cost",
                "Average treatment cost by department",
                "Top 4 departments by treatment cost",
                "Cost trend over time",
                "Average treatment cost in Cardiology"
            ]
        }
    ]

    for d in datasets:
        print(f"\n--- Testing Dataset: {d['name']} ---")
        df = pd.read_csv(d["path"])
        schema = infer_schema(df)
        
        # Test 1: Schema Inference
        assert d["expected_date"] in get_columns_by_role(schema, "date"), f"Failed to infer date col {d['expected_date']}"
        assert d["expected_measure"] in get_columns_by_role(schema, "measure"), f"Failed to infer measure col {d['expected_measure']}"
        assert d["expected_dim"] in get_columns_by_role(schema, "dimension"), f"Failed to infer dim col {d['expected_dim']}"
        assert d["expected_id"] in get_columns_by_role(schema, "id"), f"Failed to infer id col {d['expected_id']}"
        print(f"  [PASS] Schema Inference verified for {len(schema)} columns.")

        # Test 2: Anomaly Detection
        anomalies = detect_anomalies(df, schema)
        assert len(anomalies) > 0, f"Expected anomaly detection in {d['name']}"
        print(f"  [PASS] Anomaly detection identified {len(anomalies)} outlier flag(s).")

        # Test 3: 5 Question Types Execution
        last_plan = None
        for q in d["sample_questions"]:
            plan = parse_question(q, schema, df, last_plan=last_plan)
            res_df, steps, err = execute_query(df, plan)
            assert err is None, f"Query '{q}' returned error: {err}"
            assert res_df is not None and not res_df.empty, f"Query '{q}' returned empty dataframe"
            explanation = generate_explanation(plan, steps)
            assert "Calculation Reasoning" in explanation, f"Explanation malformed for '{q}'"
            print(f"  [PASS] Q: '{q}' -> Shape: {res_df.shape}, Steps: {len(steps)}")
            last_plan = plan

        # Test 4: Conversational Follow-up
        follow_up_q = "Show average instead"
        fu_plan = parse_question(follow_up_q, schema, df, last_plan=last_plan)
        res_df, steps, err = execute_query(df, fu_plan)
        assert err is None and res_df is not None
        assert fu_plan["agg"] == "mean", f"Expected mean aggregation in follow-up, got {fu_plan['agg']}"
        print(f"  [PASS] Conversational follow-up: '{follow_up_q}' correctly inherited context.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ENGINE IS VERIFIED AND READY.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
