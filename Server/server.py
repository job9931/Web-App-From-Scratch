'''This program is a simple server which returns Hello! to all requests.'''


import socket

HOST = "127.0.0.1" #server address
PORT = 9000


RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

# Create a TCP/IP socket using socket.socket() with default parameters
with socket.socket() as s:
    
    '''We need to make the socket available for reuse after a connection is closed
    and are in a are in `TIME_WAIT` state. NOTE, TIME WAIT is part of TCP: when 
    the remote endpoint, (other side) of the connection is closed with CLOSE_WAIT, 
    connection remains open at the local endpoint for some time to pick up delayed
    packets of data. TIME_WAIT represents the closing of the local endpoint.'''
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    #Bind socket to address
    s.bind((HOST,PORT))
    
    '''listen on socket, 0 is number of unaacepted connections the system will allow 
    before refusing new connections.'''
    s.listen(0) 
    
    '''The accept method accepts a connections. It returns a pair (conn, address) where 
    conn is a new socket object usable to send and receive data on the connection, and 
    address is the address bound to the socket on the other end of the connection.'''
    
    while True: #keeps server open permanantly.
        client_socket, client_address = s.accept()
        print(f"New connection from {client_address}.")
        #Send back response using sendall()
    
        with client_socket:
            client_socket.sendall(RESPONSE)
