from elasticsearch import Elasticsearch

# Connect to your local Elasticsearch instance
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

# Name of your index
index_name = 'recipes'

# Search for documents in the index
res = es.search(index=index_name, body={"query": {"match_all": {}}}, size=5)

print(f"Total hits: {res['hits']['total']['value']}")
for hit in res['hits']['hits']:
    print(hit['_source']) 