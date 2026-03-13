# 🎓 EduKit India — Business Validation Dashboard

A fully interactive Streamlit dashboard replicating the EduKit India Business Validation Dashboard (v19), with all charts, statistical models, and live data filtering.

## 🚀 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

---

## 📊 Features

| Tab | Contents |
|-----|----------|
| **Overview** | Pipeline donut, revenue by product, deal value vs NPS scatter |
| **Channels** | Leads vs converted grouped bar, conversion rate, avg deal value |
| **Funnel** | Sales pipeline funnel chart, stage × channel stacked bar |
| **Trends** | Monthly leads/conversions line chart, revenue bar, channel × month heatmap |
| **Segments** | NPS & conversion bars, radar comparison chart |
| **Geography** | India scatter-geo map, city revenue & conversion bars, summary table |
| **Products** | Lead share donut, revenue bar, NPS bar, product quadrant bubble |
| **Data Quality** | Cleaning ops log, distribution histograms, box plots |
| **Statistical Models** | Pareto, Z-Score, Cohort Matrix, BCG Matrix, Linear Regression, RFM |
| **Raw Data** | Full filterable table with export |

### 🤖 Statistical Models
- **Pareto (80/20)** — which cities generate 80% of revenue
- **Z-Score Outlier** — anomalous deal values
- **Cohort Matrix** — Segment × Channel conversion heatmap
- **BCG Matrix** — product portfolio quadrant analysis
- **Linear Regression** — deal value predictors with R²
- **RFM Scoring** — Recency · Frequency · Monetary city segmentation

---

## 🛠️ Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/edukit-dashboard.git
cd edukit-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## ☁️ Deploy on Streamlit Community Cloud (Free)

1. Push this repo to GitHub (must be **public**)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **"New app"** → select your repo → set **Main file path** to `app.py`
4. Click **Deploy** — your app will be live in ~2 minutes ✅

---

## 📁 Project Structure

```
edukit-dashboard/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── .streamlit/
    └── config.toml     # Theme configuration
```

---

## 📤 Adding Your Own Data

Use the **sidebar uploader** to extend the dataset with a CSV file.

Required columns:
```
Lead_ID, City, Acquisition_Channel, Customer_Segment,
Product_Interest, Pipeline_Stage, Deal_Value_INR, NPS_Score
```

Pipeline stages must be one of:
`Lead | Prospect | Qualified | Proposal Sent | Closed Won | Closed Lost`

---

## 🔧 Tech Stack

- **[Streamlit](https://streamlit.io)** — UI framework
- **[Plotly](https://plotly.com/python/)** — interactive charts
- **[Pandas](https://pandas.pydata.org)** — data manipulation
- **[scikit-learn](https://scikit-learn.org)** — linear regression model
- **[NumPy](https://numpy.org)** — numerical operations

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*EduKit India · Business Validation Dashboard · FY 2026 · v19 → Streamlit*
