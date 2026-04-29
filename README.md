# 🗳️ California Proposition County Vote Map

Interactive Streamlit app for visualizing California county-level proposition vote percentages across all historical ballot measures.

## Features
- **Interactive County Map**: Choropleth visualization by county with hover details
- **Vote Analytics**: Distribution charts, median/std dev, top/bottom counties
- **Multi-Proposition Comparison**: Compare yes/no percentages across measures in the same year
- **County Search/Filter**: Find specific counties and sort results
- **Statewide Summary**: Total votes and percentages across all counties
- **Data Export**: Download results as CSV or Excel
- **Upload Custom Data**: Load your own proposition results CSV

## Quick Start

1. **Install dependencies:**
   ```bash
   cd ~/ca-prop-vote-map
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   streamlit run app.py
   ```

3. **Open in browser:** http://localhost:8501

## Tabs

### 🗺️ Map
- Interactive choropleth of California counties
- Color by Yes % or No %
- Statewide summary statistics
- County data table with search

### 📊 Analytics
- Vote distribution histogram across counties
- Top/bottom 10 counties by vote %
- Median and standard deviation
- Highest/lowest voting counties

### 🔄 Compare
- Select multiple propositions from the same year
- Box plots comparing vote distributions
- Side-by-side summary statistics

### 💾 Data
- Download county results as CSV or Excel
- Data format reference
- Validation help

## Data Format

Your CSV should have these columns:
```
year,proposition,measure_title,county,yes_pct,no_pct,yes_votes,no_votes,total_votes
2024,Proposition 1,Infrastructure Bond,Alameda,55.2,44.8,125000,102000,227000
2024,Proposition 1,Infrastructure Bond,Alpine,48.3,51.7,2500,2700,5200
```

**Column Details:**
- `year`: Election year (string, e.g., "2024")
- `proposition`: Prop number (e.g., "Proposition 1")
- `measure_title`: Full measure name
- `county`: California county name (must match GeoJSON, e.g., "Alameda", "Los Angeles")
- `yes_pct`: Yes percentage (0-100)
- `no_pct`: No percentage (0-100)
- `yes_votes`: Total yes votes (integer)
- `no_votes`: Total no votes (integer)
- `total_votes`: Total votes cast

## Data Sources

The sample data includes all 58 California counties for 5 sample propositions from 2018–2024. Use the `scripts/generate_data.py` utility to create or validate data:

```bash
# Generate sample data
python scripts/generate_data.py --sample

# Validate a CSV file
python scripts/generate_data.py --validate data/my_prop_data.csv
```

## Project Structure

```
ca-prop-vote-map/
├── app.py                    # Main Streamlit application
├── app_basic.py              # Basic version (archived)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── data/
│   ├── ca_counties.geojson   # County boundaries (58 CA counties)
│   └── ca_prop_votes.csv     # Sample proposition results
└── scripts/
    └── generate_data.py      # Utility for data generation/validation
```

## Geographic Data

County boundaries sourced from [Code for America's Click That Hood project](https://github.com/codeforamerica/click_that_hood). Includes all 58 California counties.

## Customization

### Change Colors
Edit `app.py` line ~65, change `color_continuous_scale`:
- `"RdYlGn"` (red-yellow-green for Yes %)
- `"Viridis"` (purple-green)
- `"Blues"` (single color scale)

### Add More Data
1. Prepare your CSV with the required columns
2. Upload via the sidebar file picker
3. Or replace `data/ca_prop_votes.csv` and reload

### Deploy
Deploy to Streamlit Cloud or Docker

## Notes
- County names must exactly match GeoJSON names
- Yes % and No % should sum to ~100
- All 58 counties recommended for complete map
- Year values stored as strings
