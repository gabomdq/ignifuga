"""
    rfoo/_rfoo.py

    Fast RPC server.

    Copyright (c) 2010 Nir Aides <nir@winpdb.org> and individual contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification,
    are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright 
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

    3. Neither the name of Nir Aides nor the names of other contributors may 
    be used to endorse or promote products derived from this software without
    specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
    Example:

    class MyHandler(rfoo.BaseHandler):
        def echo(self, str):
            return str

    rfoo.InetServer(MyHandler).start()

    --- client---

    c = rfoo.InetConnection().connect()
    Proxy(c).echo('Hello World!')
"""



import threading
import logging
import inspect
import socket
import sys
import os

import marshal as _marshal

try:
    from ignifuga.rfoo.marsh import dumps, loads
except ImportError:
    sys.stderr.write("""
===========================================================    
Did you just try to import rfoo directly from its source distribution?
Well, that's possible, but first you need to build the 
Cython extension ignifuga.rfoo.marsh (inplace) with:
    python setup.py build_ext --inplace
===========================================================\n""")
    raise

try:
    import thread
except ImportError:
    import _thread as thread

try:
    import __builtin__ as builtins
except ImportError:
    import builtins



#
# Bind to loopback to restrict server to local requests, by default.
#
LOOPBACK = '127.0.0.1'
DEFAULT_PORT = 52431
BUFFER_SIZE = 4096

MAX_THREADS = 128

CALL = 0
NOTIFY = 1

# Compatible way to represent binary 'i' across Py2.x Py3.x.
INTEGER = 'i'.encode()[0]



_loads = _marshal.loads
_dumps = _marshal.dumps



def _is_builtin_exception(t):
    # Use try except or find way to tell a class in Python 2.4.
    try:
        return issubclass(t, Exception)
    except:
        return False



BUILTIN_EXCEPTIONS = set(e for e in vars(builtins).values() if _is_builtin_exception(e))
BUILTIN_EXCEPTIONS_NAMES = set(e.__name__ for e in BUILTIN_EXCEPTIONS)



class ServerError(IOError):
    """Wrap server errors by proxy."""



class EofError(IOError):
    """Socket end of file."""



class BaseHandler(object):
    """
    Handle incomming requests.
    Client can call public methods of derived classes.
    """

    def __init__(self, addr=None, context=None):
        self._addr = addr
        self._context = context
        self._methods = {}

    def _close(self):
        self._methods = {}

    def _get_method(self, name):
        """
        Get public method.
        Verify attribute is public method and use cache for performance.
        """

        m = self._methods.get(name, None)
        if m is not None:
            return m

        if name in ('trait_names', '_getAttributeNames'):
            return self._getAttributeNames

        if name.startswith('_'):
            logging.warning('Attempt to get non-public, attribute=%s.', name)
            raise ValueError(name)

        m = getattr(self, name)
        if not inspect.ismethod(m):
            logging.warning('Attempt to get non-method, attribute=%s.', name)
            raise ValueError(name)

        self._methods[name] = m

        return m

    def _getAttributeNames(self, *args, **kwargs):
        """Return list of public methods.
        Support auto completion by IPython of proxy methods over network.
        """
        
        members = inspect.getmembers(self, inspect.ismethod)
        return [m[0] for m in members if not m[0].startswith('_')]


def restrict_local(foo):
    """Decorator to restrict handler method to local proxies only."""

    def _restrict_local(self, *args, **kwargs):
        if self._addr[0] != '127.0.0.1':
            raise ValueError('Attempt to invoke method from remote address.')
        return foo(self, *args, **kwargs)
    
    return _restrict_local



class ExampleHandler(BaseHandler):
    """
    Demonstrate handler inheritance.
    Start server with: start_server(handler=ExampleHandler)
    Client calls server with: Proxy(connection).add(...)
    """

    def add(self, x, y):
        return x + y

    def echo(self, s):
        return s



class Connection(object):
    """Wrap socket with buffered read and length prefix for data."""

    def __init__(self, conn=None):
        self._conn = conn
        self.recv = self._conn.recv

    def close(self):
        """Shut down and close socket."""

        if self._conn is not None:
            try:
                self._conn.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            self._conn.close()

    def write(self, data):
        """Write length prefixed data to socket."""
        
        l = _dumps(len(data))
        self._conn.sendall(l + data)

    def read(self):
        """Read length prefixed data from socket."""

        buffer = self.recv(5)
        while len(buffer) < 5:
            data = self.recv(5 - len(buffer))
            if not data:
                raise EofError(len(buffer))
            buffer += data

        if buffer[0] != INTEGER:
            raise IOError()

        length = _loads(buffer)
        buffer = self.recv(length)
        while len(buffer) < length:
            data = self.recv(length - len(buffer))
            if not data:
                raise EofError(len(buffer))
            buffer += data

        return buffer



class InetConnection(Connection):
    """Connection type for INET sockets."""

    def __init__(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        Connection.__init__(self, s)

    def connect(self, host=LOOPBACK, port=DEFAULT_PORT):
        self._conn.connect((host, port))
        return self

        

class UnixConnection(Connection):
    """Connection type for Unix sockets."""

    def __init__(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        Connection.__init__(self, s)

    def connect(self, path):
        self._conn.connect(path)
        return self



class PipeSocket(object):
    """Abstract two pipes into socket like interface."""

    def __init__(self, to_server=None, to_client=None):
        self._to_server = to_server or os.pipe()
        self._to_client = to_client or os.pipe()

    def connect(self):
        self._r = self._to_client[0]
        self._w = self._to_server[1]

    def _connect_server(self):
        server_end = PipeSocket(self._to_server, self._to_client)
        server_end._r = self._to_server[0]
        server_end._w = self._to_client[1]
        return server_end

    def recv(self, size):
        return os.read(self._r, size)

    def sendall(self, data):
        return os.write(self._w, data)

    def shutdown(self, x):
        pass

    def close(self):
        try:
            os.close(self._to_server[0])
            os.close(self._to_server[1])
            os.close(self._to_client[0])
            os.close(self._to_client[1])
        except Exception:
            pass



class PipeConnection(Connection):
    """Connection type for pipes."""

    def connect(self, pipe_socket):
        self._conn = pipe_socket
        self._conn.connect()
        return self



class Proxy(object):
    """Proxy methods of server handler.
    Call Proxy(connection).foo(*args, **kwargs) to invoke method
    handler.foo(*args, **kwargs) of server handler.
    """

    def __init__(self, conn, name=None, cache=True):
        self._conn = conn
        self._name = name
        self._cache = True

    def __getattr__(self, name):
        attr = type(self)(self._conn, name, self._cache)

        if self._cache:
            self.__dict__[name] = attr.__call__

        return attr.__call__

    def __call__(self, *args, **kwargs):
        """Call method on server."""
       
        data = dumps((CALL, self._name, args, kwargs))
        self._conn.write(data)
        
        response = self._conn.read()
        value, error = loads(response)
        
        if error is None:
            return value

        try:
            name, args = error
        except TypeError:
            # Handle old way of returning error as repr.
            logging.warning('Unknown error returned by proxy, error=%s.', error)
            raise ServerError(error)

        logging.warning('Error returned by proxy, name=%s, args=%s.', name, args)

        # Raise built-in exceptions sent by server.
        if name in BUILTIN_EXCEPTIONS_NAMES:
            e = getattr(builtins, name)()
            e.args = args
            raise e # Exception sent from server. Original traceback unavailable.

        self._on_exception(name, args)

    def _on_exception(self, name, args):
        """Override to raise custom exceptions."""

        raise ServerError(name, args)
            


class Notifier(Proxy):
    """Proxy methods of server handler, asynchronously.
    Call Notifier(connection).foo(*args, **kwargs) to invoke method
    handler.foo(*args, **kwargs) of server handler.
    """

    def __call__(self, *args, **kwargs):
        """Call method on server, don't wait for response."""
       
        data = dumps((NOTIFY, self._name, args, kwargs))
        self._conn.write(data)
        


g_threads_semaphore = threading.Semaphore(MAX_THREADS)

def run_in_thread(foo):
    """Decorate to run foo using bounded number of threads."""

    def wrapper1(*args, **kwargs):
        try:
            foo(*args, **kwargs)
        finally:
            g_threads_semaphore.release()

    def wrapper2(*args, **kwargs):
        g_threads_semaphore.acquire()
        thread.start_new_thread(wrapper1, args, kwargs)

    return wrapper2



class Server(object):
    """Serve calls over connection."""

    def __init__(self, handler_type, handler_context=None, conn=None):
        self._handler_context = handler_context
        self._handler_type = handler_type
        self._conn = conn
    
    def close(self):
        if self._conn is not None:
            try:
                self._conn.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            self._conn.close()

    def start(self):
        """Start server, is it?
        Socket is excpted bound.
        """

        logging.info('Enter.')

        try:
            self._conn.listen(5)

            while True:
                conn, addr = self._conn.accept()
                conn.settimeout(None)
                self._on_accept(conn, addr)

        finally:
            self.close()

    def _on_accept(self, conn, addr):
        """Serve acceptted connection.
        Should be used in the context of a threaded server, see 
        threaded_connection(), or fork server (not implemented here).
        """

        logging.info('Enter, addr=%s.', addr)

        c = Connection(conn)

        try:
            #
            # Instantiate handler for the lifetime of the connection,
            # making it possible to manage a state between calls.
            #
            handler = self._handler_type(addr, self._handler_context)

            try:
                while True:
                    self._dispatch(handler, c)

            except EofError:
                logging.debug('Caught end of file, error=%r.', sys.exc_info()[1])

        finally:
            c.close()
            if 'handler' in locals():
                handler._close()

    def _dispatch(self, handler, conn, n=1000):
        """Serve single call."""

        for i in range(n):
            data = conn.read()
            type, name, args, kwargs = loads(data)

            try:    
                foo = handler._methods.get(name, None) or handler._get_method(name)
                result = foo(*args, **kwargs)
                error = None

            except Exception:
                logging.debug('Caught exception raised by callable.', exc_info=True)
                # Use exc_info for py2.x py3.x compatibility.
                t, v, tb = sys.exc_info()
                if t in BUILTIN_EXCEPTIONS:
                    error = (t.__name__, v.args)
                else:
                    error = (repr(t), v.args)
                result = None

            if type == CALL:
                response = dumps((result, error))
                conn.write(response)



class InetServer(Server):
    """Serve calls over INET sockets."""
    
    def __init__(self, handler_type, handler_context=None):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(None)
        Server.__init__(self, handler_type, handler_context, s)

    def start(self, host=LOOPBACK, port=DEFAULT_PORT):
        self._conn.bind((host, port))
        Server.start(self) 

    _on_accept = run_in_thread(Server._on_accept)



class UnixServer(Server):
    """Serve calls over Unix sockets."""
    
    def __init__(self, handler_type, handler_context=None):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(None)
        Server.__init__(self, handler_type, handler_context, s)

    def start(self, path):
        self._conn.bind(path)
        Server.start(self) 

    _on_accept = run_in_thread(Server._on_accept)



class PipeServer(Server):
    """Serve calls over pipes."""

    def start(self, pipe_socket):
        self._conn = pipe_socket._connect_server()
        self._on_accept(self._conn, 'pipes')
   


def start_server(handler, host=LOOPBACK, port=DEFAULT_PORT):
    "Start server - depratcated."""

    InetServer(handler).start(host, port)



def connect(host=LOOPBACK, port=DEFAULT_PORT):
    """Connect to server - depracated."""

    return InetConnection().connect(host, port)




class QueueInetServer(InetServer):
    """ A queueing inet server for Ignifuga, this one stores commands in a buffer for processing in the main thread
    and sets up the current scene namespace as if the commands where run from a component """
    def __init__(self, handler_type, handler_context=None, staticglobals=False):
        super(QueueInetServer, self).__init__(handler_type, handler_context)

        self.inBuf = []
        self.staticglobals = staticglobals

    def _on_accept(self, conn, addr):
        """Serve acceptted connection.
        Should be used in the context of a threaded server, see
        threaded_connection(), or fork server (not implemented here).
        """

        logging.info('Enter, addr=%s.', addr)

        c = Connection(conn)

        try:
            #
            # Instantiate handler for the lifetime of the connection,
            # making it possible to manage a state between calls.
            #
            handler = self._handler_type(addr, self._handler_context)

            try:
                while True:
                    data = c.read()
                    type, name, args, kwargs = loads(data)
                    # Buffer the call for later processing with self.process
                    self.inBuf.append((handler, c, type, name, args, kwargs))
            except EofError:
                logging.debug('Caught end of file, error=%r.', sys.exc_info()[1])

        finally:
            c.close()
            if 'handler' in locals():
                handler._close()

    def process(self):
        """Process buffered incoming calls"""
        if self.inBuf and not self.staticglobals:
            # We change the namespace available on each call, kinda hacky and certainly slow...but hey, it works and the scene is dinamically available to you
            from ignifuga.Gilbert import Gilbert
            from ignifuga.rfoo.utils.rconsole import BufferedInterpreter
            import rlcompleter

            gilbert = Gilbert()

        while self.inBuf:
            handler, conn, type, name, args, kwargs = self.inBuf.pop(0)

            try:

                if not self.staticglobals:
                    if gilbert.scene != None:
                        self._handler_context = gilbert.scene.runEnv
                    else:
                        self._handler_context = globals()

                    handler._namespace = self._handler_context
                    handler._interpreter = BufferedInterpreter(handler._namespace)
                    handler._completer = rlcompleter.Completer(handler._namespace)

                foo = handler._methods.get(name, None) or handler._get_method(name)
                result = foo(*args, **kwargs)
                error = None

            except Exception:
                print 'Caught exception raised by callable.'
                # Use exc_info for py2.x py3.x compatibility.
                t, v, tb = sys.exc_info()
                if t in BUILTIN_EXCEPTIONS:
                    error = (t.__name__, v.args)
                else:
                    error = (repr(t), v.args)
                result = None

            if type == CALL:
                response = dumps((result, error))
                conn.write(response)

