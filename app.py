import streamlit as st
import pandas as pd
from llm_text2sql import natural_to_sql
from query_executor import run_sql_query
from graph_utils import decide_chart_type, plot_chart

st.set_page_config(page_title="Text-to-SQL App", page_icon="📊", layout="wide")
st.title("📊 AI-Powered Text-to-SQL Query App")

st.write(
    """
    **Ask questions in plain English** (e.g., "Show total sales by country")  
    The AI will convert your question into SQL, execute it on the Chinook database, and show the results.
    """
)

# User Input
user_query = st.text_input("Enter your question:", placeholder="e.g., Show top 5 customers by total purchase amount")

if st.button("Submit") and user_query.strip():
    # Step 1: Generate SQL using Groq LLM
    with st.spinner("🔍 Generating SQL query..."):
        sql_query = natural_to_sql(user_query)
    st.subheader("Generated SQL Query")
    st.code(sql_query, language="sql")

    # Step 2: Execute SQL query
    with st.spinner("⚡ Running query..."):
        result = run_sql_query(sql_query)

    # Step 3: Display results
    if isinstance(result, str):
        st.error(result)
    elif isinstance(result, pd.DataFrame) and not result.empty:
        st.subheader("Query Results")
        st.dataframe(result)

        # Step 4: Decide and plot graph if applicable
        chart_type = decide_chart_type(user_query, result)
        if chart_type and result.shape[1] >= 2:
            st.subheader(f"Graphical Representation ({chart_type.title()} Chart)")
            chart_data = plot_chart(result, chart_type, user_query=user_query)
            if chart_data:
                st.image(chart_data)

    else:
        st.warning("No results found for this query.")
