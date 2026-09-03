"""
No-Code Data Cleaning & EDA App
--------------------------------
Streamlit app: ο χρήστης ανεβάζει ένα .csv ή .xlsx αρχείο και μέσα από ένα UI
μπορεί να κάνει data cleaning και exploratory data analysis (EDA) χωρίς κώδικα.

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
# Το Streamlit ξανατρέχει όλο το script σε κάθε interaction, οπότε πρέπει
# να κρατάμε το DataFrame (και το ιστορικό ενεργειών) στο session_state
# ώστε οι αλλαγές να "κολλάνε" ανάμεσα σε clicks.
if "df" not in st.session_state:
    st.session_state.df = None
if "history" not in st.session_state:
    st.session_state.history = []


def log(action: str):
    st.session_state.history.append(action)


def load_file(uploaded_file):
    """Διαβάζει csv ή xlsx σε DataFrame, με βασικό error handling."""
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Σφάλμα κατά την ανάγνωση του αρχείου: {e}")
        return None


# ----------------------------------------------------------------------
# SIDEBAR — UPLOAD & RESET
# ----------------------------------------------------------------------
st.sidebar.title("Αρχείο")
uploaded_file = st.sidebar.file_uploader("Ανέβασε .csv ή .xlsx", type=["csv", "xlsx", "xls"])

if uploaded_file is not None and st.session_state.df is None:
    df = load_file(uploaded_file)
    if df is not None:
        st.session_state.df = df
        st.session_state.history = [f"Φορτώθηκε αρχείο: {uploaded_file.name} ({df.shape[0]} γραμμές, {df.shape[1]} στήλες)"]

if st.sidebar.button("Reset (νέο αρχείο)"):
    st.session_state.df = None
    st.session_state.history = []
    st.rerun()

if st.session_state.history:
    with st.sidebar.expander("Ιστορικό ενεργειών", expanded=False):
        for h in st.session_state.history:
            st.write("•", h)

st.title("Data Cleaning & EDA-Tool")

if st.session_state.df is None:
    st.info("Ανέβασε ένα .csv ή .xlsx αρχείο από το sidebar για να ξεκινήσεις.")
    st.stop()

df = st.session_state.df

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab_preview, tab_clean, tab_eda, tab_export = st.tabs(
    ["Προεπισκόπηση", "Data Cleaning", "EDA", "Export"]
)

# ------------------------- TAB 1: PREVIEW ------------------------------
with tab_preview:
    st.subheader("Προεπισκόπηση δεδομένων")
    c1, c2, c3 = st.columns(3)
    c1.metric("Γραμμές", df.shape[0])
    c2.metric("Στήλες", df.shape[1])
    c3.metric("Διπλότυπες γραμμές", int(df.duplicated().sum()))

    st.dataframe(df.head(50), use_container_width=True)

    st.subheader("Τύποι δεδομένων ανά στήλη")
    dtypes_df = pd.DataFrame({"Στήλη": df.columns, "Τύπος": df.dtypes.astype(str).values})
    st.dataframe(dtypes_df, use_container_width=True, hide_index=True)

# ------------------------- TAB 2: CLEANING ------------------------------
with tab_clean:
    st.subheader("Ενέργειες καθαρισμού")

    # --- Διπλότυπα ---
    with st.expander("Διαγραφή διπλότυπων γραμμών", expanded=True):
        n_dupes = int(df.duplicated().sum())
        st.write(f"Βρέθηκαν **{n_dupes}** διπλότυπες γραμμές.")
        if st.button("Διαγραφή διπλότυπων", disabled=(n_dupes == 0)):
            before = len(df)
            st.session_state.df = df.drop_duplicates().reset_index(drop=True)
            log(f"Διαγράφηκαν {before - len(st.session_state.df)} διπλότυπες γραμμές")
            st.rerun()

    # --- Missing values ---
    with st.expander("Διαχείριση κενών τιμών (missing values)"):
        missing = df.isna().sum()
        missing = missing[missing > 0]
        if missing.empty:
            st.write("Δεν υπάρχουν κενές τιμές.")
        else:
            st.dataframe(
                pd.DataFrame({"Στήλη": missing.index, "Κενά": missing.values}),
                use_container_width=True,
                hide_index=True,
            )
            col = st.selectbox("Επίλεξε στήλη", missing.index.tolist(), key="miss_col")
            is_numeric = pd.api.types.is_numeric_dtype(df[col])

            options = ["Διαγραφή γραμμών με κενό", "Αντικατάσταση με σταθερή τιμή"]
            if is_numeric:
                options += ["Αντικατάσταση με Mean", "Αντικατάσταση με Median"]
            else:
                options += ["Αντικατάσταση με Mode (πιο συχνή τιμή)"]

            strategy = st.selectbox("Στρατηγική", options, key="miss_strategy")
            fill_value = None
            if strategy == "Αντικατάσταση με σταθερή τιμή":
                fill_value = st.text_input("Τιμή αντικατάστασης", key="miss_fill_value")

            if st.button("Εφαρμογή", key="apply_missing"):
                new_df = df.copy()
                try:
                    if strategy == "Διαγραφή γραμμών με κενό":
                        new_df = new_df.dropna(subset=[col])
                        log(f"Διαγράφηκαν γραμμές με κενό στη στήλη '{col}'")
                    elif strategy == "Αντικατάσταση με σταθερή τιμή":
                        val = fill_value
                        if is_numeric and fill_value not in (None, ""):
                            val = float(fill_value)
                        new_df[col] = new_df[col].fillna(val)
                        log(f"Στήλη '{col}': κενά αντικαταστάθηκαν με '{fill_value}'")
                    elif strategy == "Αντικατάσταση με Mean":
                        new_df[col] = new_df[col].fillna(new_df[col].mean())
                        log(f"Στήλη '{col}': κενά αντικαταστάθηκαν με τη μέση τιμή")
                    elif strategy == "Αντικατάσταση με Median":
                        new_df[col] = new_df[col].fillna(new_df[col].median())
                        log(f"Στήλη '{col}': κενά αντικαταστάθηκαν με τη διάμεσο")
                    elif strategy == "Αντικατάσταση με Mode (πιο συχνή τιμή)":
                        mode_val = new_df[col].mode(dropna=True)
                        if not mode_val.empty:
                            new_df[col] = new_df[col].fillna(mode_val.iloc[0])
                            log(f"Στήλη '{col}': κενά αντικαταστάθηκαν με την πιο συχνή τιμή")
                    st.session_state.df = new_df
                    st.rerun()
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

    # --- Encoding ---
    with st.expander("Encoding κατηγορικών στηλών"):
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if not cat_cols:
            st.write("Δεν υπάρχουν κατηγορικές (text) στήλες.")
        else:
            col = st.selectbox("Επίλεξε στήλη", cat_cols, key="enc_col")
            n_unique = df[col].nunique()
            st.write(f"Η στήλη έχει **{n_unique}** μοναδικές τιμές.")
            method = st.radio(
                "Μέθοδος",
                ["One-Hot Encoding (get_dummies)", "Label Encoding (0,1,2,...)"],
                key="enc_method",
            )
            if st.button("Εφαρμογή encoding", key="apply_encoding"):
                new_df = df.copy()
                if method.startswith("One-Hot"):
                    dummies = pd.get_dummies(new_df[col], prefix=col)
                    new_df = pd.concat([new_df.drop(columns=[col]), dummies], axis=1)
                    log(f"Έγινε One-Hot Encoding στη στήλη '{col}'")
                else:
                    new_df[col] = new_df[col].astype("category").cat.codes
                    log(f"Έγινε Label Encoding στη στήλη '{col}'")
                st.session_state.df = new_df
                st.rerun()

    # --- Διαγραφή στηλών ---
    with st.expander("Διαγραφή στηλών"):
        cols_to_drop = st.multiselect("Επίλεξε στήλες προς διαγραφή", df.columns.tolist())
        if st.button("Διαγραφή στηλών", disabled=(len(cols_to_drop) == 0)):
            st.session_state.df = df.drop(columns=cols_to_drop)
            log(f"Διαγράφηκαν στήλες: {', '.join(cols_to_drop)}")
            st.rerun()

    # --- Μετατροπή τύπου δεδομένων ---
    with st.expander("Μετατροπή τύπου δεδομένων (dtype)"):
        col = st.selectbox("Επίλεξε στήλη", df.columns.tolist(), key="dtype_col")
        new_type = st.selectbox("Νέος τύπος", ["int", "float", "string", "datetime"], key="dtype_new")
        if st.button("Μετατροπή", key="apply_dtype"):
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
                log(f"Στήλη '{col}' μετατράπηκε σε {new_type}")
                st.rerun()
            except Exception as e:
                st.error(f"Δεν ήταν δυνατή η μετατροπή: {e}")

# ------------------------- TAB 3: EDA ------------------------------
with tab_eda:
    st.subheader("Στατιστική επισκόπηση")
    st.dataframe(df.describe(include="all").transpose(), use_container_width=True)

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    st.subheader("Κενές τιμές ανά στήλη")
    missing_counts = df.isna().sum()
    if missing_counts.sum() == 0:
        st.write("Δεν υπάρχουν κενές τιμές.")
    else:
        fig_missing = px.bar(
            x=missing_counts.index, y=missing_counts.values,
            labels={"x": "Στήλη", "y": "Πλήθος κενών"},
            title="Κενές τιμές ανά στήλη",
        )
        st.plotly_chart(fig_missing, use_container_width=True)

    if len(numeric_cols) >= 2:
        st.subheader("Heatmap συσχέτισης (Correlation)")
        corr = df[numeric_cols].corr(numeric_only=True)
        fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", title="Correlation Heatmap")
        st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Διερεύνηση σχέσεων μεταξύ στηλών")
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Στήλη X", df.columns.tolist(), key="x_col")
    with col2:
        y_col = st.selectbox("Στήλη Y", df.columns.tolist(), index=min(1, len(df.columns) - 1), key="y_col")

    chart_type = st.radio("Τύπος γραφήματος", ["Scatter", "Bar", "Histogram", "Box"], horizontal=True)

    try:
        if chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
        elif chart_type == "Bar":
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} ανά {x_col}")
        elif chart_type == "Histogram":
            fig = px.histogram(df, x=x_col, title=f"Κατανομή {x_col}")
        else:
            fig = px.box(df, x=x_col, y=y_col, title=f"Boxplot {y_col} ανά {x_col}")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Δεν ήταν δυνατή η δημιουργία γραφήματος: {e}")

# ------------------------- TAB 4: EXPORT ------------------------------
with tab_export:
    st.subheader("Κατέβασε το καθαρισμένο dataset")
    st.dataframe(df.head(20), use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Κατέβασμα ως CSV", data=csv_bytes, file_name="cleaned_data.csv", mime="text/csv")

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    st.download_button(
        "Κατέβασμα ως Excel",
        data=excel_buffer.getvalue(),
        file_name="cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
