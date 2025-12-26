from flask import request, url_for

def generate_breadcrumbs():
    breadcrumbs = [{'label': 'Home', 'url': url_for('home')}]

    endpoint = request.endpoint
    view_args = request.view_args or {}

    if endpoint == 'all_stocks':
        breadcrumbs.append({'label': 'Stocks', 'url': url_for(endpoint)})

    elif endpoint == 'show_stock' and 'ticker' in view_args:
        breadcrumbs.append({'label': 'Stocks', 'url': url_for('all_stocks')})
        breadcrumbs.append({'label': view_args['ticker'], 'url': request.path})

    elif endpoint == 'all_indices':
        breadcrumbs.append({'label': 'Indices', 'url': url_for(endpoint)})

    elif endpoint == 'show_index' and 'index_id' in view_args:
        breadcrumbs.append({'label': 'Indices', 'url': url_for('all_indices')})
        breadcrumbs.append({'label': view_args['index_id'], 'url': request.path})

    elif endpoint == 'privacy':
        breadcrumbs.append({'label': 'Privacy', 'url': url_for(endpoint)})

    elif endpoint == 'terms':
        breadcrumbs.append({'label': 'Terms', 'url': url_for(endpoint)})

    elif endpoint == "watchlist.index":
        breadcrumbs.append({'label': 'Watchlist', 'url': url_for(endpoint)})

    elif endpoint == "watchlist.alerts":
        breadcrumbs.append({'label': 'Watchlist', 'url': url_for("watchlist.index")})
        breadcrumbs.append({'label': 'Alerts', 'url': url_for(endpoint)})

    elif endpoint == "auth.signup":
        breadcrumbs.append({'label': 'Sign Up', 'url': url_for(endpoint)})

    elif endpoint == "auth.login":
        breadcrumbs.append({'label': 'Log In', 'url': url_for(endpoint)})

    elif endpoint == "auth.settings_profile":
        breadcrumbs.append({'label': 'Settings', 'url': url_for("auth.settings")})
        breadcrumbs.append({'label': 'Profile', 'url': url_for(endpoint)})

    elif endpoint == "auth.settings_account":
        breadcrumbs.append({'label': 'Settings', 'url': url_for("auth.settings")})
        breadcrumbs.append({'label': 'Account', 'url': url_for(endpoint)})

    elif endpoint == "auth.settings_set_password":
        breadcrumbs.append({'label': 'Settings', 'url': url_for("auth.settings")})
        breadcrumbs.append({'label': 'Set Password', 'url': url_for(endpoint)})

    elif endpoint == "auth.reset_password_request":
        breadcrumbs.append({'label': 'Reset Password Request', 'url': url_for(endpoint)})

    elif endpoint == "auth.reset_password":
        breadcrumbs.append({'label': 'Reset Password', 'url': request.path})

    elif endpoint == "auth.delete_account":
        breadcrumbs.append({'label': 'Delete Account', 'url': request.path})

    return breadcrumbs