"""
    rconsole.py

    A Python console you can embed in a program and attach to remotely.

    To spawn a Python console in a script do the following in global scope
    only (!) of any module:

    from rfoo.utils import rconsole
    rconsole.spawn_server()

    This will start a listener for connections in a new thread. You may
    specify a port to listen on.

    To attach to the console from another shell use the rconsole script
    (rfoo/scripts/rconsole) which may be installed in your path. 
    Alternatively you may simply invoke interact().

    SECURITY NOTE:
    The listener started with spawn_server() will accept any local 
    connection and may therefore be insecure to use in shared hosting
    or similar environments!
"""


import rlcompleter
import logging
import pprint
import codeop
import socket
import code
import rfoo
import sys

try:
    import thread
except ImportError:
    import _thread as thread


PORT = 54321


class BufferedInterpreter(code.InteractiveInterpreter):
    """Variation of code.InteractiveInterpreter that outputs to buffer."""

    def __init__(self, *args, **kwargs):
        code.InteractiveInterpreter.__init__(self, *args, **kwargs)
        self.buffout = ''

    def write(self, data):
        self.buffout += data


class ConsoleHandler(rfoo.BaseHandler):
    """An rfoo handler that remotes a Python interpreter."""

    def __init__(self, *args, **kwargs):
        rfoo.BaseHandler.__init__(self, *args, **kwargs)
        
        self._namespace = self._context
        self._interpreter = BufferedInterpreter(self._namespace)
        self._completer = rlcompleter.Completer(self._namespace)

    @rfoo.restrict_local
    def complete(self, phrase, state):
        """Auto complete for remote console."""
        logging.debug('Enter, phrase=%r, state=%d.', phrase, state)
        return self._completer.complete(phrase, state)

    @rfoo.restrict_local
    def runsource(self, source, filename="<input>"):
        """Variation of InteractiveConsole which returns expression 
        result as second element of returned tuple.
        """

        logging.debug('Enter, source=%r.', source)

        # Inject a global variable to capture expression result.
        self._namespace['_rcon_result_'] = None

        try:
            # In case of an expression, capture result.
            compile(source, '<input>', 'eval')
            source = '_rcon_result_ = ' + source
            logging.debug('source is an expression.')
        except SyntaxError:
            pass

        more = self._interpreter.runsource(source, filename)
        result = self._namespace.pop('_rcon_result_')
        
        if more is True:
            logging.debug('source is incomplete.')
            return True, ''
        
        output = self._interpreter.buffout
        self._interpreter.buffout = ''

        if result is not None:
            result = pprint.pformat(result)
            output += result + '\n'
         
        return False, output


class ProxyConsole(code.InteractiveConsole):
    """Proxy interactive console to remote interpreter."""

    def __init__(self, port=PORT):
        code.InteractiveConsole.__init__(self)
        self.port = port
        self.conn = None

    def interact(self, banner=None):
        logging.info('Enter.')
        self.conn = rfoo.InetConnection().connect(port=self.port)
        return code.InteractiveConsole.interact(self, banner)

    def complete(self, phrase, state):
        """Auto complete support for interactive console."""
        
        logging.debug('Enter, phrase=%r, state=%d.', phrase, state)

        # Allow tab key to simply insert spaces when proper.
        if phrase == '':
            if state == 0:
                return '    '
            return None

        return rfoo.Proxy(self.conn).complete(phrase, state)
    
    def runsource(self, source, filename="<input>", symbol="single"):
        logging.debug('Enter, source=%r.', source)

        more, output = rfoo.Proxy(self.conn).runsource(source, filename)
        if output:
            self.write(output)

        return more


def spawn_server(namespace=None, port=PORT):
    """Start console server in a new thread.
    Should be called from global scope only!
    May be insecure on shared machines.
    """

    logging.info('Enter, port=%d.', port)

    if namespace is None:
        namespace = sys._getframe(1).f_globals
    
    server = rfoo.InetServer(ConsoleHandler, namespace)

    def _wrapper():
        try:
            server.start(rfoo.LOOPBACK, port)
        except socket.error:
            logging.warning('Failed to bind rconsole to socket port, port=%r.', port)

    thread.start_new_thread(_wrapper, ())


def interact(banner=None, readfunc=None, port=PORT):
    """Start console and connect to remote console server."""

    logging.info('Enter, port=%d.', port)

    console = ProxyConsole(port)

    if readfunc is not None:
        console.raw_input = readfunc
    else:
        try:
            import readline
            readline.set_completer(console.complete)
            readline.parse_and_bind('tab: complete')
        except ImportError:
            pass

    console.interact(banner)


