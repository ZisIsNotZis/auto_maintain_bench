def build_query(username):
    query = "SELECT * FROM users WHERE username = '%s'" % username
    return query
