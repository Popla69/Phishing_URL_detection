
class FastAPI:
    def __init__(self, **kwargs): 
        self.routes = {}
        
    def get(self, path, **kwargs):
        def decorator(func):
            self.routes[f"GET {path}"] = func
            return func
        return decorator
        
    def post(self, path, **kwargs):
        def decorator(func):
            self.routes[f"POST {path}"] = func
            return func
        return decorator
        
    def add_middleware(self, middleware, **kwargs): pass
    def add_exception_handler(self, exc, handler): pass
    def on_event(self, event): 
        def decorator(func): 
            return func
        return decorator

class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        
def Depends(dependency): return dependency

class status:
    HTTP_503_SERVICE_UNAVAILABLE = 503
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    HTTP_400_BAD_REQUEST = 400
    HTTP_404_NOT_FOUND = 404

class BackgroundTasks:
    def add_task(self, func, *args): pass

class CORSMiddleware: pass
class HTTPBearer: pass
