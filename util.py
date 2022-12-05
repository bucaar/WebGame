
def parse_url_path(path: str) -> list[str]:
    if path.startswith("/"):
        path = path[1:]
    
    return path.split("/")