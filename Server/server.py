'''This program is a simple server which returns Hello! to all requests.'''


import socket
import typing

HOST = "127.0.0.1" #server address
PORT = 9000


RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")



def parse_request(socket:socket.socket,bufsize: int=16_384) -> typing.Generator[bytes, None, bytes]: #note16_384 = 16,384
    #-> typing.Generator[bytes, None, bytes]:
    '''Reads individual CRLF-spearated lines from a socket in bufsize segments.
        
    Inputs:
        socket: socket object.
        bufsize: number of bytes to read at once.
            
    Yields: 
        data: represented as a bytes object.            
    '''
        
    buffer = b"" #initialise bytes literal
    while True: #loop forever
        data = socket.recv(bufsize) #read data from socket
        if not data: #if data is empty
            return b""
            
        buffer += data #add data into the buffer
            
        while True:
            try:
                i = buffer.index(b"\r\n") #get index of CRLF separator 
                line, buffer = buffer[:i],buffer[i+2:] #split buffer into separate lines
                if not line: #if line is empty
                    return buffer
                    
                yield line #yield each line then continues
                
            except IndexError: #break if CRLF separator not found
                break


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
        
    
        #begin printing request messages
        with client_socket:
            for line in parse_request(client_socket): #for each parsed line
                print(line)
            client_socket.sendall(RESPONSE) #send Hello! reponse
           