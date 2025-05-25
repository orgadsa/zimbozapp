"""
Elasticsearch Index Setup Script for Zimbozapp
- Creates the 'recipes' index with the required mapping if it does not exist
"""
import sys
sys.path.append('/app')
from elasticsearch import Elasticsearch
from config.config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_INDEX

# Define the mapping for the recipes index
mapping = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "text"},
            "ingredients": {"type": "text"},
            "instructions": {"type": "text"}
        }
    }
}

def create_index():
    """Create the recipes index in Elasticsearch if it does not exist."""
    es = Elasticsearch([{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT}])
    if not es.indices.exists(index=ELASTICSEARCH_INDEX):
        es.indices.create(index=ELASTICSEARCH_INDEX, body=mapping)
        print(f"Index '{ELASTICSEARCH_INDEX}' created.")
    else:
        print(f"Index '{ELASTICSEARCH_INDEX}' already exists.")

if __name__ == "__main__":
    create_index() 