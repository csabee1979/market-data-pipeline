"""
Script to fetch recent AI research papers from OpenAlex API.

This script:
1. Searches for the "artificial intelligence" concept in OpenAlex
2. Retrieves ALL papers published in the last 3 days related to this concept
3. Filters papers by AI relevance score and field/subfield
4. Saves the filtered results to a timestamped JSON file in the temp/ folder

Note: Uses strict filtering for relevant AI papers:
- Papers with AI relevance score ≥ 0.7, OR
- Papers with "Artificial Intelligence" as field or subfield
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from pyalex import Works, Concepts

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def retry_with_exponential_backoff(func, max_retries=10, initial_delay=1):
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts (default: 10)
        initial_delay: Initial delay in seconds (default: 1)

    Returns:
        Result of the function call

    Raises:
        Exception: If all retries are exhausted
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ ERROR: All {max_retries} retry attempts exhausted.")
                print(f"   Last error: {str(e)}")
                raise

            print(f"⚠️  Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            print(f"   Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff


def calculate_ai_relevance_score(paper: Dict[str, Any]) -> float:
    """
    Calculate AI relevance score for a paper based on multiple factors.

    Args:
        paper: Paper dictionary with metadata

    Returns:
        Relevance score (0.0 to 1.0, higher = more relevant)
    """
    score = 0.0

    # Check keywords for AI-related terms
    keywords = paper.get("keywords", [])
    for keyword in keywords:
        keyword_name = keyword.get("display_name", "").lower()
        keyword_score = keyword.get("score", 0)

        if "artificial intelligence" in keyword_name or keyword_name == "ai":
            score = max(
                score, keyword_score * 2.0
            )  # Double weight for direct AI keywords
        elif any(
            term in keyword_name
            for term in [
                "machine learning",
                "deep learning",
                "neural network",
                "computer vision",
                "natural language",
                "reinforcement learning",
            ]
        ):
            score = max(score, keyword_score * 1.5)  # High weight for ML/AI subfields

    # Check concepts for AI
    concepts = paper.get("concepts", [])
    for concept in concepts:
        concept_name = concept.get("display_name", "").lower()
        concept_score = concept.get("score", 0)

        if "artificial intelligence" in concept_name:
            score = max(score, concept_score * 2.0)
        elif any(
            term in concept_name
            for term in ["machine learning", "deep learning", "neural network"]
        ):
            score = max(score, concept_score * 1.5)

    # Check primary topic field/subfield
    primary_topic = paper.get("primary_topic", {})
    if primary_topic:
        field_name = primary_topic.get("field", {}).get("display_name", "").lower()
        subfield_name = (
            primary_topic.get("subfield", {}).get("display_name", "").lower()
        )

        if (
            "artificial intelligence" in field_name
            or "artificial intelligence" in subfield_name
        ):
            score = max(score, 0.9)  # Very high score for AI field/subfield
        elif "computer science" in field_name:
            score = max(score, 0.5)  # Moderate score for CS field

    # Check all topics
    topics = paper.get("topics", [])
    for topic in topics:
        field_name = topic.get("field", {}).get("display_name", "").lower()
        subfield_name = topic.get("subfield", {}).get("display_name", "").lower()
        topic_score = topic.get("score", 0)

        if (
            "artificial intelligence" in field_name
            or "artificial intelligence" in subfield_name
        ):
            score = max(score, topic_score * 0.8)
        elif "computer science" in field_name:
            score = max(score, topic_score * 0.4)

    return min(score, 1.0)  # Cap at 1.0


def has_ai_field_or_subfield(paper: Dict[str, Any]) -> bool:
    """
    Check if a paper has 'Artificial Intelligence' as field or subfield.

    Args:
        paper: Paper dictionary with topics information

    Returns:
        True if AI is found as field or subfield, False otherwise
    """
    ai_keywords = ["artificial intelligence", "ai"]

    # Check primary_topic
    primary_topic = paper.get("primary_topic", {})
    if primary_topic:
        field_name = primary_topic.get("field", {}).get("display_name", "").lower()
        subfield_name = (
            primary_topic.get("subfield", {}).get("display_name", "").lower()
        )

        if any(keyword in field_name for keyword in ai_keywords) or any(
            keyword in subfield_name for keyword in ai_keywords
        ):
            return True

    # Check all topics
    topics = paper.get("topics", [])
    for topic in topics:
        field_name = topic.get("field", {}).get("display_name", "").lower()
        subfield_name = topic.get("subfield", {}).get("display_name", "").lower()

        if any(keyword in field_name for keyword in ai_keywords) or any(
            keyword in subfield_name for keyword in ai_keywords
        ):
            return True

    return False


def is_ai_relevant(paper: Dict[str, Any], min_score: float = 0.7) -> bool:
    """
    Determine if a paper is AI-relevant based on:
    - High AI relevance score (>= 0.7), OR
    - Has AI as field or subfield

    Args:
        paper: Paper dictionary with metadata
        min_score: Minimum relevance score threshold (default: 0.7)

    Returns:
        True if paper is AI-relevant, False otherwise
    """
    relevance_score = calculate_ai_relevance_score(paper)

    # Store score in paper for reference
    paper["_ai_relevance_score"] = relevance_score

    # Check if has AI field/subfield
    has_ai_field = has_ai_field_or_subfield(paper)
    paper["_has_ai_field"] = has_ai_field

    # Accept if EITHER high score OR AI field/subfield
    return relevance_score >= min_score or has_ai_field


def find_ai_concept() -> Optional[str]:
    """
    Search for the 'artificial intelligence' concept and return the most relevant concept ID.

    Returns:
        Concept ID (OpenAlex ID) or None if not found
    """
    print("🔍 Searching for 'artificial intelligence' concept...")

    def search_concept():
        results = Concepts().search("artificial intelligence").get()
        return results

    try:
        results = retry_with_exponential_backoff(search_concept)

        if not results:
            print("❌ ERROR: No concept found for 'artificial intelligence'")
            return None

        # Find the most relevant concept (highest cited_by_count or relevance score)
        most_relevant = max(results, key=lambda x: x.get("cited_by_count", 0))

        concept_id = most_relevant["id"]
        concept_name = most_relevant.get("display_name", "Unknown")
        cited_count = most_relevant.get("cited_by_count", 0)

        print(f"✅ Found concept: '{concept_name}'")
        print(f"   ID: {concept_id}")
        print(f"   Cited by: {cited_count:,} works")

        return concept_id

    except Exception as e:
        print(f"❌ ERROR: Failed to find AI concept: {str(e)}")
        return None


def fetch_recent_ai_papers(concept_id: str, days: int = 3) -> List[Dict[str, Any]]:
    """
    Fetch ALL papers related to the AI concept from the last N days.

    Args:
        concept_id: OpenAlex concept ID
        days: Number of days to look back (default: 3)

    Returns:
        List of paper dictionaries with all available fields
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Format dates for OpenAlex API (YYYY-MM-DD)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    print(f"\n📅 Fetching papers from {start_date_str} to {end_date_str}...")
    print(f"🌐 Fetching ALL AI-related papers from API...")

    def fetch_papers():
        # Query works with concept filter and date range
        query = (
            Works()
            .filter(concepts={"id": concept_id})
            .filter(from_publication_date=start_date_str)
            .filter(to_publication_date=end_date_str)
        )

        # Get all results using paginate() to retrieve ALL papers
        all_papers = []
        page_num = 0
        for page in query.paginate(per_page=200):
            page_num += 1
            all_papers.extend(page)
            print(
                f"   📄 Fetched page {page_num}: {len(page)} papers (total so far: {len(all_papers)})"
            )

        return all_papers

    try:
        all_papers = retry_with_exponential_backoff(fetch_papers)

        print(f"✅ Retrieved {len(all_papers)} AI-related paper(s) from API")

        # Filter by AI relevance score OR field/subfield
        print(f"\n🔍 Filtering papers (score > 0.7 OR AI field/subfield)...")
        filtered_papers = [
            paper for paper in all_papers if is_ai_relevant(paper, min_score=0.7)
        ]

        # Sort by relevance score (highest first)
        filtered_papers.sort(
            key=lambda x: x.get("_ai_relevance_score", 0), reverse=True
        )

        print(f"✅ Filtered to {len(filtered_papers)} highly relevant AI paper(s)")
        print(f"   📊 Filtered out: {len(all_papers) - len(filtered_papers)} papers")
        if all_papers:
            precision = len(filtered_papers) / len(all_papers) * 100
            print(f"   📊 Precision: {precision:.1f}%")

        # Show score distribution and field stats
        if filtered_papers:
            scores = [p.get("_ai_relevance_score", 0) for p in filtered_papers]
            has_ai_field_count = sum(
                1 for p in filtered_papers if p.get("_has_ai_field", False)
            )
            high_score_count = sum(
                1 for p in filtered_papers if p.get("_ai_relevance_score", 0) >= 0.7
            )

            print(f"   📊 Score range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"   📊 Average score: {sum(scores)/len(scores):.3f}")
            print(f"   📊 Papers with AI field/subfield: {has_ai_field_count}")
            print(f"   📊 Papers with score ≥ 0.7: {high_score_count}")

        if len(filtered_papers) == 0:
            print("ℹ️  INFO: No highly relevant AI papers found in the last 3 days.")

        return filtered_papers

    except Exception as e:
        print(f"❌ ERROR: Failed to fetch papers: {str(e)}")
        return []


def save_to_json(
    papers: List[Dict[str, Any]], output_dir: str = "temp"
) -> Optional[str]:
    """
    Save papers to a timestamped JSON file.

    Args:
        papers: List of paper dictionaries
        output_dir: Output directory (default: "temp")

    Returns:
        Path to the saved file or None if save failed
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"ai_papers_{timestamp}.json"
    filepath = output_path / filename

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved {len(papers)} paper(s) to: {filepath}")
        return str(filepath)

    except Exception as e:
        print(f"❌ ERROR: Failed to save JSON file: {str(e)}")
        return None


def main():
    """Main execution function."""
    print("=" * 70)
    print("OpenAlex AI Research Papers Fetcher")
    print("(Strict Filter: Score ≥ 0.7 OR AI Field/Subfield)")
    print("=" * 70)

    # Step 1: Find the AI concept
    concept_id = find_ai_concept()
    if not concept_id:
        print("\n❌ FATAL: Cannot proceed without concept ID")
        # Save empty JSON
        save_to_json([])
        return

    # Step 2: Fetch and filter AI papers by relevance
    papers = fetch_recent_ai_papers(concept_id, days=3)

    # Step 3: Save results (sorted by relevance score)
    save_to_json(papers)

    print("\n" + "=" * 70)
    print("✅ Script completed successfully!")
    print(f"📊 Final result: {len(papers)} highly relevant AI papers")
    print("   (Sorted by AI relevance score, highest first)")
    print("=" * 70)


if __name__ == "__main__":
    main()
