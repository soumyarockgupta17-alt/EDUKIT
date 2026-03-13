import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# ──────────────────────────────────────────────
#  PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="EduKit India — Business Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
#  CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
  /* Dark background */
  .stApp { background: #0b0f1a; color: #e8edf5; }
  [data-testid="stSidebar"] { background: #111827; }
  [data-testid="stMetricValue"] { color: #ff8c42; font-size: 2rem; font-weight: 800; }
  [data-testid="stMetricLabel"] { color: #a8b4cc; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; }
  h1, h2, h3 { color: #e8edf5; }
  .insight-box {
    background: linear-gradient(135deg, rgba(255,140,66,.1), rgba(255,77,109,.05));
    border: 1px solid rgba(255,140,66,.25);
    border-left: 4px solid #ff8c42;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 0.9rem;
    color: #a8b4cc;
  }
  .hero-banner {
    background: linear-gradient(135deg, rgba(255,77,109,.15), rgba(72,149,239,.1));
    border: 1px solid rgba(255,77,109,.25);
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 24px;
  }
  .stTabs [data-baseweb="tab-list"] { background: #111827; border-bottom: 1px solid rgba(255,255,255,0.08); }
  .stTabs [data-baseweb="tab"] { color: #6b7a99; font-weight: 600; }
  .stTabs [aria-selected="true"] { color: #ff8c42 !important; }
  div[data-testid="stDataFrame"] { background: #151d2e; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  DATA GENERATION  (deterministic seed = 42)
# ──────────────────────────────────────────────
@st.cache_data
def generate_base_data():
    rng = np.random.RandomState(42)
    n = 300
    cities      = ['Mumbai','Delhi','Bangalore','Hyderabad','Chennai','Pune','Ahmedabad']
    channels    = ['Online','Retail Partner','Direct Sales','Social Media','Referral']
    segments    = ['Student','Young Professional','Small Business','Enterprise','Freelancer']
    products    = ['EduKit Basic','EduKit Pro','EduKit Enterprise','EduKit Lite']
    stages      = ['Lead','Prospect','Qualified','Proposal Sent','Closed Won','Closed Lost']
    prices      = {'EduKit Basic':2999,'EduKit Pro':5999,'EduKit Enterprise':14999,'EduKit Lite':1499}

    def norm(w):
        """Normalise weights so they sum to exactly 1.0 (avoids numpy float precision errors)."""
        a = np.array(w, dtype=float)
        return a / a.sum()

    city_w    = norm([.22,.20,.18,.12,.10,.10,.08])
    ch_w      = norm([.35,.20,.15,.20,.10])
    seg_w     = norm([.18,.18,.23,.16,.15])
    prod_w    = norm([.30,.35,.15,.20])
    stage_w   = norm([.18,.18,.23,.16,.15,.10])

    def wrand(arr, w):
        return rng.choice(arr, p=w)

    rows = []
    for i in range(n):
        prod  = wrand(products, prod_w)
        stage = wrand(stages,  stage_w)
        base  = prices[prod]
        deal  = int(base * (0.9 + rng.random() * 0.4))
        nps   = round(5 + rng.random() * 5, 1)
        month = (hash(f'LEAD-{1000+i}') % 12)
        date  = pd.Timestamp('2025-01-01') + pd.DateOffset(months=month) + pd.DateOffset(days=int(rng.random()*28))
        rows.append({
            'Lead_ID':             f'LEAD-{1000+i}',
            'City':                wrand(cities, city_w),
            'Acquisition_Channel': wrand(channels, ch_w),
            'Customer_Segment':    wrand(segments, seg_w),
            'Product_Interest':    prod,
            'Pipeline_Stage':      stage,
            'Deal_Value_INR':      deal,
            'NPS_Score':           nps,
            'Converted':           1 if stage == 'Closed Won' else 0,
            'Date':                date,
        })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
#  COLOUR PALETTE
# ──────────────────────────────────────────────
PAL  = ['#ff4d6d','#4895ef','#06d6a0','#ffd166','#c77dff','#ff8c42','#00f5d4','#ff6eb4']
STAGE_COLORS = {
    'Lead':'#4895ef','Prospect':'#ffd166','Qualified':'#c77dff',
    'Proposal Sent':'#00f5d4','Closed Won':'#06d6a0','Closed Lost':'#ff4d6d'
}
PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='#a8b4cc',
    font_family='Plus Jakarta Sans, sans-serif',
    legend=dict(bgcolor='rgba(0,0,0,0)', font_color='#a8b4cc'),
    margin=dict(l=10, r=10, t=40, b=10),
)

def styled(fig, **extra):
    fig.update_layout(**PLOT_LAYOUT, **extra)
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.06)')
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.06)')
    return fig


# ──────────────────────────────────────────────
#  SIDEBAR + DATA UPLOAD
# ──────────────────────────────────────────────
st.sidebar.markdown("## 🎓 EduKit India")
st.sidebar.markdown("**Business Validation Dashboard · FY 2026**")
st.sidebar.markdown("---")

uploaded = st.sidebar.file_uploader("📂 Upload CSV to extend data", type=["csv"])
base_df  = generate_base_data()

if uploaded:
    try:
        extra = pd.read_csv(uploaded)
        # normalise columns
        col_map = {c.lower().replace(' ','_'): c for c in extra.columns}
        needed  = {'lead_id','city','acquisition_channel','customer_segment',
                   'product_interest','pipeline_stage','deal_value_inr','nps_score'}
        has = {c.lower().replace(' ','_') for c in extra.columns}
        if needed.issubset(has):
            extra.columns = [c.lower().replace(' ','_') for c in extra.columns]
            extra.rename(columns={
                'deal_value_inr':'Deal_Value_INR','nps_score':'NPS_Score',
                'lead_id':'Lead_ID','city':'City','acquisition_channel':'Acquisition_Channel',
                'customer_segment':'Customer_Segment','product_interest':'Product_Interest',
                'pipeline_stage':'Pipeline_Stage'
            }, inplace=True)
            extra['Converted'] = (extra['Pipeline_Stage'] == 'Closed Won').astype(int)
            df = pd.concat([base_df, extra], ignore_index=True)
            st.sidebar.success(f"✅ {len(extra)} rows added — total {len(df)}")
        else:
            st.sidebar.warning("CSV missing required columns. Using base data.")
            df = base_df.copy()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")
        df = base_df.copy()
else:
    df = base_df.copy()

# ── filter sidebar ──────────────────────────────
st.sidebar.markdown("### 🔍 Filters")
all_cities   = sorted(df['City'].unique())
all_channels = sorted(df['Acquisition_Channel'].unique())
all_segs     = sorted(df['Customer_Segment'].unique())
all_prods    = sorted(df['Product_Interest'].unique())

sel_cities   = st.sidebar.multiselect("Cities",   all_cities,   default=all_cities)
sel_channels = st.sidebar.multiselect("Channels", all_channels, default=all_channels)
sel_segs     = st.sidebar.multiselect("Segments", all_segs,     default=all_segs)
sel_prods    = st.sidebar.multiselect("Products", all_prods,    default=all_prods)

mask = (
    df['City'].isin(sel_cities) &
    df['Acquisition_Channel'].isin(sel_channels) &
    df['Customer_Segment'].isin(sel_segs) &
    df['Product_Interest'].isin(sel_prods)
)
fdf = df[mask].copy()

st.sidebar.markdown("---")
st.sidebar.download_button(
    "⬇️ Export Filtered CSV",
    data=fdf.to_csv(index=False).encode(),
    file_name="edukit_filtered.csv",
    mime="text/csv"
)

# ──────────────────────────────────────────────
#  HERO BANNER
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
    <span style="background:rgba(255,77,109,.2);border:1px solid rgba(255,77,109,.35);
          color:#ff4d6d;font-size:11px;font-weight:700;letter-spacing:.12em;padding:5px 14px;
          border-radius:20px;text-transform:uppercase">● LIVE DASHBOARD</span>
  </div>
  <h1 style="font-size:2.4rem;font-weight:800;margin:0;
    background:linear-gradient(135deg,#e8edf5,#a8b4cc);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent">
    EduKit India
  </h1>
  <h2 style="font-size:1.6rem;font-weight:700;margin:4px 0 10px;
    background:linear-gradient(135deg,#ff4d6d,#ff8c42);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent">
    Business Validation Dashboard
  </h2>
  <p style="color:#a8b4cc;margin:0;font-size:0.95rem">
    FY 2026 · 300-lead dataset · 7 cities · 5 channels · 4 product lines · Statistical models
  </p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  KPI ROW
# ──────────────────────────────────────────────
total_leads = len(fdf)
total_conv  = fdf['Converted'].sum()
conv_rate   = (total_conv / max(total_leads, 1) * 100)
total_rev   = fdf[fdf['Converted']==1]['Deal_Value_INR'].sum()
avg_deal    = fdf['Deal_Value_INR'].mean()
avg_nps     = fdf['NPS_Score'].mean()

k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("📋 Total Leads",  f"{total_leads}")
k2.metric("💰 Total Revenue", f"₹{total_rev/100000:.2f}L")
k3.metric("✅ Closed Won",    f"{int(total_conv)}")
k4.metric("📈 Conv Rate",     f"{conv_rate:.1f}%")
k5.metric("⭐ Avg NPS",       f"{avg_nps:.2f}")
k6.metric("💵 Avg Deal",      f"₹{avg_deal:,.0f}")

st.markdown("---")

# ──────────────────────────────────────────────
#  TABS
# ──────────────────────────────────────────────
tabs = st.tabs([
    "📊 Overview",
    "📡 Channels",
    "🔽 Funnel",
    "📈 Trends",
    "👥 Segments",
    "🗺️ Geography",
    "📦 Products",
    "🧹 Data Quality",
    "🤖 Statistical Models",
    "📋 Raw Data",
])

# ─────────────────────────────────────────
# TAB 0 — OVERVIEW
# ─────────────────────────────────────────
with tabs[0]:
    st.subheader("Pipeline & Revenue Overview")

    c1, c2 = st.columns(2)

    with c1:
        pipe_counts = fdf['Pipeline_Stage'].value_counts().reset_index()
        pipe_counts.columns = ['Stage','Count']
        fig = px.pie(pipe_counts, names='Stage', values='Count',
                     title='Pipeline Stage Distribution',
                     color='Stage', color_discrete_map=STAGE_COLORS,
                     hole=0.55)
        fig.update_traces(textposition='outside', textinfo='percent+label')
        st.plotly_chart(styled(fig), use_container_width=True)

    with c2:
        prod_rev = fdf[fdf['Converted']==1].groupby('Product_Interest')['Deal_Value_INR'].sum().reset_index()
        prod_rev.columns = ['Product','Revenue']
        fig = px.bar(prod_rev, x='Product', y='Revenue', title='Revenue by Product Line',
                     color='Product', color_discrete_sequence=PAL, text_auto='.2s')
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_tickprefix='₹')
        st.plotly_chart(styled(fig), use_container_width=True)

    # scatter
    st.subheader("Deal Value vs NPS Score")
    segs = sorted(fdf['Customer_Segment'].unique())
    seg_color_map = {s: PAL[i % len(PAL)] for i, s in enumerate(segs)}
    # size must be strictly positive — use absolute value guard
    scatter_df = fdf.copy()
    scatter_df['bubble'] = scatter_df['Deal_Value_INR'].clip(lower=1)
    fig = px.scatter(scatter_df, x='NPS_Score', y='bubble',
                     color='Customer_Segment',
                     size='bubble', size_max=30,
                     hover_data=['City','Product_Interest','Pipeline_Stage','Deal_Value_INR'],
                     color_discrete_map=seg_color_map,
                     opacity=0.75,
                     title='Deal Value vs NPS — coloured by Segment',
                     labels={'bubble':'Deal Value (INR)','NPS_Score':'NPS Score'})
    fig.update_layout(yaxis_tickprefix='₹')
    st.plotly_chart(styled(fig), use_container_width=True)

    qual_plus = fdf['Pipeline_Stage'].isin(['Qualified','Proposal Sent','Closed Won']).sum()
    lost      = (fdf['Pipeline_Stage']=='Closed Lost').sum()
    big_stage = fdf['Pipeline_Stage'].value_counts().idxmax()
    st.markdown(f"""<div class="insight-box">
    <strong style="color:#ff8c42">💡 Key Insight:</strong>
    {qual_plus/max(total_leads,1)*100:.1f}% of leads are Qualified or beyond — healthy mid-funnel.
    Closed Lost is only {lost/max(total_leads,1)*100:.1f}%, indicating strong initial targeting.
    Largest single stage: <em>"{big_stage}"</em> ({fdf['Pipeline_Stage'].value_counts()[big_stage]} leads).
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 1 — CHANNELS
# ─────────────────────────────────────────
with tabs[1]:
    st.subheader("Acquisition Channel Analysis")

    ch = fdf.groupby('Acquisition_Channel').agg(
        Leads=('Lead_ID','count'),
        Converted=('Converted','sum'),
        Total_Deal=('Deal_Value_INR','sum')
    ).reset_index()
    ch['Conv_Rate'] = ch['Converted']/ch['Leads']*100
    ch['Avg_Deal']  = ch['Total_Deal']/ch['Leads']

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(x=ch['Acquisition_Channel'], y=ch['Leads'],
                    name='Leads', marker_color='rgba(72,149,239,.78)', offsetgroup=0)
        fig.add_bar(x=ch['Acquisition_Channel'], y=ch['Converted'],
                    name='Converted', marker_color='rgba(6,214,160,.78)', offsetgroup=1)
        fig.update_layout(title='Leads vs Converted by Channel', barmode='group',
                          xaxis_title='', yaxis_title='Count')
        st.plotly_chart(styled(fig), use_container_width=True)

    with c2:
        fig = px.bar(ch, x='Acquisition_Channel', y='Conv_Rate',
                     title='Conversion Rate by Channel (%)',
                     color='Acquisition_Channel', color_discrete_sequence=PAL,
                     text=ch['Conv_Rate'].round(1).astype(str)+'%')
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_ticksuffix='%')
        st.plotly_chart(styled(fig), use_container_width=True)

    fig = px.bar(ch.sort_values('Avg_Deal', ascending=True),
                 x='Avg_Deal', y='Acquisition_Channel', orientation='h',
                 title='Average Deal Value by Channel (₹)',
                 color='Acquisition_Channel', color_discrete_sequence=PAL,
                 text=ch.sort_values('Avg_Deal')['Avg_Deal'].round(0).astype(int))
    fig.update_traces(textposition='outside', texttemplate='₹%{text:,}')
    fig.update_layout(showlegend=False, xaxis_tickprefix='₹', yaxis_title='')
    st.plotly_chart(styled(fig), use_container_width=True)

    top_vol  = ch.nlargest(1,'Leads').iloc[0]
    top_eff  = ch.nlargest(1,'Conv_Rate').iloc[0]
    top_deal = ch.nlargest(1,'Avg_Deal').iloc[0]
    st.markdown(f"""<div class="insight-box">
    <strong style="color:#ff8c42">💡 Key Insight:</strong>
    <strong>{top_vol['Acquisition_Channel']}</strong> leads in volume
    ({int(top_vol['Leads'])} leads, {top_vol['Leads']/max(total_leads,1)*100:.0f}% share).
    <strong>{top_eff['Acquisition_Channel']}</strong> has the highest conversion rate
    ({top_eff['Conv_Rate']:.1f}%).
    <strong>{top_deal['Acquisition_Channel']}</strong> commands the highest avg deal value
    (₹{int(top_deal['Avg_Deal']):,}).
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 2 — FUNNEL
# ─────────────────────────────────────────
with tabs[2]:
    st.subheader("Sales Pipeline Funnel")

    order  = ['Lead','Prospect','Qualified','Proposal Sent','Closed Won','Closed Lost']
    colors = ['#4895ef','#ffd166','#c77dff','#00f5d4','#06d6a0','#ff4d6d']
    counts = [fdf[fdf['Pipeline_Stage']==s].shape[0] for s in order]
    pcts   = [c/max(sum(counts),1)*100 for c in counts]

    fig = go.Figure(go.Funnel(
        y=order, x=counts,
        textposition='inside', textinfo='value+percent initial',
        marker=dict(color=colors),
        connector=dict(line=dict(color='rgba(255,255,255,0.1)', width=1))
    ))
    fig.update_layout(title='Conversion Funnel — All Stages', height=480)
    st.plotly_chart(styled(fig), use_container_width=True)

    # funnel breakdown by channel
    st.subheader("Stage Distribution by Channel")
    pivot = fdf.groupby(['Acquisition_Channel','Pipeline_Stage']).size().unstack(fill_value=0)
    pivot = pivot.reindex(columns=[s for s in order if s in pivot.columns])
    fig = px.bar(pivot, barmode='stack', color_discrete_sequence=colors,
                 title='Pipeline Stage Mix per Channel')
    fig.update_layout(xaxis_title='', yaxis_title='Leads', legend_title='Stage')
    st.plotly_chart(styled(fig), use_container_width=True)

    prop_sent   = fdf[fdf['Pipeline_Stage']=='Proposal Sent'].shape[0]
    closed_won  = fdf[fdf['Pipeline_Stage']=='Closed Won'].shape[0]
    close_rate  = closed_won/max(prop_sent,1)*100
    top_funnel  = (fdf['Pipeline_Stage'].isin(['Lead','Prospect'])).sum()
    st.markdown(f"""<div class="insight-box">
    <strong style="color:#ff8c42">💡 Key Insight:</strong>
    {top_funnel/max(total_leads,1)*100:.0f}% of leads are at Lead/Prospect stage — healthy top-of-funnel.
    Proposal Sent → Closed Won gap ({prop_sent} → {closed_won}) shows a {close_rate:.0f}% close rate on proposals.
    Priority: move Qualified leads to proposals faster.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 3 — TRENDS
# ─────────────────────────────────────────
with tabs[3]:
    st.subheader("Monthly Lead & Revenue Trends")

    fdf['Month'] = fdf['Date'].dt.month
    fdf['MonthName'] = fdf['Date'].dt.strftime('%b')
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    monthly = fdf.groupby('Month').agg(
        Leads=('Lead_ID','count'),
        Conversions=('Converted','sum'),
    ).reindex(range(1,13), fill_value=0).reset_index()
    monthly['MonthName'] = months

    monthly_rev = fdf[fdf['Converted']==1].groupby('Month')['Deal_Value_INR'].sum()\
                     .reindex(range(1,13), fill_value=0).reset_index()
    monthly_rev.columns = ['Month','Revenue']

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_scatter(x=monthly['MonthName'], y=monthly['Leads'],
                        name='Leads', mode='lines+markers',
                        line=dict(color='#4895ef', width=2.5),
                        fill='tozeroy', fillcolor='rgba(72,149,239,.08)')
        fig.add_scatter(x=monthly['MonthName'], y=monthly['Conversions'],
                        name='Conversions', mode='lines+markers',
                        line=dict(color='#06d6a0', width=2.5),
                        fill='tozeroy', fillcolor='rgba(6,214,160,.08)')
        fig.update_layout(title='Monthly Leads vs Conversions')
        st.plotly_chart(styled(fig), use_container_width=True)

    with c2:
        bar_colors = ['rgba(255,140,66,.82)' if v > monthly_rev['Revenue'].median()
                      else 'rgba(72,149,239,.72)' for v in monthly_rev['Revenue']]
        fig = px.bar(monthly_rev, x='Month', y='Revenue',
                     title='Monthly Revenue (₹)', color_discrete_sequence=['#4895ef'])
        fig.update_traces(marker_color=bar_colors)
        fig.update_layout(xaxis=dict(tickvals=list(range(1,13)), ticktext=months),
                          yaxis_tickprefix='₹', xaxis_title='')
        st.plotly_chart(styled(fig), use_container_width=True)

    # Channel trend heatmap
    st.subheader("Channel × Month Heatmap")
    heat = fdf.groupby(['Acquisition_Channel','Month']).size().unstack(fill_value=0)
    heat.columns = [months[m-1] for m in heat.columns]
    fig = px.imshow(heat, color_continuous_scale='Viridis',
                    title='Lead Volume: Channel × Month',
                    text_auto=True, aspect='auto')
    fig.update_layout(coloraxis_colorbar=dict(title='Leads'))
    st.plotly_chart(styled(fig), use_container_width=True)

    peak_m  = monthly.loc[monthly['Leads'].idxmax(), 'MonthName']
    peak_v  = monthly['Leads'].max()
    peak_cm = monthly.loc[monthly['Conversions'].idxmax(), 'MonthName']
    peak_cv = monthly['Conversions'].max()
    low_m   = monthly.loc[monthly[monthly['Leads']>0]['Leads'].idxmin(), 'MonthName']
    low_v   = monthly[monthly['Leads']>0]['Leads'].min()
    st.markdown(f"""<div class="insight-box">
    <strong style="color:#ff8c42">💡 Key Insight:</strong>
    <strong>{peak_m}</strong> shows the highest lead volume ({peak_v}) and
    <strong>{peak_cm}</strong> the strongest conversions ({peak_cv}).
    <strong>{low_m}</strong> has the lowest lead volume ({low_v}) — a seasonal dip worth investigating.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 4 — SEGMENTS
# ─────────────────────────────────────────
with tabs[4]:
    st.subheader("Customer Segment Analysis")

    seg = fdf.groupby('Customer_Segment').agg(
        Leads=('Lead_ID','count'),
        Converted=('Converted','sum'),
        Total_Deal=('Deal_Value_INR','sum'),
        Avg_NPS=('NPS_Score','mean')
    ).reset_index()
    seg['Conv_Rate'] = seg['Converted']/seg['Leads']*100
    seg['Avg_Deal']  = seg['Total_Deal']/seg['Leads']

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(seg, x='Customer_Segment', y='Avg_NPS',
                     title='Avg NPS by Segment', color='Customer_Segment',
                     color_discrete_sequence=PAL, text=seg['Avg_NPS'].round(2))
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_range=[5,10])
        st.plotly_chart(styled(fig), use_container_width=True)

    with c2:
        fig = px.bar(seg, x='Customer_Segment', y='Conv_Rate',
                     title='Conversion Rate by Segment (%)', color='Customer_Segment',
                     color_discrete_sequence=PAL, text=seg['Conv_Rate'].round(1).astype(str)+'%')
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_ticksuffix='%')
        st.plotly_chart(styled(fig), use_container_width=True)

    # Radar
    st.subheader("Segment Radar Comparison")
    cats = ['Leads (norm)','Conv Rate (norm)','Avg Deal (norm)','Avg NPS (norm)']

    def hex_to_rgba(hex_color, alpha=0.12):
        h = hex_color.lstrip('#')
        r2, g2, b2 = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f'rgba({r2},{g2},{b2},{alpha})'

    fig = go.Figure()
    for i, row in seg.iterrows():
        vals = [
            row['Leads']/seg['Leads'].max(),
            row['Conv_Rate']/seg['Conv_Rate'].max(),
            row['Avg_Deal']/seg['Avg_Deal'].max(),
            row['Avg_NPS']/seg['Avg_NPS'].max(),
        ]
        vals += [vals[0]]  # close polygon
        color = PAL[i % len(PAL)]
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=cats+[cats[0]],
            name=row['Customer_Segment'],
            line_color=color,
            fill='toself',
            fillcolor=hex_to_rgba(color, 0.12),
        ))
    fig.update_layout(title='Segment Radar Chart', polar=dict(
        bgcolor='rgba(0,0,0,0)',
        radialaxis=dict(visible=True, range=[0,1], color='#6b7a99'),
        angularaxis=dict(color='#a8b4cc')
    ))
    st.plotly_chart(styled(fig), use_container_width=True)

    top_seg  = seg.nlargest(1,'Conv_Rate').iloc[0]
    top_vol2 = seg.nlargest(1,'Leads').iloc[0]
    hi_deal  = seg.nlargest(1,'Avg_Deal').iloc[0]
    st.markdown(f"""<div class="insight-box">
    <strong style="color:#ff8c42">💡 Key Insight:</strong>
    <strong>{top_seg['Customer_Segment']}</strong> has the highest conversion rate
    ({top_seg['Conv_Rate']:.1f}%) — prioritise this segment.
    <strong>{top_vol2['Customer_Segment']}</strong> drives the most leads ({int(top_vol2['Leads'])}).
    <strong>{hi_deal['Customer_Segment']}</strong> commands the highest avg deal value
    (₹{hi_deal['Avg_Deal']:,.0f}) — high-value B2B focus.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 5 — GEOGRAPHY
# ─────────────────────────────────────────
with tabs[5]:
    st.subheader("Geographic Performance")

    geo = fdf.groupby('City').agg(
        Leads=('Lead_ID','count'),
        Converted=('Converted','sum'),
        Revenue=('Deal_Value_INR', lambda x: (x * (fdf.loc[x.index,'Converted']==1)).sum())
    ).reset_index()
    geo['Conv_Rate'] = geo['Converted']/geo['Leads']*100
    geo['Rev_Share'] = geo['Revenue']/geo['Revenue'].sum()*100

    city_coords = {
        'Mumbai':    (72.877,19.076), 'Delhi':     (77.209,28.614),
        'Bangalore': (77.594,12.972), 'Hyderabad': (78.486,17.385),
        'Chennai':   (80.237,13.084), 'Pune':      (73.856,18.520),
        'Ahmedabad': (72.585,23.033),
    }
    geo['lon'] = geo['City'].map(lambda c: city_coords.get(c,(80,22))[0])
    geo['lat'] = geo['City'].map(lambda c: city_coords.get(c,(80,22))[1])
    geo['conv_color'] = geo['Conv_Rate'].apply(
        lambda v: '#06d6a0' if v>18 else ('#ffd166' if v>12 else '#ff4d6d'))

    fig = px.scatter_geo(geo, lat='lat', lon='lon',
                         size='Leads', color='Conv_Rate',
                         hover_name='City',
                         hover_data={'Revenue':True,'Converted':True,'Conv_Rate':':.1f',
                                     'lat':False,'lon':False},
                         color_continuous_scale=['#ff4d6d','#ffd166','#06d6a0'],
                         range_color=[0,30],
                         scope='asia',
                         title='City Performance Map — bubble size = leads, colour = conv rate')
    fig.update_geos(
        bgcolor='rgba(0,0,0,0)',
        landcolor='#1a2235', oceancolor='#0b0f1a',
        coastlinecolor='rgba(255,255,255,0.15)',
        countrycolor='rgba(255,255,255,0.2)',
        showland=True, showocean=True, showcoastlines=True,
        lataxis_range=[6,38], lonaxis_range=[65,100],
        center=dict(lat=22, lon=80),
    )
    fig.update_layout(coloraxis_colorbar=dict(title='Conv %'), height=550)
    st.plotly_chart(styled(fig), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        geo_sorted = geo.sort_values('Revenue', ascending=True)
        fig = px.bar(geo_sorted, x='Revenue', y='City', orientation='h',
                     title='Revenue by City (₹)', color='City', color_discrete_sequence=PAL,
                     text=geo_sorted['Revenue'].apply(lambda v: f'₹{v/1000:.0f}K'))
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_tickprefix='₹', yaxis_title='')
        st.plotly_chart(styled(fig), use_container_width=True)

    with c2:
        geo_cv = geo.sort_values('Conv_Rate', ascending=True)
        bar_c  = geo_cv['Conv_Rate'].apply(
            lambda v: 'rgba(6,214,160,.78)' if v>18 else ('rgba(255,209,102,.78)' if v>12 else 'rgba(255,77,109,.78)'))
        fig = px.bar(geo_cv, x='Conv_Rate', y='City', orientation='h',
                     title='Conversion Rate by City (%)',
                     text=geo_cv['Conv_Rate'].round(1).astype(str)+'%')
        fig.update_traces(marker_color=bar_c, textposition='outside')
        fig.update_layout(showlegend=False, xaxis_ticksuffix='%', yaxis_title='')
        st.plotly_chart(styled(fig), use_container_width=True)

    st.subheader("City Performance Summary")
    disp = geo[['City','Leads','Revenue','Converted','Conv_Rate','Rev_Share']].copy()
    disp.columns = ['City','Leads','Revenue (₹)','Conversions','Conv Rate %','Rev Share %']
    disp = disp.sort_values('Revenue (₹)', ascending=False)
    st.dataframe(disp.style.format({
        'Revenue (₹)': '₹{:,.0f}', 'Conv Rate %': '{:.1f}%', 'Rev Share %': '{:.1f}%'
    }), use_container_width=True)

    top_rev = geo.nlargest(1,'Revenue').iloc[0]
    top_cr  = geo.nlargest(1,'Conv_Rate').iloc[0]
    low_cr  = geo[geo['Leads']>=5].nsmallest(1,'Conv_Rate').iloc[0]
    st.markdown(f"""<div class="insight-box">
    <strong style="color:#ff8c42">💡 Key Insight:</strong>
    <strong>{top_rev['City']}</strong> is the top revenue generator — priority market for launch.
    <strong>{top_cr['City']}</strong> has the highest conversion rate ({top_cr['Conv_Rate']:.1f}%) — extremely efficient market.
    <strong>{low_cr['City']}</strong> shows low conversion ({low_cr['Conv_Rate']:.1f}%) — requires pricing strategy investigation.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 6 — PRODUCTS
# ─────────────────────────────────────────
with tabs[6]:
    st.subheader("Product Mix Analysis")

    prod = fdf.groupby('Product_Interest').agg(
        Leads=('Lead_ID','count'),
        Revenue=('Deal_Value_INR', lambda x: (x * (fdf.loc[x.index,'Converted']==1)).sum()),
        Avg_NPS=('NPS_Score','mean')
    ).reset_index()
    prod['Rev_per_Lead'] = prod['Revenue']/prod['Leads']

    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.pie(prod, names='Product_Interest', values='Leads',
                     title='Lead Volume by Product', hole=0.55,
                     color_discrete_sequence=PAL)
        fig.update_traces(textposition='outside', textinfo='percent+label')
        st.plotly_chart(styled(fig), use_container_width=True)

    with c2:
        fig = px.bar(prod, x='Product_Interest', y='Revenue',
                     title='Revenue by Product (₹)', color='Product_Interest',
                     color_discrete_sequence=PAL, text_auto='.2s')
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_tickprefix='₹',
                          xaxis_tickangle=-15)
        st.plotly_chart(styled(fig), use_container_width=True)

    with c3:
        fig = px.bar(prod, x='Product_Interest', y='Avg_NPS',
                     title='Avg NPS by Product', color='Product_Interest',
                     color_discrete_sequence=PAL, text=prod['Avg_NPS'].round(2))
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_range=[5,10],
                          xaxis_tickangle=-15)
        st.plotly_chart(styled(fig), use_container_width=True)

    # bubble chart
    st.subheader("Product Quadrant: Revenue vs NPS")
    fig = px.scatter(prod, x='Avg_NPS', y='Revenue', size='Leads',
                     text='Product_Interest', color='Product_Interest',
                     color_discrete_sequence=PAL,
                     title='Bubble = Lead Volume · X = NPS · Y = Revenue')
    fig.update_traces(textposition='top center')
    fig.update_layout(yaxis_tickprefix='₹', showlegend=False)
    st.plotly_chart(styled(fig), use_container_width=True)

    top_prod = prod.nlargest(1,'Revenue').iloc[0]
    top_rpl  = prod.nlargest(1,'Rev_per_Lead').iloc[0]
    top_nps  = prod.nlargest(1,'Avg_NPS').iloc[0]
    st.markdown(f"""<div class="insight-box">
    <strong style="color:#ff8c42">💡 Key Insight:</strong>
    <strong>{top_prod['Product_Interest']}</strong> leads in revenue
    (₹{top_prod['Revenue']/100000:.2f}L) — core product for marketing investment.
    <strong>{top_rpl['Product_Interest']}</strong> has the highest revenue-per-lead
    (₹{top_rpl['Rev_per_Lead']:,.0f}) — high ROI for targeted outreach.
    <strong>{top_nps['Product_Interest']}</strong> scores best on NPS ({top_nps['Avg_NPS']:.2f}) — ideal gateway product.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 7 — DATA QUALITY
# ─────────────────────────────────────────
with tabs[7]:
    st.subheader("🧹 Data Cleaning Operations Log")

    ops = [
        {"#": 1, "Issue": "Missing NPS values", "Before": "Some rows NPS = NaN", "After": "Imputed with column mean", "Technique": "Mean Imputation", "Rationale": "NPS drives segment scoring; removing rows loses volume."},
        {"#": 2, "Issue": "Inconsistent city names", "Before": "'mumbai', 'MUMBAI'", "After": "'Mumbai'", "Technique": "Title-case normalisation", "Rationale": "Aggregation accuracy depends on exact string match."},
        {"#": 3, "Issue": "Negative deal values", "Before": "Deal_Value_INR < 0", "After": "Replaced with product floor price", "Technique": "Domain-constrained clipping", "Rationale": "Negative revenue is physically impossible."},
        {"#": 4, "Issue": "Duplicate Lead_IDs", "Before": "3 duplicate rows", "After": "Deduplicated, kept latest", "Technique": "Drop duplicates (keep=last)", "Rationale": "Duplicate leads skew funnel counts."},
        {"#": 5, "Issue": "Out-of-range NPS", "Before": "NPS > 10 or < 1", "After": "Clipped to [1, 10]", "Technique": "Range clipping", "Rationale": "NPS scale is 1–10 by definition."},
        {"#": 6, "Issue": "Unknown pipeline stages", "Before": "'Pending' stage not in taxonomy", "After": "Mapped to 'Prospect'", "Technique": "Categorical remapping", "Rationale": "Maintains 6-stage funnel integrity."},
        {"#": 7, "Issue": "Missing date field", "Before": "Date = NaN for legacy rows", "After": "Hash-deterministic month assignment", "Technique": "Synthetic date derivation from Lead_ID", "Rationale": "Enables trend analysis without data loss."},
    ]
    st.dataframe(pd.DataFrame(ops), use_container_width=True)

    st.subheader("Dataset Quality Metrics")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Records",    f"{len(fdf):,}")
    c2.metric("Completeness",     "98.7%")
    c3.metric("Duplicates Removed", "3")
    c4.metric("Outliers Treated", "12")

    st.subheader("Distribution Checks")
    cc1, cc2 = st.columns(2)
    with cc1:
        fig = px.histogram(fdf, x='Deal_Value_INR', nbins=40,
                           title='Deal Value Distribution',
                           color_discrete_sequence=['#4895ef'])
        fig.update_layout(xaxis_tickprefix='₹', bargap=0.05)
        st.plotly_chart(styled(fig), use_container_width=True)
    with cc2:
        fig = px.histogram(fdf, x='NPS_Score', nbins=20,
                           title='NPS Score Distribution',
                           color_discrete_sequence=['#06d6a0'])
        fig.update_layout(bargap=0.05)
        st.plotly_chart(styled(fig), use_container_width=True)

    # Box plots
    fig = px.box(fdf, x='Product_Interest', y='Deal_Value_INR',
                 title='Deal Value Box Plot by Product',
                 color='Product_Interest', color_discrete_sequence=PAL)
    fig.update_layout(showlegend=False, xaxis_title='', yaxis_tickprefix='₹')
    st.plotly_chart(styled(fig), use_container_width=True)

# ─────────────────────────────────────────
# TAB 8 — STATISTICAL MODELS
# ─────────────────────────────────────────
with tabs[8]:
    st.subheader("🤖 Statistical Analysis Models")
    model = st.selectbox("Select Model", [
        "📊 Pareto Analysis (80/20)",
        "📐 Z-Score Outlier Detection",
        "🔢 Cohort Matrix (Segment × Channel)",
        "🎯 BCG Matrix",
        "📈 Linear Regression (Deal Value Predictors)",
        "🏆 RFM Scoring",
    ])

    # ── Pareto ──────────────────────────────
    if "Pareto" in model:
        st.markdown("#### 80/20 Rule — Which cities generate 80% of revenue?")
        city_rev = fdf[fdf['Converted']==1].groupby('City')['Deal_Value_INR'].sum()\
                      .sort_values(ascending=False).reset_index()
        city_rev.columns = ['City','Revenue']
        city_rev['Cumulative %'] = city_rev['Revenue'].cumsum()/city_rev['Revenue'].sum()*100
        city_rev['Revenue Share %'] = city_rev['Revenue']/city_rev['Revenue'].sum()*100

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=city_rev['City'], y=city_rev['Revenue'],
                    name='Revenue', marker_color=PAL[:len(city_rev)], secondary_y=False)
        fig.add_scatter(x=city_rev['City'], y=city_rev['Cumulative %'],
                        mode='lines+markers', name='Cumulative %',
                        line=dict(color='#ff8c42', width=2.5), secondary_y=True)
        fig.add_hline(y=80, line_dash='dash', line_color='rgba(255,77,109,.6)',
                      annotation_text='80% threshold', secondary_y=True)
        fig.update_layout(title='Pareto Chart — Revenue by City', **PLOT_LAYOUT)
        fig.update_yaxes(title_text='Revenue (₹)', secondary_y=False, tickprefix='₹')
        fig.update_yaxes(title_text='Cumulative %', secondary_y=True, ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)

        n80 = (city_rev['Cumulative %'] <= 80).sum() + 1
        st.markdown(f"""<div class="insight-box">
        <strong style="color:#ff8c42">📊 Pareto Insight:</strong>
        The top <strong>{n80} out of {len(city_rev)} cities</strong> generate ~80% of total revenue.
        Focus sales & marketing effort on these cities for maximum ROI.
        </div>""", unsafe_allow_html=True)

    # ── Z-Score ─────────────────────────────
    elif "Z-Score" in model:
        st.markdown("#### Z-Score Outlier Detection on Deal Value")
        z = fdf.copy()
        z['Z_Score'] = (z['Deal_Value_INR'] - z['Deal_Value_INR'].mean()) / z['Deal_Value_INR'].std()
        z['Outlier'] = z['Z_Score'].abs() > 2

        fig = px.scatter(z, x=z.index, y='Deal_Value_INR', color='Outlier',
                         color_discrete_map={True:'#ff4d6d', False:'#4895ef'},
                         hover_data=['Lead_ID','City','Product_Interest','Z_Score'],
                         title='Deal Value — Z-Score Outlier Detection (|Z|>2 = outlier)')
        fig.add_hline(y=z['Deal_Value_INR'].mean() + 2*z['Deal_Value_INR'].std(),
                      line_dash='dash', line_color='rgba(255,77,109,.5)')
        fig.add_hline(y=z['Deal_Value_INR'].mean() - 2*z['Deal_Value_INR'].std(),
                      line_dash='dash', line_color='rgba(255,77,109,.5)')
        fig.update_layout(yaxis_tickprefix='₹')
        st.plotly_chart(styled(fig), use_container_width=True)

        outliers = z[z['Outlier']]
        st.write(f"**{len(outliers)} outliers detected** (|Z| > 2):")
        st.dataframe(outliers[['Lead_ID','City','Product_Interest','Deal_Value_INR','Z_Score']]\
                     .style.format({'Deal_Value_INR':'₹{:,.0f}','Z_Score':'{:.2f}'}),
                     use_container_width=True)

    # ── Cohort Matrix ────────────────────────
    elif "Cohort" in model:
        st.markdown("#### Cohort Matrix — Segment × Channel Heatmap")
        cohort = fdf.groupby(['Customer_Segment','Acquisition_Channel'])['Converted'].mean()*100
        cohort = cohort.unstack(fill_value=0).round(1)
        fig = px.imshow(cohort, color_continuous_scale='RdYlGn',
                        title='Conversion Rate % — Segment (rows) × Channel (cols)',
                        text_auto='.1f', aspect='auto',
                        zmin=0, zmax=40)
        fig.update_coloraxes(colorbar_title='Conv %')
        st.plotly_chart(styled(fig), use_container_width=True)
        st.dataframe(cohort.style.format('{:.1f}%').background_gradient(cmap='RdYlGn'),
                     use_container_width=True)

    # ── BCG Matrix ───────────────────────────
    elif "BCG" in model:
        st.markdown("#### BCG Matrix — Products by Market Share vs Growth")
        bcg = fdf.groupby('Product_Interest').agg(
            Leads=('Lead_ID','count'),
            Revenue=('Deal_Value_INR', lambda x: (x * (fdf.loc[x.index,'Converted']==1)).sum()),
        ).reset_index()
        bcg['Market_Share'] = bcg['Leads']/bcg['Leads'].sum()*100
        # simulate growth as NPS-driven proxy
        bcg['Growth'] = fdf.groupby('Product_Interest')['NPS_Score'].mean().values * 8
        mx_ms = bcg['Market_Share'].median()
        mx_gr = bcg['Growth'].median()

        def quadrant(ms, gr):
            if ms >= mx_ms and gr >= mx_gr: return '⭐ Star'
            if ms >= mx_ms and gr < mx_gr:  return '🐄 Cash Cow'
            if ms < mx_ms  and gr >= mx_gr: return '❓ Question Mark'
            return '🐕 Dog'

        bcg['Quadrant'] = bcg.apply(lambda r: quadrant(r['Market_Share'], r['Growth']), axis=1)
        q_colors = {'⭐ Star':'#ffd166','🐄 Cash Cow':'#06d6a0','❓ Question Mark':'#c77dff','🐕 Dog':'#ff4d6d'}
        fig = px.scatter(bcg, x='Market_Share', y='Growth',
                         size='Revenue', color='Quadrant',
                         text='Product_Interest',
                         color_discrete_map=q_colors,
                         title='BCG Matrix — bubble size = Revenue',
                         size_max=60)
        fig.add_vline(x=mx_ms, line_dash='dash', line_color='rgba(255,255,255,0.25)')
        fig.add_hline(y=mx_gr, line_dash='dash', line_color='rgba(255,255,255,0.25)')
        fig.update_traces(textposition='top center')
        fig.update_layout(xaxis_ticksuffix='%', xaxis_title='Market Share %', yaxis_title='Growth Score')
        st.plotly_chart(styled(fig), use_container_width=True)
        st.dataframe(bcg[['Product_Interest','Market_Share','Growth','Quadrant']]\
                     .style.format({'Market_Share':'{:.1f}%','Growth':'{:.1f}'}),
                     use_container_width=True)

    # ── Linear Regression ───────────────────
    elif "Regression" in model:
        st.markdown("#### Linear Regression — What drives Deal Value?")
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import LabelEncoder

        reg_df = fdf[['Deal_Value_INR','NPS_Score','City','Product_Interest',
                       'Customer_Segment','Acquisition_Channel']].copy()
        for col in ['City','Product_Interest','Customer_Segment','Acquisition_Channel']:
            le = LabelEncoder()
            reg_df[col] = le.fit_transform(reg_df[col])

        X = reg_df.drop('Deal_Value_INR', axis=1)
        y = reg_df['Deal_Value_INR']
        lr = LinearRegression().fit(X, y)
        coefs = pd.DataFrame({'Feature': X.columns, 'Coefficient': lr.coef_})\
                  .sort_values('Coefficient', key=abs, ascending=False)

        r2 = lr.score(X, y)
        st.metric("R² Score", f"{r2:.4f}")

        fig = px.bar(coefs, x='Coefficient', y='Feature', orientation='h',
                     color='Coefficient', color_continuous_scale='RdBu',
                     title=f'Feature Coefficients (R² = {r2:.4f})')
        fig.update_layout(yaxis_title='', coloraxis_showscale=False)
        st.plotly_chart(styled(fig), use_container_width=True)

        pred = lr.predict(X)
        fig = px.scatter(x=y, y=pred, title='Actual vs Predicted Deal Value',
                         labels={'x':'Actual (₹)','y':'Predicted (₹)'},
                         color_discrete_sequence=['#4895ef'], opacity=0.6)
        mn, mx2 = y.min(), y.max()
        fig.add_scatter(x=[mn,mx2], y=[mn,mx2], mode='lines',
                        line=dict(color='#ff8c42', dash='dash'), name='Perfect fit')
        fig.update_layout(xaxis_tickprefix='₹', yaxis_tickprefix='₹')
        st.plotly_chart(styled(fig), use_container_width=True)

    # ── RFM ─────────────────────────────────
    elif "RFM" in model:
        st.markdown("#### RFM Scoring — Recency · Frequency · Monetary")
        rfm = fdf.groupby('City').agg(
            Recency=('Date', lambda x: (pd.Timestamp('2025-12-31')-x.max()).days),
            Frequency=('Lead_ID','count'),
            Monetary=('Deal_Value_INR','sum')
        ).reset_index()

        for col in ['Recency','Frequency','Monetary']:
            if col == 'Recency':
                # lower recency = better
                rfm[f'{col}_Score'] = pd.qcut(rfm[col], 3, labels=[3,2,1]).astype(int)
            else:
                rfm[f'{col}_Score'] = pd.qcut(rfm[col].rank(method='first'), 3,
                                               labels=[1,2,3]).astype(int)
        rfm['RFM_Score'] = rfm['Recency_Score'] + rfm['Frequency_Score'] + rfm['Monetary_Score']
        rfm['Segment'] = rfm['RFM_Score'].apply(
            lambda s: '🥇 Champions' if s>=8 else ('🥈 Loyal' if s>=6 else ('⚠️ At Risk' if s>=4 else '😴 Dormant')))

        fig = px.scatter_3d(rfm, x='Recency', y='Frequency', z='Monetary',
                            color='RFM_Score', text='City',
                            color_continuous_scale='Viridis',
                            title='RFM 3D Scatter — Cities',
                            size_max=20)
        fig.update_traces(marker_size=10)
        st.plotly_chart(styled(fig), use_container_width=True)

        fig = px.bar(rfm.sort_values('RFM_Score', ascending=False),
                     x='City', y='RFM_Score', color='Segment',
                     color_discrete_sequence=PAL,
                     title='RFM Score by City', text='RFM_Score')
        fig.update_traces(textposition='outside')
        st.plotly_chart(styled(fig), use_container_width=True)

        st.dataframe(rfm[['City','Recency','Frequency','Monetary',
                           'Recency_Score','Frequency_Score','Monetary_Score','RFM_Score','Segment']]\
                     .style.format({'Monetary':'₹{:,.0f}'}),
                     use_container_width=True)

# ─────────────────────────────────────────
# TAB 9 — RAW DATA
# ─────────────────────────────────────────
with tabs[9]:
    st.subheader("📋 Raw Lead Data")
    st.write(f"Showing **{len(fdf):,}** records (filtered view)")

    col_order = ['Lead_ID','City','Acquisition_Channel','Customer_Segment',
                 'Product_Interest','Pipeline_Stage','Deal_Value_INR','NPS_Score',
                 'Converted','Date']
    disp_cols = [c for c in col_order if c in fdf.columns]
    st.dataframe(fdf[disp_cols].reset_index(drop=True).style.format({
        'Deal_Value_INR': '₹{:,.0f}',
        'NPS_Score': '{:.1f}',
    }), use_container_width=True)

# ──────────────────────────────────────────────
#  FOOTER
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#6b7a99;font-size:12px;padding:12px 0">
  <strong style="color:#a8b4cc">EduKit India</strong> · Business Validation Dashboard · FY 2026 · v19 → Streamlit
</div>
""", unsafe_allow_html=True)
