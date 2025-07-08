from flask import request, url_for

def generate_breadcrumbs():
    breadcrumbs = [{'label': 'Home', 'url': url_for('home')}]

    endpoint = request.endpoint
    view_args = request.view_args or {}

    if endpoint == 'all_stocks':
        breadcrumbs.append({'label': 'Stocks', 'url': url_for('all_stocks')})

    elif endpoint == 'show_stock' and 'ticker' in view_args:
        breadcrumbs.append({'label': 'Stocks', 'url': url_for('all_stocks')})
        breadcrumbs.append({'label': view_args['ticker'], 'url': request.path})

    elif endpoint == 'all_indexes':
        breadcrumbs.append({'label': 'Indexes', 'url': url_for('all_indexes')})

    elif endpoint == 'show_index' and 'index_id' in view_args:
        breadcrumbs.append({'label': 'Indexes', 'url': url_for('all_indexes')})
        breadcrumbs.append({'label': view_args['index_id'], 'url': request.path})

    return breadcrumbs