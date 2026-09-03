# No-Code Data Cleaning & EDA App

## Run (locally, without Docker)

```bash
pip install -r requirements.txt
streamlit run app.py
```

It will open in the browser at `http://localhost:8501`.

## Run with Docker

```bash
docker compose up --build
```

or without compose:

```bash
docker build -t nocode-eda-app .
docker run -p 8501:8501 nocode-eda-app
```

Open the browser to `http://localhost:8501`.

## What does it do?

- **Upload**: .csv or .xlsx from the sidebar.
- **Data Cleaning tab**: delete duplicates, manage gaps (drop/mean/median/mode/constant value), one-hot / label encoding, delete columns, data type conversion.
- **EDA tab**: `describe()`, graph of empty values, correlation heatmap, scatter/bar/histogram/box plots with column selection from dropdown.
- **Export tab**: download the cleaned dataset to CSV or Excel.

The DataFrame is held in `st.session_state` so that changes persist
between clicks (Streamlit reruns the entire script on each interaction).

## Possible extensions

- Outlier detection (IQR / z-score) with remove button.
- Undo/redo using `history` already held.
- Auto-profiling with `ydata-profiling` for a more complete EDA report.
- Deploy to Streamlit Community Cloud for free hosting.
