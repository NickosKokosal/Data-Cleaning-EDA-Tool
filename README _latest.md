# No-Code Data Cleaning & EDA App

## Εκτέλεση (τοπικά, χωρίς Docker)
```bash
pip install -r requirements.txt
streamlit run app.py
```
Θα ανοίξει στο browser στο `http://localhost:8501`.

## Εκτέλεση με Docker
```bash
docker compose up --build
```
ή χωρίς compose:
```bash
docker build -t nocode-eda-app .
docker run -p 8501:8501 nocode-eda-app
```
Άνοιξε το browser στο `http://localhost:8501`.

## Τι κάνει
- **Upload**: .csv ή .xlsx από το sidebar.
- **Data Cleaning tab**: διαγραφή διπλότυπων, διαχείριση κενών (drop/mean/median/mode/σταθερή τιμή), one-hot / label encoding, διαγραφή στηλών, μετατροπή τύπου δεδομένων.
- **EDA tab**: `describe()`, γράφημα κενών τιμών, correlation heatmap, scatter/bar/histogram/box plots με επιλογή στηλών από dropdown.
- **Export tab**: κατέβασμα του καθαρισμένου dataset σε CSV ή Excel.

Το DataFrame κρατιέται στο `st.session_state`, ώστε οι αλλαγές να παραμένουν
ανάμεσα σε clicks (το Streamlit ξανατρέχει όλο το script σε κάθε interaction).

## Πιθανές επεκτάσεις
- Outlier detection (IQR / z-score) με κουμπί αφαίρεσης.
- Undo/redo χρησιμοποιώντας το `history` που ήδη κρατιέται.
- Auto-profiling με `ydata-profiling` για πιο πλήρες EDA report.
- Deploy σε Streamlit Community Cloud για δωρεάν hosting.
