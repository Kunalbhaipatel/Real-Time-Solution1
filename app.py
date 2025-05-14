
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

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Monitoring Dashboard", "🚨 Alerts", "📊 Statistics", "⏱️ Alert Timeline", "🛢️ Shaker Performance"
        ])

        with tab1:
            st.markdown("### Real-Time Sensor Trends")
            for col in df.columns:
                fig = px.line(df, x=df.index, y=col, title=col)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.markdown("### 🚨 Detected Alerts")
            alerts = []
            alert_times = []

            df['ROP_change'] = df['Rate Of Penetration (ft_per_hr)'].pct_change().abs()
            rop_alerts = df[df['ROP_change'].rolling('10min').mean().gt(0.5)]
            if not rop_alerts.empty:
                alerts.append("Significant ROP fluctuation (>50% in 10 min) detected.")
                alert_times.append(rop_alerts.index[0])

            hl_issue = (df['Hook Load (klbs)'] > 60) &                        (df['Rate Of Penetration (ft_per_hr)'] < 1) &                        (df['Pump 1 strokes/min (SPM)'] == 0)
            if hl_issue.any():
                alerts.append("High hook load while pumps are off and ROP is near zero. Possible stuck pipe.")
                alert_times.append(df[hl_issue].index[0])

            vib_alert = df['DAS Vibe Lateral Max (g_force)'].gt(25)
            if vib_alert.any():
                alerts.append("Excessive lateral vibration detected (>25g).")
                alert_times.append(df[vib_alert].index[0])

            if alerts:
                for alert in alerts:
                    st.error(alert)
            else:
                st.success("No critical alerts detected.")

        with tab3:
            st.markdown("### 📊 Statistical Summary")
            stats = df.describe().T[['mean', 'std', 'min', 'max']]
            st.dataframe(stats)

        with tab4:
            st.markdown("### ⏱️ Alert Timeline")
            if alerts:
                timeline_df = pd.DataFrame({'Alert': alerts, 'Time': alert_times})
                st.dataframe(timeline_df)
            else:
                st.info("No alert timestamps available.")

        with tab5:
            st.markdown("### 🛢️ Shaker Performance (Mock Values)")
            df['Mock Shaker Load %'] = (df['PLC ROP (ft_per_hr)'] * 2).clip(0, 100)
            df['Mock Screen Occupancy'] = (df['DAS Vibe Lateral Max (g_force)'] * 3).clip(0, 100)
            df['Mock Overload Risk'] = ((df['Mock Shaker Load %'] > 80) & (df['Mock Screen Occupancy'] > 70)).astype(int)

            st.markdown("#### Shaker Load & Screen Status")
            st.line_chart(df[['Mock Shaker Load %', 'Mock Screen Occupancy']])

            st.markdown("#### Overload Risk (1 = Risk)")
            fig = px.scatter(df.reset_index(), x='Timestamp', y='Mock Overload Risk', color='Mock Overload Risk')
            st.plotly_chart(fig)

        st.sidebar.markdown("---")
        csv = df.to_csv().encode('utf-8')
        st.sidebar.download_button("Download Cleaned CSV", csv, "processed_data.csv")
