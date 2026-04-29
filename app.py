
import json
import os
from pathlib import Path
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GEOJSON_FILE = DATA_DIR / "ca_counties.geojson"
SAMPLE_DATA_FILE = DATA_DIR / "ca_prop_votes.csv"

st.set_page_config(
    page_title="California Proposition County Vote Map",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🗳️ California Proposition County Vote Map")
st.markdown(
    "Explore California county-level ballot measure percentages for every proposition ever. "
    "Visualize vote share by county, compare propositions, filter counties, and download results."
)

@st.cache_data
def load_geojson() -> dict:
    if GEOJSON_FILE.exists():
        with GEOJSON_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)

    st.warning("County GeoJSON file is missing locally. Attempting to load from GitHub...")
    import urllib.request

    url = (
        "https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
        "master/public/data/california-counties.geojson"
    )
    with urllib.request.urlopen(url) as response:
        return json.load(response)


@st.cache_data
def load_data(file_path: Path) -> pd.DataFrame:
    df = pd.read_csv(file_path, dtype={"county": str})
    df.columns = [c.strip() for c in df.columns]
    if "yes_pct" not in df.columns or "no_pct" not in df.columns:
        raise ValueError(
            "CSV must include 'yes_pct' and 'no_pct' columns with county vote percentages."
        )

    df = df.dropna(subset=["county"])
    df["county"] = df["county"].astype(str).str.strip()
    df["measure_title"] = df.get("measure_title", df.get("proposition", "")).astype(str)
    df["year"] = df["year"].astype(str)
    return df


def make_choropleth(df: pd.DataFrame, geojson: dict, color_col: str, title: str = "") -> px.choropleth_mapbox:
    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations="county",
        featureidkey="properties.name",
        color=color_col,
        hover_name="county",
        hover_data={
            "yes_pct": ":.1f",
            "no_pct": ":.1f",
            "yes_votes": ":,",
            "no_votes": ":,",
            "total_votes": ":,",
        },
        color_continuous_scale="RdYlGn" if color_col == "yes_pct" else "RdYlGn_r",
        range_color=(0, 100),
        mapbox_style="carto-positron",
        center={"lat": 37.2, "lon": -119.6},
        zoom=5.2,
        opacity=0.8,
        title=title,
    )
    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        height=600,
    )
    return fig


def statewide_summary(df: pd.DataFrame) -> dict:
    """Calculate statewide vote totals and percentages."""
    total_yes = df["yes_votes"].sum()
    total_no = df["no_votes"].sum()
    total = total_yes + total_no
    yes_pct = (total_yes / total * 100) if total > 0 else 0
    return {
        "yes_votes": int(total_yes),
        "no_votes": int(total_no),
        "total_votes": int(total),
        "yes_pct": round(yes_pct, 1),
        "no_pct": round(100 - yes_pct, 1),
    }


def make_county_distribution(df: pd.DataFrame, color_col: str) -> go.Figure:
    """Create a histogram of vote distribution across counties."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df[color_col],
        nbinsx=20,
        marker_color="steelblue",
        hovertemplate="<b>Vote %: %{x:.1f}</b><br>Counties: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Distribution of {color_col.replace('_', ' ').title()} Across Counties",
        xaxis_title=f"{color_col.replace('_', ' ').title()} (%)",
        yaxis_title="Number of Counties",
        height=400,
        showlegend=False,
    )
    return fig


def make_county_bar_chart(df: pd.DataFrame, color_col: str, top_n: int = 15) -> go.Figure:
    """Create a bar chart of top and bottom counties."""
    df_sorted = df.sort_values(color_col, ascending=False)
    top = df_sorted.head(top_n)
    bottom = df_sorted.tail(top_n)
    combined = pd.concat([top, bottom]).sort_values(color_col)
    
    colors = ["green" if x > 50 else "red" for x in combined[color_col]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=combined["county"],
        x=combined[color_col],
        orientation="h",
        marker_color=colors,
        hovertemplate="<b>%{y}</b><br>" + color_col.replace("_", " ").title() + ": %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=f"Top and Bottom {top_n} Counties by {color_col.replace('_', ' ').title()}",
        xaxis_title=f"{color_col.replace('_', ' ').title()} (%)",
        yaxis_title="County",
        height=500,
        showlegend=False,
    )
    return fig


def main():
    tab1, tab2, tab3, tab4 = st.tabs(["Map", "Analytics", "Compare", "Data"])
    
    # SIDEBAR DATA LOADING
    st.sidebar.header("📂 Dataset")
    custom_file = st.sidebar.file_uploader(
        "Upload a CSV of California proposition county results",
        type=["csv"],
    )

    if custom_file is not None:
        try:
            df = load_data(Path(custom_file.name))
        except Exception as e:
            st.sidebar.error(f"Error loading file: {e}")
            st.stop()
    elif SAMPLE_DATA_FILE.exists():
        df = load_data(SAMPLE_DATA_FILE)
    else:
        st.sidebar.error(
            "No data file found. Add a CSV named `ca_prop_votes.csv` under the `data/` folder "
            "or upload a file above."
        )
        st.stop()

    geojson = load_geojson()

    years = sorted(df["year"].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("📅 Election year", years)

    measures = (
        df[df["year"] == selected_year]["proposition"].astype(str).drop_duplicates().sort_values()
    )
    selected_measure = st.sidebar.selectbox("🗳️ Proposition", measures)

    side_pct = st.sidebar.radio("Color by", ["yes_pct", "no_pct"], format_func=lambda x: "Yes %" if x == "yes_pct" else "No %")

    selected_rows = df[
        (df["year"] == selected_year) & (df["proposition"] == selected_measure)
    ].copy()
    
    if selected_rows.empty:
        st.warning("No county results found for the selected year and proposition.")
        st.stop()

    selected_rows["yes_pct"] = pd.to_numeric(selected_rows["yes_pct"], errors="coerce")
    selected_rows["no_pct"] = pd.to_numeric(selected_rows["no_pct"], errors="coerce")
    selected_rows["yes_votes"] = pd.to_numeric(selected_rows.get("yes_votes", 0), errors="coerce")
    selected_rows["no_votes"] = pd.to_numeric(selected_rows.get("no_votes", 0), errors="coerce")
    selected_rows["total_votes"] = pd.to_numeric(selected_rows.get("total_votes", selected_rows["yes_votes"] + selected_rows["no_votes"]), errors="coerce")

    # TAB 1: MAP
    with tab1:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader(f"{selected_measure} — {selected_year}")
        with col2:
            st.metric("Measure Title", selected_rows['measure_title'].iloc[0][:30])
        with col3:
            st.metric("Counties Reporting", len(selected_rows))

        statewide = statewide_summary(selected_rows)
        st.markdown(f"**Statewide Results:** {statewide['yes_pct']}% Yes • {statewide['no_pct']}% No • {statewide['total_votes']:,} votes")

        fig = make_choropleth(selected_rows, geojson, side_pct, f"{side_pct.replace('_', ' ').title()} by County")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📊 Show county table"):
            county_display = selected_rows[
                ["county", "yes_pct", "no_pct", "yes_votes", "no_votes", "total_votes"]
            ].sort_values("yes_pct", ascending=False)
            
            search_col = st.columns([1, 3])[0]
            search_term = search_col.text_input("Search county:", "")
            if search_term:
                county_display = county_display[county_display["county"].str.contains(search_term, case=False, na=False)]
            
            st.dataframe(county_display, use_container_width=True)

    # TAB 2: ANALYTICS
    with tab2:
        st.subheader("Vote Distribution Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(make_county_distribution(selected_rows, "yes_pct"), use_container_width=True)
        with col2:
            st.metric("Median Yes %", f"{selected_rows['yes_pct'].median():.1f}%")
            st.metric("Std Dev", f"{selected_rows['yes_pct'].std():.1f}%")

        st.plotly_chart(make_county_bar_chart(selected_rows, "yes_pct", top_n=10), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Highest Yes %", f"{selected_rows['yes_pct'].max():.1f}% — {selected_rows.loc[selected_rows['yes_pct'].idxmax(), 'county']}")
        with col2:
            st.metric("Lowest Yes %", f"{selected_rows['yes_pct'].min():.1f}% — {selected_rows.loc[selected_rows['yes_pct'].idxmin(), 'county']}")

    # TAB 3: COMPARE PROPOSITIONS
    with tab3:
        st.subheader("Compare Multiple Propositions")
        compare_measures = st.multiselect(
            "Select propositions to compare (same year):",
            measures,
            default=[selected_measure],
        )

        if len(compare_measures) > 1:
            compare_df = df[(df["year"] == selected_year) & (df["proposition"].isin(compare_measures))].copy()
            compare_df["yes_pct"] = pd.to_numeric(compare_df["yes_pct"], errors="coerce")
            compare_df["yes_votes"] = pd.to_numeric(compare_df.get("yes_votes", 0), errors="coerce")
            compare_df["no_votes"] = pd.to_numeric(compare_df.get("no_votes", 0), errors="coerce")
            compare_df["total_votes"] = compare_df["yes_votes"] + compare_df["no_votes"]

            pivot_yes = compare_df.pivot_table(
                index="county",
                columns="proposition",
                values="yes_pct",
                aggfunc="first",
            )

            fig = go.Figure()
            for prop in pivot_yes.columns:
                fig.add_trace(go.Box(
                    y=pivot_yes[prop],
                    name=prop,
                    boxmean="sd",
                ))
            fig.update_layout(
                title="Distribution of Yes % Across Propositions",
                yaxis_title="Yes %",
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Comparison Table")
            comp_summary = []
            for prop in compare_measures:
                prop_data = df[(df["year"] == selected_year) & (df["proposition"] == prop)].copy()
                prop_data["yes_votes"] = pd.to_numeric(prop_data.get("yes_votes", 0), errors="coerce")
                prop_data["no_votes"] = pd.to_numeric(prop_data.get("no_votes", 0), errors="coerce")
                total_yes = prop_data["yes_votes"].sum()
                total_votes = total_yes + prop_data["no_votes"].sum()
                yes_pct = (total_yes / total_votes * 100) if total_votes > 0 else 0
                comp_summary.append({
                    "Proposition": prop,
                    "Statewide Yes %": round(yes_pct, 1),
                    "Counties": len(prop_data),
                    "Median County Yes %": round(prop_data["yes_pct"].median(), 1),
                })
            st.dataframe(pd.DataFrame(comp_summary), use_container_width=True)
        else:
            st.info("Select 2+ propositions to compare.")

    # TAB 4: DOWNLOAD
    with tab4:
        st.subheader("Download Results")
        
        download_format = st.radio("Format:", ["CSV", "Excel"])
        
        if download_format == "CSV":
            csv_data = selected_rows[
                ["county", "year", "proposition", "measure_title", "yes_pct", "no_pct", "yes_votes", "no_votes", "total_votes"]
            ].sort_values("county").to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=f"ca_prop_{selected_measure.replace(' ', '_')}_{selected_year}.csv",
                mime="text/csv",
            )
        else:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                selected_rows[
                    ["county", "year", "proposition", "measure_title", "yes_pct", "no_pct", "yes_votes", "no_votes", "total_votes"]
                ].sort_values("county").to_excel(writer, index=False, sheet_name="Results")
                
                summary_df = pd.DataFrame([statewide])
                summary_df.to_excel(writer, index=False, sheet_name="Summary")
            
            buffer.seek(0)
            st.download_button(
                label="📥 Download as Excel",
                data=buffer.getvalue(),
                file_name=f"ca_prop_{selected_measure.replace(' ', '_')}_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.markdown("---")
        st.markdown(
            "### How to use your own data\n"
            "Your CSV should include at least these columns: `year`, `proposition`, `measure_title`, `county`, `yes_pct`, `no_pct`, `yes_votes`, `no_votes`, `total_votes`. "
            "County names should match California county names in the GeoJSON file (e.g., `Alameda`, `Los Angeles`, `San Diego`)."
        )


if __name__ == "__main__":
    main()
