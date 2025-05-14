
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🛠️ Drilling Operations Monitoring Dashboard")

st.sidebar.header("Upload Drilling Sensor CSV")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:
    with st.spinner("Processing uploaded data..."):
        usecols = [
            'YYYY/MM/DD', 'HH:MM:SS',
            'Rate Of Penetration (ft_per_hr)', 'PLC ROP (ft_per_hr)',
            'Hook Load (klbs)', 'Standpipe Pressure (psi)',
            'Pump 1 strokes/min (SPM)', 'Pump 2 strokes/min (SPM)',
            'DAS Vibe Lateral Max (g_force)', 'DAS Vibe Axial Max (g_force)',
            'AutoDriller Limiting (unitless)',
            'DAS Vibe WOB Reduce (percent)', 'DAS Vibe RPM Reduce (percent)'
        ]

        df = pd.read_csv(uploaded_file, usecols=usecols)
        df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'], format='%m/%d/%Y %H:%M:%S')
        df.set_index('Timestamp', inplace=True)
        df.drop(columns=['YYYY/MM/DD', 'HH:MM:SS'], inplace=True)

        st.success("Data loaded successfully!")
        st.subheader("🔍 Preview of Uploaded Data")
        st.dataframe(df.head(10))

        tab1, tab2, tab3 = st.tabs(["📈 Monitoring Dashboard", "🚨 Alerts", "📊 Statistics"])

        with tab1:
            st.markdown("### Real-Time Sensor Trends")
            for col in df.columns:
                fig = px.line(df, x=df.index, y=col, title=col)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.markdown("### 🚨 Detected Alerts")
            alerts = []

            df['ROP_change'] = df['Rate Of Penetration (ft_per_hr)'].pct_change().abs()
            if df['ROP_change'].rolling('10min').mean().gt(0.5).any():
                alerts.append("Significant ROP fluctuation (>50% in 10 min) detected.")

            hl_issue = (df['Hook Load (klbs)'] > 60) &                        (df['Rate Of Penetration (ft_per_hr)'] < 1) &                        (df['Pump 1 strokes/min (SPM)'] == 0)
            if hl_issue.any():
                alerts.append("High hook load while pumps are off and ROP is near zero. Possible stuck pipe.")

            if df['DAS Vibe Lateral Max (g_force)'].gt(25).any():
                alerts.append("Excessive lateral vibration detected (>25g).")

            if df['AutoDriller Limiting (unitless)'].gt(0).any():
                alerts.append("AutoDriller limiting detected.")

            if df['DAS Vibe WOB Reduce (percent)'].gt(0).any() or df['DAS Vibe RPM Reduce (percent)'].gt(0).any():
                alerts.append("DAS vibration mitigation active.")

            if alerts:
                for alert in alerts:
                    st.error(alert)
            else:
                st.success("No critical alerts detected.")

        with tab3:
            st.markdown("### 📊 Statistical Summary")
            stats = df.describe().T[['mean', 'std', 'min', 'max']]
            st.dataframe(stats)

        st.sidebar.markdown("---")
        csv = df.to_csv().encode('utf-8')
        st.sidebar.download_button("Download Cleaned CSV", csv, "processed_data.csv")
