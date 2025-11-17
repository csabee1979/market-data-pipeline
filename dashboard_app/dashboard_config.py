"""
Dashboard Configuration and Utilities for Research Papers Analytics

This module provides configuration management and database utilities
specifically designed for the Streamlit dashboard.
"""

import os
import sys
import pandas as pd
import streamlit as st
from typing import Dict, Any

# Import database utilities from existing module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database"))
try:
    from database import get_connection, execute_query
except ImportError:
    # Fallback for development
    def get_connection():
        pass

    def execute_query(query):
        return []


class DashboardConfig:
    """Configuration class for dashboard settings."""

    def __init__(self):
        self.page_title = "AI Research Papers Analytics Dashboard"
        self.page_icon = "📊"
        self.layout = "wide"
        self.sidebar_title = "🔍 Navigation & Filters"

        # Color scheme
        self.colors = {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "success": "#2ca02c",
            "warning": "#d62728",
            "info": "#17a2b8",
            "background": "#f8f9fa",
        }

        # Chart configurations
        self.default_chart_height = 400
        self.default_chart_width = 800

        # Cache configurations
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_entries = 1000


class DashboardQueries:
    """Database query utilities for dashboard analytics."""

    @staticmethod
    @st.cache_data(ttl=300)
    def get_overview_metrics() -> Dict[str, Any]:
        """Get key metrics for dashboard overview."""
        try:
            queries = {
                "total_papers": "SELECT COUNT(*) as count FROM papers",
                "total_authors": "SELECT COUNT(*) as count FROM authors",
                "total_citations": "SELECT COALESCE(SUM(cited_by_count), 0) as total FROM papers",
                "avg_citations": "SELECT ROUND(AVG(cited_by_count)::numeric, 2) as avg FROM papers WHERE cited_by_count > 0",
                "open_access_ratio": """
                    SELECT ROUND(
                        ((COUNT(CASE WHEN is_open_access = true THEN 1 END)::float / COUNT(*)) * 100)::numeric, 1
                    ) as percentage FROM papers
                """,
                "recent_papers": """
                    SELECT COUNT(*) as count FROM papers 
                    WHERE publication_date >= CURRENT_DATE - INTERVAL '30 days'
                """,
            }

            results = {}
            for key, query in queries.items():
                result = execute_query(query)
                if result and len(result) > 0:
                    if key in ["total_papers", "total_authors", "recent_papers"]:
                        results[key] = result[0][0]
                    elif key == "total_citations":
                        results[key] = int(result[0][0]) if result[0][0] else 0
                    elif key == "avg_citations":
                        results[key] = float(result[0][0]) if result[0][0] else 0.0
                    elif key == "open_access_ratio":
                        results[key] = float(result[0][0]) if result[0][0] else 0.0
                else:
                    results[key] = 0

            return results

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error fetching overview metrics: {e}")
            return {}

    @staticmethod
    @st.cache_data(ttl=300)
    def get_publication_trends(days_back: int = 365) -> pd.DataFrame:
        """Get publication trends over time."""
        try:
            query = f"""
            SELECT 
                DATE_TRUNC('month', publication_date) as month,
                COUNT(*) as paper_count,
                ROUND(AVG(cited_by_count)::numeric, 2) as avg_citations,
                COUNT(CASE WHEN is_open_access = true THEN 1 END) as oa_papers
            FROM papers 
            WHERE publication_date >= CURRENT_DATE - INTERVAL '{days_back} days'
                AND publication_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', publication_date)
            ORDER BY month DESC
            LIMIT 24
            """

            result = execute_query(query)
            if result:
                df = pd.DataFrame(
                    result,
                    columns=["month", "paper_count", "avg_citations", "oa_papers"],
                )
                df["month"] = pd.to_datetime(df["month"])
                df["oa_percentage"] = (df["oa_papers"] / df["paper_count"] * 100).round(
                    1
                )
                return df.sort_values("month")
            else:
                return pd.DataFrame()

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error fetching publication trends: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=300)
    def get_top_journals(limit: int = 15) -> pd.DataFrame:
        """Get top journals by paper count."""
        try:
            query = f"""
            SELECT 
                COALESCE(journal_name, 'Unknown Journal') as journal,
                COUNT(*) as paper_count,
                ROUND(AVG(cited_by_count)::numeric, 2) as avg_citations,
                COUNT(CASE WHEN is_open_access = true THEN 1 END) as oa_papers,
                ROUND(
                    ((COUNT(CASE WHEN is_open_access = true THEN 1 END)::float / COUNT(*)) * 100)::numeric, 1
                ) as oa_percentage
            FROM papers 
            WHERE journal_name IS NOT NULL 
                AND journal_name != ''
            GROUP BY journal_name
            HAVING COUNT(*) >= 3
            ORDER BY paper_count DESC
            LIMIT {limit}
            """

            result = execute_query(query)
            if result:
                return pd.DataFrame(
                    result,
                    columns=[
                        "journal",
                        "paper_count",
                        "avg_citations",
                        "oa_papers",
                        "oa_percentage",
                    ],
                )
            else:
                return pd.DataFrame()

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error fetching top journals: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=300)
    def get_top_authors(limit: int = 20) -> pd.DataFrame:
        """Get top authors by various metrics."""
        try:
            query = f"""
            SELECT 
                display_name,
                total_papers,
                total_citations,
                h_index,
                COALESCE(primary_institution, 'Unknown') as institution,
                COALESCE(primary_country, 'Unknown') as country,
                orcid
            FROM authors 
            WHERE total_papers > 0
            ORDER BY total_citations DESC, total_papers DESC
            LIMIT {limit}
            """

            result = execute_query(query)
            if result:
                return pd.DataFrame(
                    result,
                    columns=[
                        "author",
                        "papers",
                        "citations",
                        "h_index",
                        "institution",
                        "country",
                        "orcid",
                    ],
                )
            else:
                return pd.DataFrame()

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error fetching top authors: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=300)
    def get_research_topics(limit: int = 20) -> pd.DataFrame:
        """Get most popular research topics."""
        try:
            query = f"""
            SELECT 
                COALESCE(primary_topic, 'Unknown Topic') as topic,
                COUNT(*) as paper_count,
                ROUND(AVG(cited_by_count)::numeric, 2) as avg_citations,
                COUNT(CASE WHEN has_ai_field = true THEN 1 END) as ai_papers,
                ROUND(
                    ((COUNT(CASE WHEN has_ai_field = true THEN 1 END)::float / COUNT(*)) * 100)::numeric, 1
                ) as ai_percentage
            FROM papers 
            WHERE primary_topic IS NOT NULL 
                AND primary_topic != ''
            GROUP BY primary_topic
            HAVING COUNT(*) >= 2
            ORDER BY paper_count DESC
            LIMIT {limit}
            """

            result = execute_query(query)
            if result:
                return pd.DataFrame(
                    result,
                    columns=[
                        "topic",
                        "paper_count",
                        "avg_citations",
                        "ai_papers",
                        "ai_percentage",
                    ],
                )
            else:
                return pd.DataFrame()

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error fetching research topics: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=300)
    def get_geographic_distribution() -> pd.DataFrame:
        """Get geographic distribution of research."""
        try:
            query = """
            SELECT 
                COALESCE(first_country, 'Unknown') as country,
                COUNT(*) as paper_count,
                COUNT(DISTINCT pa.author_id) as unique_authors,
                ROUND(AVG(p.cited_by_count)::numeric, 2) as avg_citations,
                COUNT(CASE WHEN p.is_open_access = true THEN 1 END) as oa_papers
            FROM papers p
            LEFT JOIN paper_authors pa ON p.paper_id = pa.paper_id AND pa.author_position = 'first'
            WHERE first_country IS NOT NULL 
                AND first_country != ''
            GROUP BY first_country
            HAVING COUNT(*) >= 3
            ORDER BY paper_count DESC
            LIMIT 25
            """

            result = execute_query(query)
            if result:
                return pd.DataFrame(
                    result,
                    columns=[
                        "country",
                        "paper_count",
                        "unique_authors",
                        "avg_citations",
                        "oa_papers",
                    ],
                )
            else:
                return pd.DataFrame()

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error fetching geographic distribution: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=300)
    def get_recent_papers(limit: int = 10) -> pd.DataFrame:
        """Get most recent papers."""
        try:
            query = f"""
            SELECT 
                title,
                COALESCE(journal_name, 'Unknown Journal') as journal,
                publication_date,
                cited_by_count,
                is_open_access,
                COALESCE(first_country, 'Unknown') as country,
                paper_id
            FROM papers 
            WHERE publication_date IS NOT NULL
            ORDER BY publication_date DESC, cited_by_count DESC
            LIMIT {limit}
            """

            result = execute_query(query)
            if result:
                return pd.DataFrame(
                    result,
                    columns=[
                        "title",
                        "journal",
                        "date",
                        "citations",
                        "open_access",
                        "country",
                        "paper_id",
                    ],
                )
            else:
                return pd.DataFrame()

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error fetching recent papers: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=300)
    def search_papers(search_term: str, limit: int = 50) -> pd.DataFrame:
        """Search papers by title or keywords."""
        try:
            # Use PostgreSQL full-text search
            query = f"""
            SELECT 
                title,
                COALESCE(journal_name, 'Unknown Journal') as journal,
                publication_date,
                cited_by_count,
                is_open_access,
                COALESCE(primary_topic, 'Unknown') as topic,
                paper_id
            FROM papers 
            WHERE to_tsvector('english', title) @@ plainto_tsquery('english', %s)
                OR LOWER(title) LIKE LOWER(%s)
            ORDER BY cited_by_count DESC, publication_date DESC
            LIMIT {limit}
            """

            search_pattern = f"%{search_term}%"

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (search_term, search_pattern))
                result = cursor.fetchall()

            if result:
                return pd.DataFrame(
                    result,
                    columns=[
                        "title",
                        "journal",
                        "date",
                        "citations",
                        "open_access",
                        "topic",
                        "paper_id",
                    ],
                )
            else:
                return pd.DataFrame()

        except (Exception, ImportError, ConnectionError) as e:
            st.error(f"Error searching papers: {e}")
            return pd.DataFrame()


def setup_page_config():
    """Setup Streamlit page configuration."""
    config = DashboardConfig()

    st.set_page_config(
        page_title=config.page_title,
        page_icon=config.page_icon,
        layout=config.layout,
        initial_sidebar_state="expanded",
    )

    # Custom CSS for better styling
    st.markdown(
        """
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .sidebar-filter {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stSidebar"] > div {
        background-color: #f8f9fa;
    }
    
    .plot-container {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def format_number(num: int) -> str:
    """Format numbers for display."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)


def create_sidebar_filters() -> Dict[str, Any]:
    """Create sidebar filters and return selected values."""
    st.sidebar.title("🔍 Filters & Navigation")

    filters = {}

    # Date range filter
    st.sidebar.subheader("📅 Date Range")
    date_options = {
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last 6 months": 180,
        "Last year": 365,
        "Last 2 years": 730,
        "All time": 3650,
    }

    selected_period = st.sidebar.selectbox(
        "Select time period:", list(date_options.keys()), index=3
    )
    filters["days_back"] = date_options[selected_period]

    # Additional filters can be added here
    st.sidebar.subheader("🎯 Quick Stats")

    # Display some quick stats in sidebar
    try:
        metrics = DashboardQueries.get_overview_metrics()
        if metrics:
            st.sidebar.metric(
                "Total Papers", format_number(metrics.get("total_papers", 0))
            )
            st.sidebar.metric(
                "Total Authors", format_number(metrics.get("total_authors", 0))
            )
            st.sidebar.metric("Avg Citations", f"{metrics.get('avg_citations', 0):.1f}")
    except (Exception, ImportError, ConnectionError):
        pass

    return filters
