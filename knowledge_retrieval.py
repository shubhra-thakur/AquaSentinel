
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_FILE = BASE_DIR / "knowledge_base" / "water_conservation.json"


def load_knowledge_base(file_path=KNOWLEDGE_FILE):
    """Load and validate the local water conservation knowledge base."""

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge base file not found: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in knowledge base: {error}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError("Knowledge base must contain a JSON object.")

    records = data.get("knowledge_base")

    if not isinstance(records, list):
        raise ValueError(
            "Knowledge base must contain a 'knowledge_base' list."
        )

    required_fields = {
        "id",
        "category",
        "title",
        "keywords",
        "content",
        "actions",
        "priority"
    }

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(
                f"Invalid record at position {index}."
            )

        missing_fields = required_fields - set(record.keys())

        if missing_fields:
            raise ValueError(
                f"Record {index} is missing fields: "
                f"{', '.join(sorted(missing_fields))}"
            )

        if not isinstance(record["keywords"], list):
            raise ValueError(
                f"Keywords must be a list in record {record['id']}."
            )

        if not isinstance(record["actions"], list):
            raise ValueError(
                f"Actions must be a list in record {record['id']}."
            )

    return records


def search_knowledge(query, category=None, top_k=3):
    """
    Retrieve relevant knowledge using simple keyword matching.

    This is lightweight local retrieval, not a full generative RAG system.
    """

    if not isinstance(query, str) or not query.strip():
        return []

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    records = load_knowledge_base()
    query_words = set(query.lower().split())

    results = []

    for record in records:

        if category and record["category"].lower() != category.lower():
            continue

        searchable_text = " ".join(
            [
                record["title"],
                record["content"],
                *record["keywords"]
            ]
        ).lower()

        searchable_words = set(searchable_text.split())

        matched_words = query_words.intersection(searchable_words)

        score = len(matched_words)

        if score > 0:
            result = record.copy()
            result["relevance_score"] = score
            results.append(result)

    results.sort(
        key=lambda item: item["relevance_score"],
        reverse=True
    )

    return results[:top_k]


def get_knowledge_response(query, category=None):
    """Return a structured advisory response from retrieved knowledge."""

    results = search_knowledge(query, category=category)

    if not results:
        return {
            "success": False,
            "message": (
                "No directly relevant guidance was found. "
                "Please verify the issue manually."
            ),
            "recommendations": [],
            "sources": []
        }

    recommendations = []

    for record in results:
        for action in record["actions"]:
            if action not in recommendations:
                recommendations.append(action)

    return {
        "success": True,
        "message": "Relevant guidance retrieved successfully.",
        "recommendations": recommendations,
        "sources": [
            {
                "id": record["id"],
                "title": record["title"],
                "category": record["category"],
                "priority": record["priority"],
                "relevance_score": record["relevance_score"]
            }
            for record in results
        ]
    }


if __name__ == "__main__":

    print("\n========== AQUASENTINEL KNOWLEDGE RETRIEVAL ==========")

    test_query = "How can I reduce household water leakage?"

    response = get_knowledge_response(test_query)

    print("\nQuery:", test_query)
    print("\nStatus:", response["success"])
    print("\nRecommendations:")

    for recommendation in response["recommendations"]:
        print("-", recommendation)

    print("\nKnowledge Sources:")

    for source in response["sources"]:
        print("-", source["title"], "|", source["priority"])

    print("\n======================================================")
