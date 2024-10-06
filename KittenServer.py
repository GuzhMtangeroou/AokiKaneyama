import ssl
import http,http.server
import json
import os,sys
import traceback,ast
import importlib
import flask,logging
from Lib import*
ERROR_OK = 0
ERROR_INVALID_REQUEST = 65

ERROR_FUNCTION_NOT_FOUND = 1
ERROR_FUNCTION_PARAMS_ERROR = 2
ERROR_IMPORT_ERROR = 3
ERROR_RUNTIME_ERROR = 4

ERROR_GET_FUNCTIONS = 16

g_kw_tmp_mod = None

class RequestHandler(http.server.BaseHTTPRequestHandler):

    py_module_loaded = False

    def log_message(self, format, *args):
        """Override log_message() in parent class, do not print log to stderr.

        :param format:
        :param args:
        :return:
        """
        pass

    def do_OPTIONS(self):
        # Support CORS
        self.send_response(http.HTTPStatus.OK)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Accept", "application/json")
        self.send_header("Access-Control-Request-Method", "POST")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        self.send_response(http.HTTPStatus.OK)
        self.send_header("Content-Type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        msg = b"hello, kw"
        self.send_header("Content-Length", len(msg))
        self.end_headers()
        self.wfile.write(msg)

    def do_POST(self):
        self.send_response(http.HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            req_data = self.rfile.read(int(self.headers.get('Content-Length')))
            req_json = json.loads(req_data.decode())
            resp_obj = handle_kw_req(req_json)
        except Exception as err:
            traceback.print_exc()
            resp_obj = new_reply(ERROR_INVALID_REQUEST, str(err))

        try:
            self.wfile.write(json.dumps(resp_obj).encode())
        except Exception as err:
            traceback.print_exc()

class Request(object):

    ACTION_EXEC_FUNC = "execFunc"
    ACTION_GET_FUNCTIONS = "getFunctions"

    def __init__(self, action, param, py_params):
        super().__init__()
        self.action = action
        self.param = param
        self.py_params = py_params

    @classmethod
    def parse(cls, obj: dict):
        """Parse kitten request msg.

        May raise KeyError or TypeError exceptions
        """
        try:
            # Be compactible with kitten xhr framework.
            # All the payload messages are placed in {"data": xxx} property.
            if "data" in obj:
                obj = obj["data"]
            action = obj["action"]
            param = obj["param"]
            py_params = obj["pyParams"]
        except KeyError as err:
            raise err

        if action != cls.ACTION_EXEC_FUNC and \
                action != cls.ACTION_GET_FUNCTIONS:
            raise KeyError("Invalid action, ", action)
        if not isinstance(param, str):
            raise TypeError("param expected to be string")
        if not isinstance(py_params, list):
            raise TypeError("py_params expected to be a list")
        req = Request(action, param, py_params)
        return req

    def is_exec_func_action(self):
        return self.action == self.ACTION_EXEC_FUNC

    def is_get_functions_action(self):
        return self.action == self.ACTION_GET_FUNCTIONS

def load_module(py_path: str):
    """Load py module into current context"""
    global g_kw_tmp_mod
    dirname, filename = os.path.split(py_path)
    basename, _extname_ = os.path.splitext(filename)
    if g_kw_tmp_mod:
        g_kw_tmp_mod = importlib.reload(g_kw_tmp_mod)
    else:
        if dirname not in sys.path:
            sys.path.append(dirname)
        g_kw_tmp_mod = importlib.import_module(basename)

def get_functions(py_path: str):
    """Parse AST in python module and returns function list"""
    with open(py_path) as fh:
        data = fh.read()
    _dirname, filename = os.path.split(py_path)
    tree = ast.parse(data, filename)
    functions = []
    for obj in tree.body:
        if isinstance(obj, ast.FunctionDef):
            functions.append({
                "name": obj.name,
                "argCount": len(obj.args.args),
                "defaultCount": len(obj.args.defaults),
                "hasVarArgs": obj.args.vararg is not None,
                "hasKwArgs": obj.args.kwarg is not None,
            })
    return functions

def exec_function(function_name, args):
    """Execute a function in a module.
    
    Call load_module() to init module context first"""
    # Remember to capture exceptions.
    assert g_kw_tmp_mod
    func = getattr(g_kw_tmp_mod, function_name)
    return func(*args)

app = flask.Flask(__name__)
@app.route("/")
def hello():
    return "Hello, world"

@app.route("/kw", methods=["POST"])
def kw():
    try:
        req_json = flask.request.json
        resp_json = handle_kw_req(req_json)
        return flask.jsonify(resp_json)
    except Exception as err:
        print(err)
        return flask.jsonify(new_reply(
            ERROR_INVALID_REQUEST,
            str(err)
        ))

def new_reply(errno, result):
    return {
            "errno": errno,
            "result": result,
            }


g_py_module_loaded = False
def load_py_module():
    global g_py_module_loaded
    if g_py_module_loaded:
        return
    # May raise IndexError.
    py_path = f"{os.getcwd()}\plugins\KittenLink.py"
    # May raise ModuleNotFoundError.
    load_module(py_path)
    g_py_module_loaded = True

def handle_kw_req(req_json):
    try:
        req = Request.parse(req_json)
    except Exception as err:
        traceback.print_exc()
        return new_reply(ERROR_INVALID_REQUEST, str(err))
    try:
        # Load module into current context before executing.
        load_py_module()
    except IndexError as err:
        traceback.print_exc()
        return new_reply(ERROR_RUNTIME_ERROR, str(err))
    except Exception as err:
        traceback.print_exc()
        return new_reply(ERROR_IMPORT_ERROR, str(err))

    if req.is_exec_func_action():
        try:
            ret = exec_function(req.param, req.py_params)
            return new_reply(ERROR_OK, ret)
        except ModuleNotFoundError as err:
            traceback.print_exc()
            return new_reply(ERROR_IMPORT_ERROR, str(err))
        except AttributeError as err:
            traceback.print_exc()
            expected_error = F" has no attribute '{req.param}'"
            if err.args and expected_error in err.args[0]:
                return new_reply(ERROR_FUNCTION_NOT_FOUND, str(err))
            else:
                return new_reply(ERROR_RUNTIME_ERROR, str(err))
        except TypeError as err:
            traceback.print_exc()
            expected_error = F"{req.param}() takes"
            if err.args and expected_error in err.args[0]:
                return new_reply(ERROR_FUNCTION_PARAMS_ERROR, str(err))
            else:
                return new_reply(ERROR_RUNTIME_ERROR, str(err))
        except Exception as err:
            traceback.print_exc()
            return new_reply(ERROR_RUNTIME_ERROR, str(err))
    else:
        return new_reply(ERROR_INVALID_REQUEST, "Invalid action type")

def start_server():
    server_address = ("", 8964)
    cert_path = os.path.abspath(os.path.join(os.path.expanduser('~'), '.wood/cert'))
    cert_file_path = os.path.join(cert_path, 'wood.cert.pem')
    key_file_path = os.path.join(cert_path, 'wood.key.pem')
    httpd = http.server.HTTPServer(server_address, RequestHandler)
    httpd.socket = ssl.wrap_socket(
        httpd.socket,
        certfile=cert_file_path,
        keyfile=key_file_path,
        server_side=True,
        )
    httpd.serve_forever()

def main(py_path,dirname):
    if os.path.exists(py_path):
        os.chdir(dirname)
    else:
        print("File not found:", py_path)

    start_server()


if __name__ == "__main__":
    main(os.getcwd(),os.getcwd())