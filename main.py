from socket import * 
import argparse
import threading
import logging
import zipfile
import os

MAX_CONNETION = 50
MAX_FILE_SIZE = 30720 * 1024 #30MB

logging.basicConfig(level= logging.DEBUG, filename='pythonServer.log', filemode= 'w',  format='[%(asctime)s] [%(process)s] [%(levelname)s] [%(message)s]')
logg = logging.getLogger(__name__)

class Error:
    Error404 = b'HTTP/1.1 404 Not Found'

class Request:
    def __init__(self, rawClientData:bytes):
        logg.info(rawClientData)
        self.rawClientData = rawClientData
        self.rawClientDataSplit = rawClientData.split(b'\r\n')
        self.headerLine = self.rawClientDataSplit[0].decode()

        self.method, self.path, self.protocol = self.headerLine.split(' ') 

class ConnectionHandling(threading.Thread):
    def __init__(self, clientCon:socket):
        super().__init__()
        self.clientCon = clientCon
        self.serve()
    
    def serve(self):
        try:
            dirPath = os.getcwd()

            clinetRequestedData = self.clientCon.recv(MAX_FILE_SIZE)

            if not clinetRequestedData:
                return
            
            req = Request(clinetRequestedData)
            reqFile = req.path[1:]

            if '.' not in reqFile:
                reqDir = reqFile
                if os.path.exists(reqDir):
                    zipFilePath = os.path.join(dirPath, reqDir + '.zip')

                    with zipfile.ZipFile(zipFilePath, 'w') as zipDir:
                        for fileName in os.listdir(reqDir):
                            filePath = os.path.join(dirPath, reqDir, fileName)
                            zipDir.write(filePath, fileName)

                    with open(zipFilePath, 'rb') as zipped:
                        content = zipped.read()
                    
                    responseHeader = f'HTTP/1.1 200 OK\r\nContent-Disposition: attachment; filename={fileName}.zip\r\n\r\n'
                    self.clientCon.sendall(responseHeader.encode() + content)

                    os.remove(zipFilePath)

            else:
                filepath = os.path.join(dirPath, reqFile)

                if os.path.isfile(filepath):
                    with open(filepath, 'rb') as file:
                        content = file.read()

                responseHeader = f'HTTP/1.1 200 OK\r\nContent-Disposition: attachment; filename={reqFile}\r\n\r\n'
                self.clientCon.sendall(responseHeader.encode() + content)
            
            self.clientCon.close()

        except FileNotFoundError:
            self.clientCon.send(Error.Error404)
            self.clientCon.close()

class Server:
    def __init__(self, options):
        print('Server is listning...')
        self.host = options.host
        self.port = options.port
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.bind((self.host, self.port))
        self.serverSocket.listen(MAX_CONNETION)
        print(f"Listening at: http://{self.host}:{self.port}")

    
    def start(self):
        while True:
            clientCon, addr = self.serverSocket.accept()
            logg.info(f'Received Connection from {addr}')
            thread = ConnectionHandling(clientCon)
            thread.start()
    
    def __del__(self):
        self.serverSocket.close()


if __name__ == "__main__":
    desc = 'Run Simple Python Server for serving Files'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-n', type=str, default=gethostbyname(gethostname()),
                        dest='host',
                        help='get hostname of the server %(default)s')
    
    parser.add_argument('-p', type=int, default=8080,
                        dest='port',
                        help='get port number of the server %(default)s')
    options = parser.parse_args()

    if hasattr(options, '-h'):
        parser.print_help()

    ser = Server(options)
    ser.start()