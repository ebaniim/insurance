import streamlit as st
import pandas as pd
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns

CUSTOMERS_FILE = "cust.csv"
CNTT_FILE = "cntt.csv"
CLAIM_FILE = "claim.csv"

st.set_page_config(page_title="Insurance Database Viewer", layout="wide")

@st.cache_data
def load_csv_data(file_path):
    return pd.read_csv(file_path)

customers_df = load_csv_data(CUSTOMERS_FILE)
cntt_df = load_csv_data(CNTT_FILE)
claim_df = load_csv_data(CLAIM_FILE)

conn = duckdb.connect(database=':memory:')
conn.register("customers", customers_df)
conn.register("cntt", cntt_df)
conn.register("claim", claim_df)

st.sidebar.title("Insurance Fraud Analysis")
menu = st.sidebar.radio("Navigate", ["Insurance Database","Overview", "Queries and Visualizations", "Summaries and Action Plans"])

if menu == "Insurance Database":
    st.title("Insurance Database 💼")
    selected_table = st.selectbox("Select a table to view:", ["customers", "cntt", "claim"])

    if selected_table == "customers":
        st.dataframe(customers_df.sort_values(by="CUST_ID", ascending=True))
    elif selected_table == "cntt":
        st.dataframe(cntt_df.sort_values(by="POLY_NO", ascending=True))
    elif selected_table == "claim":
        st.dataframe(claim_df.sort_values(by="POLY_NO", ascending=True))

elif menu == "Overview":
    st.title("Overview of Insurance Database")

    st.markdown("""
    ### Key Objectives
    - **성별 그룹별 사기율을 파악하기**
    - **연령대별 사기율을 분석하기**
    - **총 고객, 정책 및 청구에 대한 통찰력을 얻기기**
    """)

    total_customers = customers_df['CUST_ID'].nunique()
    total_policies = cntt_df['POLY_NO'].nunique()
    total_claims = claim_df['POLY_NO'].count()

    gender_fraud_rate = conn.execute("""
        SELECT SEX, 
               SUM(CASE WHEN SIU_CUST_YN = 'Y' THEN 1 ELSE 0 END) AS FRAUD_COUNT,
               COUNT(*) AS TOTAL_COUNT,
               ROUND((SUM(CASE WHEN SIU_CUST_YN = 'Y' THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 2) AS FRAUD_RATE
        FROM customers
        GROUP BY SEX
    """).df()

    age_fraud_rate = conn.execute("""
        SELECT CASE 
                   WHEN AGE < 25 THEN 'Under 25'
                   WHEN AGE BETWEEN 25 AND 40 THEN '25-40'
                   WHEN AGE BETWEEN 41 AND 60 THEN '41-60'
                   ELSE 'Above 60'
               END AS AGE_GROUP,
               SUM(CASE WHEN SIU_CUST_YN = 'Y' THEN 1 ELSE 0 END) AS FRAUD_COUNT,
               COUNT(*) AS TOTAL_COUNT,
               ROUND((SUM(CASE WHEN SIU_CUST_YN = 'Y' THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 2) AS FRAUD_RATE
        FROM customers
        GROUP BY AGE_GROUP
    """).df()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Customers", total_customers)
    col2.metric("Total Policies", total_policies)
    col3.metric("Total Claims", total_claims)

    st.subheader("Fraud Rate by Gender")
    st.dataframe(gender_fraud_rate)

    st.subheader("Fraud Rate by Age Group")
    st.dataframe(age_fraud_rate)

elif menu == "Queries and Visualizations":
    st.title("Queries & Visualizations 🔍")

    tab1, tab2 = st.tabs(["Analysis Queries", "Custom Query"])
    with tab1:
        st.header("Analysis Queries")
        query = st.selectbox(
            "Choose a Query",
            ["Fraud by Gender", "Fraud by Age Group","Fraud by insurance products"]
        )

        if query == "Fraud by Gender":
            result = conn.execute("""
                SELECT SEX, 
                       COUNT(*) AS TOTAL_CUSTOMERS,
                       SUM(CASE WHEN SIU_CUST_YN = 'Y' THEN 1 ELSE 0 END) AS FRAUD_COUNT,
                       AVG(CASE WHEN SIU_CUST_YN = 'Y' THEN 1.0 ELSE 0.0 END) * 100 AS FRAUD_RATE
                FROM customers
                GROUP BY SEX
            """).df()
            st.dataframe(result)

            st.subheader("Query Graph:")
            fig, ax = plt.subplots()
            sns.barplot(data=result, x="SEX", y="FRAUD_RATE", palette="coolwarm", ax=ax)
            ax.set_title("Fraud Rate by Gender")
            ax.set_ylabel("Fraud Rate (%)")
            st.pyplot(fig)

        elif query == "Fraud by Age Group":
            result = conn.execute("""
                SELECT CASE 
                           WHEN AGE < 25 THEN 'Under 25'
                           WHEN AGE BETWEEN 25 AND 40 THEN '25-40'
                           WHEN AGE BETWEEN 41 AND 60 THEN '41-60'
                           ELSE 'Above 60' 
                       END AS AGE_GROUP,
                       COUNT(*) AS TOTAL_CUSTOMERS,
                       SUM(CASE WHEN SIU_CUST_YN = 'Y' THEN 1 ELSE 0 END) AS FRAUD_COUNT,
                       AVG(CASE WHEN SIU_CUST_YN = 'Y' THEN 1.0 ELSE 0.0 END) * 100 AS FRAUD_RATE
                FROM customers
                GROUP BY AGE_GROUP
            """).df()
            st.dataframe(result)

            st.subheader("Query Graph:")
            fig, ax = plt.subplots()
            sns.barplot(data=result, x="AGE_GROUP", y="FRAUD_RATE", palette="muted", ax=ax)
            ax.set_title("Fraud Rate by Age Group")
            ax.set_ylabel("Fraud Rate (%)")
            st.pyplot(fig)

        elif query == "Fraud by insurance products":
            result = conn.execute("""SELECT 
                        GOOD_CLSF_CDNM,
                        COUNT(*) AS TOTAL_POLICIES,
                        SUM(CASE WHEN customers.SIU_CUST_YN = 'Y' THEN 1 ELSE 0 END) AS FRAUD_COUNT,
                        AVG(CASE WHEN customers.SIU_CUST_YN = 'Y' THEN 1.0 ELSE 0.0 END) * 100 AS FRAUD_RATE
                    FROM cntt
                    JOIN customers ON cntt.CUST_ID = customers.CUST_ID
                    GROUP BY GOOD_CLSF_CDNM
                    ORDER BY FRAUD_RATE desc
                    Limit 5;""").df()
    
            st.dataframe(result)

            st.subheader("Query Graph:")
            fig, ax = plt.subplots()
            sns.barplot(data=result, x="GOOD_CLSF_CDNM", y="FRAUD_RATE", palette="muted", ax=ax)
            ax.set_title("Fraud Rate by Insurance Products")
            ax.set_ylabel("Fraud Rate (%)")
            custom_labels = ["1", "2", "3", "4", "5"]
            ax.set_xticklabels(custom_labels)  
            st.pyplot(fig)



    
    with tab2:
        st.header("Run Custom SQL Query")
        st.text("Example Queries:")
        st.markdown("""
        - **가장 많은 청구를 한 상위 10대 고객**:
        ```sql
        SELECT CUST_ID, COUNT(*) AS TOTAL_CLAIMS
        FROM claim
        GROUP BY CUST_ID
        ORDER BY TOTAL_CLAIMS DESC
        LIMIT 10
        ```
        """)

        query = st.text_area("Enter your SQL Query", height=150)
        if st.button("Execute Query"):
            try:
                result = conn.execute(query).df()
                st.dataframe(result)
            except Exception as e:
                st.error(f"Error: {e}")

elif menu == "Summaries and Action Plans":
    st.title("Summaries & Action Plans 📋")

    tab1, tab2 = st.tabs(["Summary Report", "Recommendations & Action Plan"])

    with tab1:
        st.markdown("""
        ### 1. 성별과 사기
        - **관찰**: 여성 고객의 사기율이 남성 고객보다 더 높게 나타났다. 이는 특정 패턴이나 정책이 특정 그룹을 더 취약하게 만들거나, 검출이 더 용이하게 작용했을 가능성이 있다.

        ### 2. 연령대와 사기
        - **관찰**: 30~60세 연령대 고객의 사기율이 가장 높게 나타났다. 이 연령대는 보험 가입 및 클레임 활동이 가장 활발한 경제 활동 인구층이다.

        ### 3. 보험 상품
        - **관찰**: 보험 상품별로 사기율이 크게 다르게 나타났다. 특히 고가치 또는 고위험 상품에서 사기 비율이 높은 경향이 있다.
        """)

    with tab2:
        st.markdown("""
        ### 추천 사항
        - **고급 분석 기술 활용**: 실시간 사기 탐지를 위해 AI 및 머신러닝 모델 개발
        - **고객 교육 강화**: 고위험 인구통계학적 집단을 대상으로 한 보험 사기 위험에 대한 인식 캠페인 실시
        - **사기 탐지 프로세스 맞춤화**: 연령, 성별, 상품 분석에서 도출된 위험 프로필을 기반으로 검증 절차 최적
        - **사기 모니터링 시스템 도입**: 과거 데이터 및 분석을 활용하여 고위험 거래를 자동으로 감지할 수 있는 도구 배치

        ---

        ### 세부 실행 계획

        #### 1. 연령대별 사기
        - **고위험 연령대**: 30~60세 고객의 사기율이 가장 높다.
        - **실행 계획**:
        1. 이 연령대에서 접수된 청구에 대해 이상 금액 및 빈도를 확인하는 추가 검증 단계를 만든다.
        2. 이 연령대에서 나타나는 의심스러운 행동 패턴을 인지할 수 있도록 보험 담당자를 훈련한다.
        3. 사기 탐지 AI 모델에서 연령을 가중치 요소로 포함시켜 위험 평가의 정확도를 높인다.

        #### 2. 성별별 사기
        - **고위험 그룹**: 여성 고객의 사기율이 남성 고객보다 높게 나타났다.
        - **실행 계획**:
        1. 여성 고객의 청구 처리 방식에서 암묵적인 편향이 없는지 확인하기 위해 기존 정책을 검토한다.
        2. 여성 고객에서 발생하는 사기 사례의 유형과 상품을 세부적으로 분석한다.
        3. 사기 사례를 분석하고, 이를 기반으로 성별별 패턴을 탐지하기 위한 알고리즘을 지속적으로 개선한다.

        #### 3. 보험 상품별 사기
        - **고위험 상품**: 정기, 어린이저축, 일반저축, 교육, 일반연금이 높은 사기율을 보인다.
        - **실행 계획**:
        1. 이러한 상품의 고유 특성을 반영한 상품별 사기 탐지 알고리즘을 개발한다.
        2. 정기적인 감사 절차를 통해 고위험 상품에서 발생하는 패턴과 악용 사례를 확인한다.
        3. 보험 약관을 세부적으로 검토하여 사기에 악용될 수 있는 허점을 제거하기 위해 언더라이터와 협력한다.
        4. 고위험 청구에 대해 자동 검토를 트리거할 수 있는 청구 상한선을 도입한다.

        ---

        ### 최종 메모
        이 실행 계획은 사기 탐지 능력을 강화하고, 위험을 최소화하며, 공정성과 투명성을 유지하면서 전반적인 청구 프로세스를 최적화하는 것을 목표로 한다.
        """)

