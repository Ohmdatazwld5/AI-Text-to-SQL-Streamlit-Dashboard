import streamlit as st
import pandas as pd
from llm_text2sql import natural_to_sql
from query_executor import run_sql_query
from graph_utils import decide_chart_type, plot_chart
from config import DB_PATH, ensure_db
import os

st.set_page_config(page_title="Text-to-SQL App", page_icon="📊", layout="wide")
st.title("📊 AI-Powered Text-to-SQL Query App")

# Ensure DB is present
ensure_db()

# Debug sidebar info
st.sidebar.write("**Debug Info**")
st.sidebar.write("DB Path:", DB_PATH)
st.sidebar.write("Exists:", DB_PATH.exists())
if DB_PATH.exists():
    st.sidebar.write("Size (KB):", round(os.path.getsize(DB_PATH) / 1024, 2))

st.write(
    """
    **Ask questions in plain English** (e.g., "Show total sales by country")  
    The AI will convert your question into SQL, execute it on the Chinook database, and show the results.
    """
)

# User Input
user_query = st.text_input("Enter your question:", placeholder="e.g., Show top 5 customers by total purchase amount")

if st.button("Submit") and user_query.strip():
    with st.spinner("🔍 Generating SQL query..."):
        sql_query = natural_to_sql(user_query)
    st.subheader("Generated SQL Query")
    st.code(sql_query, language="sql")

    with st.spinner("⚡ Running query..."):
        result = run_sql_query(sql_query)

    if isinstance(result, str):
        st.error(result)
    elif isinstance(result, pd.DataFrame) and not result.empty:
        st.subheader("Query Results")
        st.dataframe(result)

        chart_type = decide_chart_type(user_query, result)
        if chart_type and result.shape[1] >= 2:
            st.subheader(f"Graphical Representation ({chart_type.title()} Chart)")
            chart_data = plot_chart(result, chart_type, user_query=user_query)
            if chart_data:
                st.image(chart_data)
    else:
        st.warning("No results found for this query.")

