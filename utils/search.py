from sqlalchemy.orm import Session
from Levenshtein import distance as levenshtein_distance
import models


def search_listings(db: Session, search_query: str = "", sort_by: str = None):
    """
    Search listings using Levenshtein distance.

    Args:
        db (Session): Database session
        search_query (str): Search query string
        sort_by (str, optional): Sort field ('title', 'price', etc.)

    Returns:
        list: Sorted list of listings matching the search query
    """
    # Get all listings
    listings = db.query(models.Listing).all()

    if not search_query:
        return listings

    # Normalize search query
    search_query = search_query.lower().strip()

    def calculate_similarity_score(listing):
        """Calculate similarity score for a listing based on multiple fields"""
        title_distance = levenshtein_distance(listing.title.lower(), search_query)
        description_distance = levenshtein_distance(
            listing.description.lower(), search_query
        )
        price_str = str(listing.price)
        price_distance = levenshtein_distance(price_str, search_query)

        # Return the minimum distance (closest match) among all fields
        return min(title_distance, description_distance, price_distance)

    # Sort listings by similarity score
    sorted_listings = sorted(listings, key=calculate_similarity_score)

    return sorted_listings
