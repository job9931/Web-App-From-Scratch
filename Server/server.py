'''This program is a simple server which serves files.'''

import socket
import typing
import mimetypes
import os

HOST = "127.0.0.1" #server address
PORT = 9000

#Where the server should serve files from 
SERVER_ROOT = os.path.abspath("www")

#make not found default file server response
NOT_FOUND_RESPONSE = b"""\
HTTP/1.1 404 Not Found
Content-type: text/plain
Content-length: 9

Not Found""".replace(b"\n", b"\r\n")

#Not allowed response for requests we dont permit
METHOD_NOT_ALLOWED_RESPONSE = b"""\
HTTP/1.1 405 Method Not Allowed
Content-type: text/plain
Content-length: 17

Method Not Allowed""".replace(b"\n", b"\r\n")

BAD_REQUEST_RESPONSE = b"""\
HTTP/1.1 400 Bad Request
Content-type: text/plain
Content-length: 11

Bad Request""".replace(b"\n", b"\r\n")


FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")


def parse_request(socket,bufsize=16_384): #note16_384 = 16,384
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
                
def serve_file(sock: socket.socket, path: str) -> None:
    '''Given a socket and the relative path to a file (relative to
    SERVER_SOCK), send that file to the socket if it exists.  If the
    file does not exist, sent '404 Not Found' response.'''
    
    #construct path to file
    if path == "/":
        path = "/index.html"
    
    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        sock.sendall(NOT_FOUND_RESPONSE)
        return

    try:
        with open(abspath, "rb") as f:#open file
            stat = os.fstat(f.fileno()) #get file descriptor and estimate attributes (size)
            content_type, encoding = mimetypes.guess_type(abspath)#guess file type based on URL
            if content_type is None:#check for content
                content_type = "application/octet-stream"

            if encoding is not None:#check encoding
                content_type += f"; charset={encoding}"
            
            #construct response from template
            response_headers = FILE_RESPONSE_TEMPLATE.format(
                content_type=content_type,
                content_length=stat.st_size,
            ).encode("ascii")

            sock.sendall(response_headers)#write file to socket
            sock.sendfile(f)
    except FileNotFoundError:#notify if file not found 
        sock.sendall(NOT_FOUND_RESPONSE)
        return 
    
    

class Request(typing.NamedTuple):
    method: str
    path: str
    headers: typing.Mapping[str, str]

    @classmethod
    def from_socket(cls, sock: socket.socket) -> "Request":
        """Read and parse the request from a socket object.

        Raises:
          ValueError: When the request cannot be parsed.
        """
        lines = parse_request(sock) #parse lines using external function

        try:
            request_line = next(lines).decode("ascii")#decode bytearray into string
        except StopIteration:
            raise ValueError("Request line missing.")

        try:
            method, path, _ = request_line.split(" ") #extract method and path attributes
        except ValueError:
            raise ValueError(f"Malformed request line {request_line!r}.")

        headers = {}#headers are mapping from str to str (dictionary)
        for line in lines:
            try:
                name, _, value = line.decode("ascii").partition(":")#Extract header info
                headers[name.lower()] = value.lstrip()#add to dictionary
            except ValueError:
                raise ValueError(f"Malformed header line {line!r}.")
                
        #return a Request object 
        return cls(method=method.upper(), path=path, headers=headers)
    
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
    
        #Insert a try-except block to handle bad requests
        with client_socket:
            try:
                request = Request.from_socket(client_socket)
                if request.method != 'GET':
                    client_socket.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                    continue
                    
                serve_file(client_socket,request.path)#serve file  
            except Exception as e:
                print(f"Failed to parse request: {e}")
                client_socket.sendall(BAD_REQUEST_RESPONSE)