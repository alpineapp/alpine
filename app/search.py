from flask import current_app
from flask_login import current_user

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    if hasattr(model, 'user_id'):
        payload['user_id'] = model.user_id
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    query_str = {
        "query": {
            "bool": {
                "must": {
                    'multi_match': {
                        'query': query,
                        'fields': ['*']
                    }
                },
                "filter": {
                    "term": {"user_id": current_user.id}
                }
            }
        },
        'from': (page - 1) * per_page,
        'size': per_page
    }
    search = current_app.elasticsearch.search(
        index=index,
        body=query_str)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']
