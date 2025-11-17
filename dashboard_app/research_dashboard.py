#!/usr/bin/env python3
"""
AI Research Papers Analytics Dashboard

A comprehensive Streamlit dashboard for analyzing AI research papers data
from the Neon PostgreSQL database. Provides insights into publications,
authors, institutions, and research trends.

Usage:
    streamlit run research_dashboard.py

Features:
- Overview with key metrics and recent papers
- Publication trends and journal analysis
- Author and institutional analytics
- Research topics and AI/ML trends
- Geographic distribution analysis
- Interactive search and filtering
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sys
import os

print("🚀 Dashboard starting...")
print(f"📁 Python path: {sys.path[:3]}...")

# Import dashboard utilities
# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("📦 Importing dashboard config...")
    from dashboard_app.dashboard_config import (
        DashboardConfig,
        DashboardQueries,
        setup_page_config,
        format_number,
        create_sidebar_filters,
    )
    print("✅ Dashboard config imported successfully")
except Exception as e:
    print(f"❌ Dashboard config import failed: {e}")
    st.error(f"Configuration import failed: {e}")
    st.stop()


def main():
    """Main dashboard application."""
    # Setup page configuration
    setup_page_config()

    # Add diagnostics section at the top
    with st.expander("🔍 Database Diagnostics (Click to expand)", expanded=False):
        st.markdown("**Copy these logs to help troubleshoot:**")
        
        diagnostic_info = []
        diagnostic_info.append("=== STREAMLIT CLOUD DIAGNOSTICS ===")
        
        # Check if we're in Streamlit Cloud
        try:
            import streamlit as st_check
            if hasattr(st_check, 'secrets'):
                diagnostic_info.append("✅ Streamlit secrets object exists")
                if st_check.secrets:
                    diagnostic_info.append("✅ Streamlit secrets has data")
                    diagnostic_info.append(f"📋 Available secret keys: {list(st_check.secrets.keys())}")
                    
                    # Check specific database keys
                    db_keys = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_SSLMODE']
                    for key in db_keys:
                        if key in st_check.secrets:
                            value = st_check.secrets[key]
                            if key == 'DB_PASSWORD':
                                diagnostic_info.append(f"🔐 {key}: {'*' * len(str(value))}")
                            elif key == 'DB_HOST':
                                diagnostic_info.append(f"🌐 {key}: {str(value)[:30]}...")
                            else:
                                diagnostic_info.append(f"📝 {key}: {value}")
                        else:
                            diagnostic_info.append(f"❌ Missing key: {key}")
                else:
                    diagnostic_info.append("❌ Streamlit secrets is empty")
            else:
                diagnostic_info.append("❌ Streamlit secrets object not found")
        except Exception as e:
            diagnostic_info.append(f"⚠️ Secrets check failed: {e}")
        
        # Test database configuration
        try:
            diagnostic_info.append("\n=== DATABASE CONFIG TEST ===")
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
            from database import get_connection
            
            diagnostic_info.append("✅ Database module imported")
            
            conn = get_connection()
            if conn:
                diagnostic_info.append("✅ Database connection successful")
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM papers")
                    count = cursor.fetchone()[0]
                    diagnostic_info.append(f"📊 Papers in database: {count}")
                    cursor.close()
                    conn.close()
                except Exception as e:
                    diagnostic_info.append(f"⚠️ Query failed: {e}")
            else:
                diagnostic_info.append("❌ Database connection failed - returned None")
                
        except Exception as e:
            diagnostic_info.append(f"❌ Database test failed: {e}")
        
        # Display all diagnostic info
        diagnostic_text = "\n".join(diagnostic_info)
        st.code(diagnostic_text, language="text")
        
        if st.button("🔄 Refresh Diagnostics"):
            st.rerun()

    # Create main header
    st.markdown(
        '<h1 class="main-header">🔬 AI Research Papers Analytics</h1>',
        unsafe_allow_html=True,
    )

    # Create sidebar filters
    filters = create_sidebar_filters()

    # Main navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Dashboard Pages")

    # Page selection
    pages = {
        "🏠 Overview": "overview",
        "📈 Publication Trends": "publications",
        "👥 Authors & Institutions": "authors",
        "🔬 Research Topics": "topics",
        "🌍 Geographic Analysis": "geographic",
    }

    selected_page = st.sidebar.radio("Navigate to:", list(pages.keys()))
    page_key = pages[selected_page]

    # Route to appropriate page
    if page_key == "overview":
        show_overview_page(filters)
    elif page_key == "publications":
        show_publications_page(filters)
    elif page_key == "authors":
        show_authors_page(filters)
    elif page_key == "topics":
        show_topics_page(filters)
    elif page_key == "geographic":
        show_geographic_page(filters)

    # Footer
    st.markdown("---")
    st.markdown(
        "**💡 Dashboard Info:** Data sourced from OpenAlex API • "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} • "
        "Built with Streamlit & Plotly"
    )


def show_overview_page(filters: dict):
    """Display overview page with key metrics and recent activity."""
    st.header("📊 Research Portfolio Overview")

    # Get overview metrics
    with st.spinner("Loading overview metrics..."):
        metrics = DashboardQueries.get_overview_metrics()
        recent_papers = DashboardQueries.get_recent_papers(15)

    if not metrics:
        st.error("Unable to load overview metrics. Please check database connection.")
        return

    # Key Metrics Row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Papers",
            value=format_number(metrics.get("total_papers", 0)),
            delta=f"+{metrics.get('recent_papers', 0)} this month",
        )

    with col2:
        st.metric(
            label="Total Citations",
            value=format_number(metrics.get("total_citations", 0)),
            delta=f"Avg: {metrics.get('avg_citations', 0):.1f} per paper",
        )

    with col3:
        st.metric(
            label="Unique Authors", value=format_number(metrics.get("total_authors", 0))
        )

    with col4:
        st.metric(
            label="Open Access",
            value=f"{metrics.get('open_access_ratio', 0):.1f}%",
            delta="of all papers",
        )

    # Two column layout for charts
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Publication Trends (Last 24 Months)")

        # Get publication trends
        with st.spinner("Loading publication trends..."):
            trends_df = DashboardQueries.get_publication_trends(730)  # 2 years

        if not trends_df.empty:
            # Create dual-axis chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Papers count
            fig.add_trace(
                go.Scatter(
                    x=trends_df["month"],
                    y=trends_df["paper_count"],
                    mode="lines+markers",
                    name="Papers Published",
                    line=dict(color="#1f77b4", width=3),
                    marker=dict(size=8),
                ),
                secondary_y=False,
            )

            # Average citations
            fig.add_trace(
                go.Scatter(
                    x=trends_df["month"],
                    y=trends_df["avg_citations"],
                    mode="lines+markers",
                    name="Avg Citations",
                    line=dict(color="#ff7f0e", width=3),
                    marker=dict(size=8),
                ),
                secondary_y=True,
            )

            fig.update_xaxes(title_text="Month")
            fig.update_yaxes(title_text="Number of Papers", secondary_y=False)
            fig.update_yaxes(title_text="Average Citations", secondary_y=True)
            fig.update_layout(
                height=400,
                hovermode="x unified",
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )

            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No publication trends data available.")

    with col2:
        st.subheader("🎯 Quick Insights")

        # Top topics mini chart
        with st.spinner("Loading research topics..."):
            topics_df = DashboardQueries.get_research_topics(8)

        if not topics_df.empty:
            fig = px.pie(
                topics_df.head(6),
                values="paper_count",
                names="topic",
                title="Top Research Areas",
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(height=300, showlegend=False, font=dict(size=10))
            st.plotly_chart(fig, width="stretch")

        # Mini stats
        if not topics_df.empty:
            ai_papers = topics_df["ai_papers"].sum()
            total_topic_papers = topics_df["paper_count"].sum()
            ai_percentage = (
                (ai_papers / total_topic_papers * 100) if total_topic_papers > 0 else 0
            )

            st.metric("AI/ML Focus", f"{ai_percentage:.1f}%", f"{ai_papers} papers")

    # Recent Papers Section
    st.subheader("📚 Recent Publications")

    if not recent_papers.empty:
        # Add search functionality
        search_term = st.text_input(
            "🔍 Search papers by title:", placeholder="Enter keywords..."
        )

        if search_term:
            with st.spinner(f"Searching for '{search_term}'..."):
                search_results = DashboardQueries.search_papers(search_term, 20)

            if not search_results.empty:
                st.write(f"**Search Results ({len(search_results)} papers found):**")
                display_df = search_results
            else:
                st.warning("No papers found matching your search.")
                display_df = recent_papers
        else:
            display_df = recent_papers

        # Format the dataframe for display
        if not display_df.empty:
            display_papers = display_df.copy()
            display_papers["date"] = pd.to_datetime(display_papers["date"]).dt.strftime(
                "%Y-%m-%d"
            )
            display_papers["open_access"] = display_papers["open_access"].map(
                {True: "✅ Yes", False: "❌ No"}
            )
            display_papers["title"] = display_papers["title"].str.slice(0, 80) + "..."

            # Display as interactive table
            st.dataframe(
                display_papers[
                    ["title", "journal", "date", "citations", "open_access", "country"]
                ],
                column_config={
                    "title": "Paper Title",
                    "journal": "Journal",
                    "date": "Published",
                    "citations": st.column_config.NumberColumn(
                        "Citations", format="%d"
                    ),
                    "open_access": "Open Access",
                    "country": "Country",
                },
                hide_index=True,
                width="stretch",
            )

    else:
        st.info("No recent papers data available.")


def show_publications_page(filters: dict):
    """Display publications analysis page."""
    st.header("📈 Publications Analysis")

    # Get data
    with st.spinner("Loading publications data..."):
        trends_df = DashboardQueries.get_publication_trends(filters["days_back"])
        journals_df = DashboardQueries.get_top_journals(20)
        topics_df = DashboardQueries.get_research_topics(15)

    # Publications over time
    st.subheader("📅 Publication Timeline")

    if not trends_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Papers per month
            fig = px.bar(
                trends_df,
                x="month",
                y="paper_count",
                title="Papers Published per Month",
                labels={"paper_count": "Number of Papers", "month": "Month"},
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width="stretch")

        with col2:
            # Open access trends
            fig = px.line(
                trends_df,
                x="month",
                y="oa_percentage",
                title="Open Access Percentage Over Time",
                labels={"oa_percentage": "Open Access %", "month": "Month"},
            )
            fig.update_layout(height=400)
            fig.update_traces(line=dict(color="#2ca02c", width=3))
            st.plotly_chart(fig, width="stretch")

    # Top Journals Analysis
    st.subheader("📚 Journal Analysis")

    if not journals_df.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Top journals by paper count
            fig = px.bar(
                journals_df.head(10),
                x="paper_count",
                y="journal",
                title="Top Journals by Paper Count",
                labels={"paper_count": "Number of Papers", "journal": "Journal"},
                orientation="h",
            )
            fig.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, width="stretch")

        with col2:
            # Journal metrics table
            st.write("**Journal Metrics:**")
            display_journals = journals_df.head(10).copy()
            display_journals = display_journals.round(
                {"avg_citations": 1, "oa_percentage": 1}
            )

            st.dataframe(
                display_journals[
                    ["journal", "paper_count", "avg_citations", "oa_percentage"]
                ],
                column_config={
                    "journal": "Journal Name",
                    "paper_count": "Papers",
                    "avg_citations": "Avg Citations",
                    "oa_percentage": "OA %",
                },
                hide_index=True,
                width="stretch",
            )

    # Research Topics Distribution
    st.subheader("🔬 Research Topics Distribution")

    if not topics_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Topics treemap
            fig = px.treemap(
                topics_df.head(12),
                values="paper_count",
                names="topic",
                title="Research Topics by Paper Count",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width="stretch")

        with col2:
            # AI vs Non-AI papers
            fig = px.scatter(
                topics_df.head(15),
                x="paper_count",
                y="avg_citations",
                size="ai_papers",
                color="ai_percentage",
                hover_name="topic",
                title="Topics: Papers vs Citations (Size = AI Papers)",
                labels={
                    "paper_count": "Number of Papers",
                    "avg_citations": "Average Citations",
                    "ai_percentage": "AI %",
                },
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width="stretch")


def show_authors_page(filters: dict):
    """Display authors and institutions analysis page."""
    st.header("👥 Authors & Institutions Analysis")

    # Get authors data
    with st.spinner("Loading authors data..."):
        authors_df = DashboardQueries.get_top_authors(30)
        geo_df = DashboardQueries.get_geographic_distribution()

    if authors_df.empty:
        st.error("No authors data available.")
        return

    # Top Authors Section
    st.subheader("🏆 Top Authors by Citations")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Top authors bar chart
        top_authors = authors_df.head(15)
        fig = px.bar(
            top_authors,
            x="citations",
            y="author",
            title="Most Cited Authors",
            labels={"citations": "Total Citations", "author": "Author"},
            orientation="h",
        )
        fig.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Authors metrics
        st.write("**Author Metrics:**")
        display_authors = authors_df.head(10).copy()
        display_authors["author"] = display_authors["author"].str.slice(0, 25) + "..."

        st.dataframe(
            display_authors[["author", "papers", "citations", "h_index"]],
            column_config={
                "author": "Author",
                "papers": "Papers",
                "citations": "Citations",
                "h_index": "H-index",
            },
            hide_index=True,
            width="stretch",
        )

    # H-index vs Citations Analysis
    st.subheader("📊 Author Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        # H-index vs citations scatter
        fig = px.scatter(
            authors_df.head(25),
            x="citations",
            y="h_index",
            size="papers",
            hover_name="author",
            title="H-index vs Citations (Size = Paper Count)",
            labels={"citations": "Total Citations", "h_index": "H-index"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Papers vs citations
        fig = px.scatter(
            authors_df.head(25),
            x="papers",
            y="citations",
            color="h_index",
            hover_name="author",
            title="Papers vs Citations (Color = H-index)",
            labels={"papers": "Number of Papers", "citations": "Total Citations"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    # Geographic and Institutional Analysis
    if not geo_df.empty:
        st.subheader("🌍 Geographic & Institutional Distribution")

        col1, col2 = st.columns(2)

        with col1:
            # Country distribution
            fig = px.bar(
                geo_df.head(15),
                x="paper_count",
                y="country",
                title="Research Output by Country",
                labels={"paper_count": "Number of Papers", "country": "Country"},
                orientation="h",
            )
            fig.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, width="stretch")

        with col2:
            # Top institutions from authors
            if "institution" in authors_df.columns:
                inst_counts = (
                    authors_df.groupby("institution")
                    .agg({"papers": "sum", "citations": "sum"})
                    .reset_index()
                    .sort_values("citations", ascending=False)
                )

                inst_counts = inst_counts[inst_counts["institution"] != "Unknown"].head(
                    10
                )

                if not inst_counts.empty:
                    fig = px.bar(
                        inst_counts,
                        x="citations",
                        y="institution",
                        title="Top Institutions by Total Citations",
                        labels={
                            "citations": "Total Citations",
                            "institution": "Institution",
                        },
                        orientation="h",
                    )
                    fig.update_layout(
                        height=500, yaxis={"categoryorder": "total ascending"}
                    )
                    st.plotly_chart(fig, width="stretch")


def show_topics_page(filters: dict):
    """Display research topics analysis page."""
    st.header("🔬 Research Topics & Trends")

    # Get topics data
    with st.spinner("Loading research topics..."):
        topics_df = DashboardQueries.get_research_topics(25)

    if topics_df.empty:
        st.error("No research topics data available.")
        return

    # Topics Overview
    st.subheader("📈 Research Areas Overview")

    col1, col2 = st.columns(2)

    with col1:
        # Topics by paper count
        fig = px.bar(
            topics_df.head(15),
            x="paper_count",
            y="topic",
            title="Most Active Research Topics",
            labels={"paper_count": "Number of Papers", "topic": "Research Topic"},
            orientation="h",
        )
        fig.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    with col2:
        # AI vs Non-AI distribution
        ai_topics = topics_df[topics_df["ai_percentage"] > 50].head(10)

        fig = px.pie(
            ai_topics,
            values="ai_papers",
            names="topic",
            title="AI/ML Focused Research Areas",
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, width="stretch")

    # Research Impact Analysis
    st.subheader("📊 Research Impact by Topic")

    col1, col2 = st.columns(2)

    with col1:
        # Citations vs papers bubble chart
        fig = px.scatter(
            topics_df.head(20),
            x="paper_count",
            y="avg_citations",
            size="ai_papers",
            color="ai_percentage",
            hover_name="topic",
            title="Research Volume vs Impact (Size = AI Papers)",
            labels={
                "paper_count": "Number of Papers",
                "avg_citations": "Average Citations",
                "ai_percentage": "AI Focus %",
            },
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Top topics by average citations
        top_cited = topics_df.sort_values("avg_citations", ascending=False).head(10)

        fig = px.bar(
            top_cited,
            x="avg_citations",
            y="topic",
            title="Highest Impact Research Topics",
            labels={
                "avg_citations": "Average Citations per Paper",
                "topic": "Research Topic",
            },
            orientation="h",
        )
        fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    # Detailed Topics Table
    st.subheader("📋 Detailed Topics Analysis")

    # Add sorting options
    sort_options = {
        "Paper Count (↓)": ("paper_count", False),
        "Average Citations (↓)": ("avg_citations", False),
        "AI Percentage (↓)": ("ai_percentage", False),
        "Topic Name (A-Z)": ("topic", True),
    }

    selected_sort = st.selectbox("Sort by:", list(sort_options.keys()))
    sort_col, ascending = sort_options[selected_sort]

    sorted_topics = topics_df.sort_values(sort_col, ascending=ascending)

    # Format for display
    display_topics = sorted_topics.copy()
    display_topics = display_topics.round({"avg_citations": 1, "ai_percentage": 1})

    st.dataframe(
        display_topics,
        column_config={
            "topic": "Research Topic",
            "paper_count": st.column_config.NumberColumn("Papers", format="%d"),
            "avg_citations": st.column_config.NumberColumn(
                "Avg Citations", format="%.1f"
            ),
            "ai_papers": st.column_config.NumberColumn("AI Papers", format="%d"),
            "ai_percentage": st.column_config.NumberColumn(
                "AI Focus %", format="%.1f%%"
            ),
        },
        hide_index=True,
        width="stretch",
    )


def show_geographic_page(filters: dict):
    """Display geographic analysis page."""
    st.header("🌍 Geographic Analysis")

    # Get geographic data
    with st.spinner("Loading geographic data..."):
        geo_df = DashboardQueries.get_geographic_distribution()

    if geo_df.empty:
        st.error("No geographic data available.")
        return

    # World Map Visualization (if we had coordinates)
    st.subheader("🗺️ Global Research Distribution")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Country bar chart
        fig = px.bar(
            geo_df.head(20),
            x="paper_count",
            y="country",
            title="Research Output by Country",
            labels={"paper_count": "Number of Papers", "country": "Country"},
            orientation="h",
        )
        fig.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Top countries metrics
        st.write("**Country Metrics:**")
        display_geo = geo_df.head(15).copy()
        display_geo = display_geo.round({"avg_citations": 1})

        st.dataframe(
            display_geo[["country", "paper_count", "unique_authors", "avg_citations"]],
            column_config={
                "country": "Country",
                "paper_count": "Papers",
                "unique_authors": "Authors",
                "avg_citations": "Avg Citations",
            },
            hide_index=True,
            width="stretch",
        )

    # Research Quality Analysis
    st.subheader("📊 Research Quality by Country")

    col1, col2 = st.columns(2)

    with col1:
        # Citations vs papers
        fig = px.scatter(
            geo_df.head(20),
            x="paper_count",
            y="avg_citations",
            size="unique_authors",
            hover_name="country",
            title="Research Volume vs Quality (Size = Authors)",
            labels={
                "paper_count": "Number of Papers",
                "avg_citations": "Average Citations",
            },
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Open access by country
        geo_with_oa = geo_df.copy()
        geo_with_oa["oa_percentage"] = (
            geo_with_oa["oa_papers"] / geo_with_oa["paper_count"] * 100
        ).round(1)

        fig = px.bar(
            geo_with_oa.head(15),
            x="oa_percentage",
            y="country",
            title="Open Access Adoption by Country",
            labels={"oa_percentage": "Open Access %", "country": "Country"},
            orientation="h",
        )
        fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Dashboard error: {e}")
        st.info("Please check your database connection and try again.")
