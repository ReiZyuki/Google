from .observer import observer


def run_with_fallback(url, operation, cookie_paths=None):
    cookie_paths = list(cookie_paths or [])
    ranked = observer.rank_cookies(url, cookie_paths) if cookie_paths else []
    proven = [x for x in ranked if x[2] == 100.0 and x[0] >= 50.0]
    normal = [x for x in ranked if x[1] not in {p[1] for p in proven}]
    ordered = proven + normal
    last_error = None

    def attempt(cookie):
        nonlocal last_error
        if cookie is not None:
            observer.save_attempt(url, cookie)
        try:
            result = operation(cookie)
            if cookie is not None:
                observer.save_success(url, cookie)
            return True, result
        except Exception as exc:
            last_error = exc
            return False, None

    if proven:
        ok, result = attempt(proven[0][1])
        if ok:
            return result
        ok, result = attempt(None)
        if ok:
            return result
        for _, cookie, _ in ordered:
            if cookie == proven[0][1]:
                continue
            ok, result = attempt(cookie)
            if ok:
                return result
    else:
        ok, result = attempt(None)
        if ok:
            return result
        for _, cookie, _ in ordered:
            ok, result = attempt(cookie)
            if ok:
                return result
    if last_error is not None:
        raise last_error
    raise RuntimeError("Operation failed")
