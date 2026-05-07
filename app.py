import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Nairobi Property Market Analyzer", layout="wide")
st.title("Nairobi Property Market Analyzer")
st.caption("Interactive dashboard — explore prices, rents, and yields across Nairobi.")


@st.cache_data
def load_data():
    conn = sqlite3.connect("data/property.db")
    df = pd.read_sql_query("SELECT * FROM listings", conn)
    conn.close()
    lookup = pd.read_csv("data/processed/neighborhood_to_subcounty.csv", comment="#")
    df = df.merge(lookup[["neighborhood", "sub_county"]], on="neighborhood", how="left")
    df["date_published"] = pd.to_datetime(df["date_published"]).dt.tz_localize(None)
    today = pd.Timestamp.now()
    df["days_old"] = (today - df["date_published"]).dt.days
    df["freshness"] = pd.cut(
        df["days_old"], bins=[-1, 30, 90, 100000],
        labels=["🟢 Fresh", "🟡 Possibly stale", "🔴 Probably gone"],
    )
    return df


@st.cache_data
def load_geojson():
    with open("data/geo/nairobi_sub_counties.geojson") as f:
        return json.load(f)


df = load_data()
geojson = load_geojson()
all_sub_counties = [f["properties"]["sub_county"] for f in geojson["features"]]

# --- Sidebar filters ---
st.sidebar.header("Filters")
types = st.sidebar.multiselect("Type", ["sale", "rent"], default=["sale", "rent"])

all_neighborhoods = sorted(df["neighborhood"].unique())
selected = st.sidebar.multiselect(
    "Neighborhoods", options=all_neighborhoods, default=all_neighborhoods
)
bedroom_range = st.sidebar.slider("Bedrooms", 1, 10, (1, 10))
furnished_filter = st.sidebar.selectbox(
    "Furnished", ["All", "Furnished only", "Unfurnished only"]
)

# Apply non-neighborhood filters first (used by Map View + Price Analysis)
city_wide = df[df["type"].isin(types)]
city_wide = city_wide[
    (city_wide["bedrooms"] >= bedroom_range[0]) & (city_wide["bedrooms"] <= bedroom_range[1])
]
if furnished_filter == "Furnished only":
    city_wide = city_wide[city_wide["furnished"] == 1]
elif furnished_filter == "Unfurnished only":
    city_wide = city_wide[city_wide["furnished"] == 0]

# Then apply neighborhood filter (used by Overview + Browse Listings)
filtered = city_wide.copy()
if selected:
    filtered = filtered[filtered["neighborhood"].isin(selected)]

st.sidebar.markdown(f"**Filtered: {len(filtered)} listings**")
st.sidebar.caption("Note: Map View and Price Analysis show all of Nairobi for comparison. Neighborhood filter only affects Overview, Listings table, and counts above.")


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🗺️ Map View", "💰 Price Analysis", "💎 Best Value", "🔗 Browse Listings"]
)

with tab1:
    st.header("Overview")
    sale_data = filtered[filtered["type"] == "sale"]
    rent_data = filtered[filtered["type"] == "rent"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total listings", f"{len(filtered):,}")
    c2.metric("Median sale", f"KES {sale_data['price'].median()/1e6:.1f}M" if len(sale_data) else "—")
    c3.metric("Median rent", f"KES {rent_data['price'].median()/1e3:.0f}K" if len(rent_data) else "—")

    top_n = filtered["neighborhood"].value_counts()
    if len(selected) > 1 and len(top_n):
        c4.metric("Top neighborhood", top_n.index[0])
    else:
        med_size = filtered["size_m2"].median()
        c4.metric("Median size", f"{med_size:.0f} m²" if pd.notna(med_size) else "—")

    if len(filtered):
        st.subheader("Listings by neighborhood")
        n = filtered["neighborhood"].value_counts().head(15).reset_index()
        n.columns = ["neighborhood", "count"]
        fig = px.bar(n, x="count", y="neighborhood", orientation="h", text="count")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Listings")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Listing freshness")
        fresh = filtered["freshness"].value_counts().reindex(
            ["🟢 Fresh", "🟡 Possibly stale", "🔴 Probably gone"], fill_value=0
        )
        f1, f2, f3 = st.columns(3)
        f1.metric("🟢 Fresh (≤30d)", int(fresh.iloc[0]))
        f2.metric("🟡 30–90d", int(fresh.iloc[1]))
        f3.metric("🔴 >90d", int(fresh.iloc[2]))
    else:
        st.info("No listings match the current filters. Adjust filters in the sidebar.")


with tab2:
    st.header("Map View")

    available_metrics = []
    if "sale" in types:
        available_metrics.append("Median sale price")
    if "rent" in types:
        available_metrics.append("Median monthly rent")
    if "sale" in types:
        available_metrics.append("Sale price per m²")

    if not available_metrics:
        st.warning("Select at least one Type (sale or rent) in the sidebar to see the map.")
        map_metric = None
    else:
        map_metric = st.radio("Show on map:", available_metrics, horizontal=True)

    mapped = city_wide.dropna(subset=["sub_county"])
    if map_metric is None:
        agg = pd.DataFrame(columns=["sub_county", "median", "count", "value"])
        label = ""
    elif map_metric == "Median sale price":
        agg = mapped[mapped["type"] == "sale"].groupby("sub_county")["price"].agg(["median", "count"]).reset_index()
        agg["value"] = agg["median"] / 1e6
        label = "KES millions"
    elif map_metric == "Median monthly rent":
        agg = mapped[mapped["type"] == "rent"].groupby("sub_county")["price"].agg(["median", "count"]).reset_index()
        agg["value"] = agg["median"] / 1e3
        label = "KES thousands"
    else:
        s = mapped[(mapped["type"] == "sale") & mapped["size_m2"].notna()].copy()
        s["price_per_m2"] = s["price"] / s["size_m2"]
        agg = s.groupby("sub_county")["price_per_m2"].agg(["median", "count"]).reset_index()
        agg["value"] = agg["median"] / 1e3
        label = "KES thousands per m²"

    agg = agg[agg["count"] >= 5]

    # Always draw the full Nairobi outline first (all 17 sub-counties) in grey
    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        geojson=geojson,
        locations=all_sub_counties,
        z=[1] * len(all_sub_counties),
        featureidkey="properties.sub_county",
        colorscale=[[0, "lightgrey"], [1, "lightgrey"]],
        showscale=False,
        marker_line_color="white",
        marker_line_width=1,
        hoverinfo="text",
        hovertext=[f"{sc} (no data)" for sc in all_sub_counties],
    ))

    # Overlay coloured sub-counties (only those with enough data)
    if len(agg):
        fig.add_trace(go.Choropleth(
            geojson=geojson,
            locations=agg["sub_county"],
            z=agg["value"],
            featureidkey="properties.sub_county",
            colorscale="YlOrRd",
            marker_line_color="white",
            marker_line_width=1.5,
            colorbar=dict(title=label, thickness=15, len=0.7),
            customdata=agg[["count"]].values,
            hovertemplate="<b>%{location}</b><br>" + label + ": %{z:.1f}<br>n=%{customdata[0]}<extra></extra>",
        ))

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=600)
    st.plotly_chart(fig, use_container_width=True)

    if len(agg) == 0:
        st.warning("No sub-counties with enough data (n≥5) for selected filters. All 17 polygons shown in grey.")


with tab3:
    st.header("Price Analysis")
    st.caption("Comparing all neighborhoods across Nairobi. Sidebar's neighborhood filter does not apply here.")
    sale_data = city_wide[city_wide["type"] == "sale"]
    rent_data = city_wide[city_wide["type"] == "rent"]
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Median sale price")
        if len(sale_data):
            a = sale_data.groupby("neighborhood")["price"].agg(["median", "count"]).reset_index()
            a = a[a["count"] >= 3].sort_values("median", ascending=False).head(15)
            a["median_M"] = (a["median"] / 1e6).round(1)
            fig = px.bar(a, x="median_M", y="neighborhood", orientation="h", text="median_M")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="KES millions")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sale listings in current filter.")

    with c2:
        st.subheader("Median monthly rent")
        if len(rent_data):
            a = rent_data.groupby("neighborhood")["price"].agg(["median", "count"]).reset_index()
            a = a[a["count"] >= 3].sort_values("median", ascending=False).head(15)
            a["median_K"] = (a["median"] / 1e3).round(0)
            fig = px.bar(a, x="median_K", y="neighborhood", orientation="h", text="median_K")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="KES thousands")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rent listings in current filter.")

    st.subheader("Sale price per m² — premium areas (n≥5)")
    s = sale_data[sale_data["size_m2"].notna()].copy()
    if len(s):
        s["price_per_m2"] = s["price"] / s["size_m2"]
        ppm = s.groupby("neighborhood")["price_per_m2"].agg(["median", "count"]).reset_index()
        ppm = ppm[ppm["count"] >= 5].sort_values("median", ascending=False).head(10)
        if len(ppm):
            ppm["median_K"] = (ppm["median"] / 1e3).round(0)
            fig = px.bar(ppm, x="median_K", y="neighborhood", orientation="h",
                         color="median_K", color_continuous_scale="Greens", text="median_K")
            fig.update_layout(yaxis={"categoryorder": "total ascending"},
                              xaxis_title="KES thousands per m²")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No neighborhoods with ≥5 sized sale listings in current filter.")
    else:
        st.info("No sale listings with size data in current filter.")


with tab4:
    st.header("Best Value — Apartment Rental Yields")
    st.caption("Bedroom-matched gross yields. Apartments only, unfurnished rents, n≥10 each side.")

    apt = df[df["property_subtype"] == "apartment"]
    sale_med = apt[apt["type"] == "sale"].groupby(["neighborhood", "bedrooms"]).agg(
        median_sale=("price", "median"), n_sale=("price", "count")
    )
    rent_med = apt[(apt["type"] == "rent") & (apt["furnished"] == 0)].groupby(
        ["neighborhood", "bedrooms"]
    ).agg(median_rent=("price", "median"), n_rent=("price", "count"))
    yields = sale_med.join(rent_med, how="inner").reset_index()
    yields = yields[(yields["n_sale"] >= 10) & (yields["n_rent"] >= 10)]
    yields["annual_yield"] = (yields["median_rent"] * 12) / yields["median_sale"]
    yields = yields.sort_values(["bedrooms", "annual_yield"], ascending=[True, False])

    if len(yields):
        d = yields.copy()
        d["bedrooms"] = d["bedrooms"].astype(int)
        d["median_sale"] = d["median_sale"].apply(lambda x: f"KES {x/1e6:.1f}M")
        d["median_rent"] = d["median_rent"].apply(lambda x: f"KES {x/1e3:.0f}K")
        d["annual_yield"] = d["annual_yield"].apply(lambda x: f"{x*100:.1f}%")
        st.dataframe(d, hide_index=True, use_container_width=True)
    else:
        st.warning("No yield data available.")


with tab5:
    st.header("Browse listings")
    st.caption("Click any 'View on BRK' link to open the listing in a new tab.")

    if len(filtered):
        cols = ["title", "neighborhood", "type", "property_subtype",
                "bedrooms", "bathrooms", "size_m2", "price", "furnished", "url"]
        view = filtered[cols].copy()
        view["bedrooms"] = view["bedrooms"].astype("Int64")
        view["bathrooms"] = view["bathrooms"].astype("Int64")
        view["furnished"] = view["furnished"].map({1: "Yes", 0: "No"})
        view = view.sort_values("price", ascending=False)

        st.caption(f"{len(view)} listings shown. Sortable by clicking column headers.")
        st.dataframe(
            view,
            column_config={
                "title": st.column_config.TextColumn("Title", width="large"),
                "neighborhood": "Neighborhood",
                "type": "Type",
                "property_subtype": "Subtype",
                "bedrooms": st.column_config.NumberColumn("Beds"),
                "bathrooms": st.column_config.NumberColumn("Baths"),
                "size_m2": st.column_config.NumberColumn("Size (m²)", format="%.0f"),
                "price": st.column_config.NumberColumn("Price (KES)", format="%d"),
                "furnished": "Furnished",
                "url": st.column_config.LinkColumn("Link", display_text="View on BRK"),
            },
            use_container_width=True,
            hide_index=True,
            height=500,
        )
    else:
        st.info("No listings match the current filters.")


st.markdown("---")
st.caption(f"Data: BuyRentKenya scrape · {len(df)} listings · most recent {df['date_published'].max().strftime('%B %Y')}")
