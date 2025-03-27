import json
from datetime import datetime
from typing import Any, Dict, List, Union
from bson import ObjectId
from fastapi import HTTPException, status
import re

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle MongoDB ObjectId and datetime objects."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def json_serialize(obj: Any) -> str:
    """Convert an object to a JSON string."""
    return json.dumps(obj, cls=JSONEncoder)

def validate_object_id(id_str: str) -> bool:
    """Validate if a string is a valid MongoDB ObjectId."""
    try:
        ObjectId(id_str)
        return True
    except Exception:
        return False

def parse_query_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate query parameters."""
    parsed_params = {}
    
    # Handle pagination
    if 'page' in params:
        try:
            page = int(params['page'])
            if page < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page must be a positive integer"
                )
            parsed_params['page'] = page
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid page parameter"
            )
    
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if limit < 1 or limit > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Limit must be between 1 and 100"
                )
            parsed_params['limit'] = limit
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid limit parameter"
            )
    
    # Handle date filters
    for date_param in ['start_date', 'end_date']:
        if date_param in params and params[date_param]:
            try:
                parsed_params[date_param] = datetime.fromisoformat(params[date_param])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {date_param} format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
    
    # Pass through other parameters
    for key, value in params.items():
        if key not in ['page', 'limit', 'start_date', 'end_date']:
            parsed_params[key] = value
    
    return parsed_params

def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract potential keywords from text by removing stopwords and selecting
    frequent words or phrases.
    """
    if not text:
        return []
    
    # Convert to lowercase and split into words
    text = text.lower()
    
    # Remove special characters and extra spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Simple list of common English stopwords
    stopwords = {
        'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'am', 'was', 'were',
        'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 'by',
        'about', 'against', 'between', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'from', 'up', 'down', 'of', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just',
        'don', 'should', 'now'
    }
    
    words = text.split()
    
    # Filter out stopwords
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Count word frequencies
    word_counts = {}
    for word in filtered_words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    
    # Sort by frequency and get top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N keywords
    return [word for word, count in sorted_words[:max_keywords]]
