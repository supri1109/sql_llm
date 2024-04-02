import streamlit as st
import pyodbc
from sqlalchemy.engine import URL
from langchain_community.llms import AzureOpenAI
from langchain_community.utilities import SQLDatabase
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_sql_query_chain
import os
from langchain_openai import AzureChatOpenAI

os.environ["AZURE_OPENAI_API_KEY"] = "c546b3e067584e49adaf2e880c28472f"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://cog-v76g3g7q7vqto.openai.azure.com/"

st.title("🤖 Unlocking Clinical Trial Insights: Leveraging LLMs for Database Queries")

def generate_sql_code(prompt):
    # check the local ODBC driver and make sure it match with the target database instance
    for driver in pyodbc.drivers():
        print(driver)

    server = 'appdbserver082.database.windows.net'
    database = 'appdb'
    username = 'saisupriya.vadali@bs.nttdata.com'
    driver = 'ODBC+Driver+18+for+SQL+Server'
    auth = 'ActiveDirectoryInteractive'
    table = "clinical_trial_dboard"
    # Connecting to db through SQLDatabase of Langchain
    conn_string = 'DRIVER={ODBC Driver 18 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';Authentication='+auth+';ENCRYPT=yes'
    conn_url = URL.create("mssql+pyodbc", query={"odbc_connect": conn_string})
    db = SQLDatabase.from_uri(conn_url)

    answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question.
Question: {question}
SQL Query: {query}
SQL Result: {result}
Answer: """
)
    
    llm = AzureChatOpenAI(
    openai_api_version="2023-05-15",
    azure_deployment="chat",
    temperature = 0.01
)
    execute_query = QuerySQLDataBaseTool(db=db)
    write_query = create_sql_query_chain(llm, db)
    chain = write_query | execute_query
    answer = answer_prompt | llm | StrOutputParser()
    chain = (
        RunnablePassthrough.assign(query=write_query).assign(
            result=itemgetter("query") | execute_query
        )
        | answer
    )
    sql_chain = create_sql_query_chain(llm, db=db)
    sql_code = sql_chain.invoke({"question": prompt})
    response = chain.invoke({"question": prompt})

    return sql_code, response

# Create a bigger textbox for the user to enter the prompt
prompt = st.text_area("Enter your prompt:", height=100)


# Create a button for generating the SQL code
generate_button = st.button("Execute")

# Display a loading symbol while the SQL code is being generated
if generate_button:
    with st.spinner("Processing..."):
        sql_code, response = generate_sql_code(prompt)
        st.subheader("Generated SQL Code:")
        st.code(sql_code)
        st.subheader("Generated Response:")
        st.write(response)