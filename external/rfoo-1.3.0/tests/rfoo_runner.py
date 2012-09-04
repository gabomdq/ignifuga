#! /usr/bin/env python

"""
    tests/rfoo_runner.py

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



import threading
import logging
import getopt
import time
import rfoo
import sys
import os



#
# Python 2.5 logging module supports function name in format string. 
#
if logging.__version__[:3] >= '0.5':
    LOGGING_FORMAT = '[%(process)d:%(thread).5s] %(asctime)s %(levelname)s %(module)s:%(lineno)d %(funcName)s() - %(message)s'
else:
    LOGGING_FORMAT = '[%(process)d:%(thread).5s] %(asctime)s %(levelname)s %(module)s:%(lineno)d - %(message)s'



ISPY3K = sys.version_info[0] >= 3



class DummySocket(object):
    def __init__(self, handler, conn):
        self._handler = handler
        self._conn = conn
        self._buffer = ''
        self._counter = 0
        self._server = rfoo.Server(self._handler)

    def shutdown(self, x):
        pass

    def close(self):
        pass

    def sendall(self, data):
        self._buffer = data

        self._counter += 1
        if self._counter % 2 == 1:
            self._server._dispatch(self._handler, self._conn)

    def recv(self, size):
        data = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return data



class DummyConnection(rfoo.Connection):
    """Dispatch without network, for debugging."""

    def __init__(self, handler):
        rfoo.Connection.__init__(self, DummySocket(handler, self))



def print_usage():
    scriptName = os.path.basename(sys.argv[0])
    sys.stdout.write("""
Start server:
%(name)s -s [-pPORT]

Start client:
%(name)s [-c] [-oHOST] [-pPORT] [-nN] [data]

data, if present should be an integer value, which controls the
length of a CPU intensive loop performed at the server.

-h, --help  Print this help.
-v          Debug output.
-s          Start server.
-a          Use async notifications instead of synchronous calls.
-c          Setup and tear down connection with each iteration.
-oHOST      Set HOST.
-pPORT      Set PORT.
-nN         Repeat client call N times.
-tN         Number of client threads to use.
-iF         Set thread switch interval in seconds (float).
""" % {'name': scriptName})



def main():
    """Parse options and run script."""

    try:
        options, args = getopt.getopt(
            sys.argv[1:], 
            'hvsacuo:p:n:t:i:', 
            ['help']
            )
        options = dict(options)

    except getopt.GetoptError:
        print_usage()
        return 2

    if '-h' in options or '--help' in options:
        print_usage()
        return

    #
    # Prevent timing single connection async calls since 
    # this combination will simply generate a SYN flood,
    # and is not a practical use case.
    #
    if '-a' in options and '-c' in options:
        print_usage()
        return

    if '-v' in options:
        level = logging.DEBUG
        verbose = True
    else:
        level = logging.WARNING
        verbose = False

    logging.basicConfig(
        level=level, 
        format=LOGGING_FORMAT,
        stream=sys.stderr
    )
    
    if '-i' in options:
        interval = float(options.get('-i'))
        sys.setswitchinterval(interval)

    host = options.get('-o', '127.0.0.1')
    port = int(options.get('-p', rfoo.DEFAULT_PORT))

    t0 = time.time()
    try:
        if '-s' in options:
            logging.warning('Start as server.')
            rfoo.start_server(host=host, port=port, handler=rfoo.ExampleHandler)
            return
            
        logging.warning('Start as client.')

        if len(args) > 0:
            data = 'x' * int(args[0])
        else:
            data = 'x'

        n = int(options.get('-n', 1))
        t = int(options.get('-t', 1))
        m = int(n / t)

        if '-a' in options:
            gate = rfoo.Notifier
        else:
            gate = rfoo.Proxy

        def client():
            #
            # Time connection setup/teardown.
            #
            if '-c' in options:
                for i in range(m):
                    connection = rfoo.connect(host=host, port=port)
                    r = rfoo.Proxy(connection).echo(data)
                    if level == logging.DEBUG:
                        logging.debug('Received %r from proxy.', r)
                    connection.close()

            #
            # Time with dummy connection (no network).
            #
            elif '-u' in options:
                handler = rfoo.ExampleHandler()
                dummy = DummyConnection(handler)
                echo = gate(dummy).echo
                for i in range(m):
                    r = echo(data)
                    if level == logging.DEBUG:
                        logging.debug('Received %r from proxy.', r)

            #
            # Time calls synched / asynch (notifications).
            #
            else:
                connection = rfoo.connect(host=host, port=port)
                echo = gate(connection).echo
                for i in range(m):
                    r = echo(data)
                    #if level == logging.DEBUG:
                    #    logging.debug('Received %r from proxy.', r)

            logging.warning('Received %r from proxy.', r)

        if t == 1:
            client()
            return

        threads = [threading.Thread(target=client) for i in range(t)]
        t0 = time.time()
        
        for t in threads:
            t.start()

        for t in threads:
            t.join()

    finally:
        logging.warning('Running time, %f seconds.', time.time() - t0)


    
if __name__ == '__main__':
    #import cProfile; 
    #cProfile.run('main()', '/tmp/profiled');
    main()




