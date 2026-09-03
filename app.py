"""
No-Code Data Cleaning & EDA App
--------------------------------
Streamlit app: the user uploads a .csv or .xlsx file and through a UI
can run data cleaning and exploratory data analysis (EDA) without code.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import io

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Data Cleaning & EDA", layout="wide")

# ----------------------------------------------------------------------
# STATE MANAGEMENT
# ----------------------------------------------------------------------
# Streamlit re-runs the whole script on every interaction, so we need to
# keep the DataFrame (and the action history) in session_state so that
# changes persist between clicks.
if "df" not in st.session_state:
    st.session_state.df = None
if "history" not in st.session_state:
    st.session_state.history = []


def log(action: str):
    st.session_state.history.append(action)


def load_file(uploaded_file):
    """Reads csv or xlsx into a DataFrame, with basic error handling."""
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error while reading the file: {e}")
        return None


# ----------------------------------------------------------------------
# SIDEBAR — UPLOAD & RESET
# ----------------------------------------------------------------------
st.sidebar.title("File")
uploaded_file = st.sidebar.file_uploader("Upload .csv or .xlsx", type=["csv", "xlsx", "xls"])

if uploaded_file is not None and st.session_state.df is None:
    df = load_file(uploaded_file)
    if df is not None:
        st.session_state.df = df
        st.session_state.history = [f"File loaded: {uploaded_file.name} ({df.shape[0]} rows, {df.shape[1]} columns)"]

if st.sidebar.button("Reset (new file)"):
    st.session_state.df = None
    st.session_state.history = []
    st.rerun()

if st.session_state.history:
    with st.sidebar.expander("Activity history", expanded=False):
        for h in st.session_state.history:
            st.write("-", h)

st.title("Data Cleaning & EDA Tool")

if st.session_state.df is None:
    st.info("Upload a .csv or .xlsx file from the sidebar to get started.")
    st.stop()

df = st.session_state.df

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab_preview, tab_clean, tab_eda, tab_export = st.tabs(
    ["Preview", "Data Cleaning", "EDA", "Export"]
)

# ------------------------- TAB 1: PREVIEW ------------------------------
with tab_preview:
    st.subheader("Data preview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Duplicate rows", int(df.duplicated().sum()))

    st.dataframe(df.head(50), use_container_width=True)

    st.subheader("Data types per column")
    dtypes_df = pd.DataFrame({"Column": df.columns, "Type": df.dtypes.astype(str).values})
    st.dataframe(dtypes_df, use_container_width=True, hide_index=True)

# ------------------------- TAB 2: CLEANING ------------------------------
with tab_clean:
    st.subheader("Cleaning operations")

    # --- Duplicates ---
    with st.expander("Delete duplicate rows", expanded=True):
        n_dupes = int(df.duplicated().sum())
        st.write(f"Found **{n_dupes}** duplicate rows.")
        if st.button("Delete duplicate rows", disabled=(n_dupes == 0)):
            before = len(df)
            st.session_state.df = df.drop_duplicates().reset_index(drop=True)
            log(f"Deleted {before - len(st.session_state.df)} duplicate rows")
            st.rerun()

    # --- Missing values ---
    with st.expander("Handle missing values"):
        missing = df.isna().sum()
        missing = missing[missing > 0]
        if missing.empty:
            st.write("No missing values.")
        else:
            st.dataframe(
                pd.DataFrame({"Column": missing.index, "Missing": missing.values}),
                use_container_width=True,
                hide_index=True,
            )
            col = st.selectbox("Choose column", missing.index.tolist(), key="miss_col")
            is_numeric = pd.api.types.is_numeric_dtype(df[col])

            options = ["Drop rows with missing value", "Replace with a fixed value"]
            if is_numeric:
                options += ["Replace with Mean", "Replace with Median"]
            else:
                options += ["Replace with Mode (most frequent value)"]

            strategy = st.selectbox("Strategy", options, key="miss_strategy")
            fill_value = None
            if strategy == "Replace with a fixed value":
                fill_value = st.text_input("Replacement value", key="miss_fill_value")

            if st.button("Apply", key="apply_missing"):
                new_df = df.copy()
                try:
                    if strategy == "Drop rows with missing value":
                        new_df = new_df.dropna(subset=[col])
                        log(f"Dropped rows with a missing value in column '{col}'")
                    elif strategy == "Replace with a fixed value":
                        val = fill_value
                        if is_numeric and fill_value not in (None, ""):
                            val = float(fill_value)
                        new_df[col] = new_df[col].fillna(val)
                        log(f"Column '{col}': missing values replaced with '{fill_value}'")
                    elif strategy == "Replace with Mean":
                        new_df[col] = new_df[col].fillna(new_df[col].mean())
                        log(f"Column '{col}': missing values replaced with the mean")
                    elif strategy == "Replace with Median":
                        new_df[col] = new_df[col].fillna(new_df[col].median())
                        log(f"Column '{col}': missing values replaced with the median")
                    elif strategy == "Replace with Mode (most frequent value)":
                        mode_val = new_df[col].mode(dropna=True)
                        if not mode_val.empty:
                            new_df[col] = new_df[col].fillna(mode_val.iloc[0])
                            log(f"Column '{col}': missing values replaced with the mode")
                    st.session_state.df = new_df
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- Encoding ---
    with st.expander("Encode categorical columns"):
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if not cat_cols:
            st.write("There are no categorical (text) columns.")
        else:
            col = st.selectbox("Choose column", cat_cols, key="enc_col")
            n_unique = df[col].nunique()
            st.write(f"This column has **{n_unique}** unique values.")
            method = st.radio(
                "Method",
                ["One-Hot Encoding (get_dummies)", "Label Encoding (0,1,2,...)"],
                key="enc_method",
            )
            if st.button("Apply encoding", key="apply_encoding"):
                new_df = df.copy()
                if method.startswith("One-Hot"):
                    dummies = pd.get_dummies(new_df[col], prefix=col)
                    new_df = pd.concat([new_df.drop(columns=[col]), dummies], axis=1)
                    log(f"Applied One-Hot Encoding to column '{col}'")
                else:
                    new_df[col] = new_df[col].astype("category").cat.codes
                    log(f"Applied Label Encoding to column '{col}'")
                st.session_state.df = new_df
                st.rerun()

    # --- Drop columns ---
    with st.expander("Drop columns"):
        cols_to_drop = st.multiselect("Choose columns to drop", df.columns.tolist())
        if st.button("Drop columns", disabled=(len(cols_to_drop) == 0)):
            st.session_state.df = df.drop(columns=cols_to_drop)
            log(f"Dropped columns: {', '.join(cols_to_drop)}")
            st.rerun()

    # --- Data type conversion ---
    with st.expander("Convert data type (dtype)"):
        col = st.selectbox("Choose column", df.columns.tolist(), key="dtype_col")
        new_type = st.selectbox("New type", ["int", "float", "string", "datetime"], key="dtype_new")
        if st.button("Convert", key="apply_dtype"):
            new_df = df.copy()
            try:
                if new_type == "int":
                    new_df[col] = pd.to_numeric(new_df[col], errors="coerce").astype("Int64")
                elif new_type == "float":
                    new_df[col] = pd.to_numeric(new_df[col], errors="coerce")
                elif new_type == "string":
                    new_df[col] = new_df[col].astype(str)
                elif new_type == "datetime":
                    new_df[col] = pd.to_datetime(new_df[col], errors="coerce")
                st.session_state.df = new_df
                log(f"Column '{col}' converted to {new_type}")
                st.rerun()
            except Exception as e:
                st.error(f"Conversion failed: {e}")

# ------------------------- TAB 3: EDA ------------------------------
with tab_eda:
    st.subheader("Statistical overview")
    st.dataframe(df.describe(include="all").transpose(), use_container_width=True)

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    st.subheader("Missing values per column")
    missing_counts = df.isna().sum()
    if missing_counts.sum() == 0:
        st.write("No missing values.")
    else:
        fig_missing = px.bar(
            x=missing_counts.index, y=missing_counts.values,
            labels={"x": "Column", "y": "Missing count"},
            title="Missing values per column",
        )
        st.plotly_chart(fig_missing, use_container_width=True)

    if len(numeric_cols) >= 2:
        st.subheader("Correlation heatmap")
        corr = df[numeric_cols].corr(numeric_only=True)
        fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", title="Correlation Heatmap")
        st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Explore relationships between columns")
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Column X", df.columns.tolist(), key="x_col")
    with col2:
        y_col = st.selectbox("Column Y", df.columns.tolist(), index=min(1, len(df.columns) - 1), key="y_col")

    chart_type = st.radio("Chart type", ["Scatter", "Bar", "Histogram", "Box"], horizontal=True)

    try:
        if chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
        elif chart_type == "Bar":
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        elif chart_type == "Histogram":
            fig = px.histogram(df, x=x_col, title=f"Distribution of {x_col}")
        else:
            fig = px.box(df, x=x_col, y=y_col, title=f"Boxplot of {y_col} by {x_col}")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not create chart: {e}")

# ------------------------- TAB 4: EXPORT ------------------------------
with tab_export:
    st.subheader("Download the cleaned dataset")
    st.dataframe(df.head(20), use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download as CSV", data=csv_bytes, file_name="cleaned_data.csv", mime="text/csv")

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    st.download_button(
        "Download as Excel",
        data=excel_buffer.getvalue(),
        file_name="cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
