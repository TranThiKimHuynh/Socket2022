import socket
import threading
import os
import sys

# Ham xu phan giai ten mien
def processDomain(domain):
    elementOfDomain = domain.split("/")
    host = elementOfDomain[2]
    return host

# Ham tao command line
def commandLine():
    listDomain = sys.argv
    num = len(listDomain)
    i = 0
    if(num == 2 and listDomain[1].find("http") == -1):
        return None
    
    while i <= num - 1:
        if(listDomain[i].find("http") == -1):
           listDomain.pop(i)
           num  = num - 1
           if num == 0:
               return None
        i = i + 1

    return listDomain

def processFileName(domain):
    # Tach ten mien ra thanh tung phan
    listElement = domain.split("/")

    sizeArr = len(listElement)

    # File co loai file cu the
    if(listElement[sizeArr -1] =="" and sizeArr <= 4):
        return "index.html"
    if(listElement[sizeArr -1].find(".") == -1 and sizeArr <= 4):
        return listElement[sizeArr - 1] + ".html"
    fileName = listElement[sizeArr - 1]
    # File  root
    if sizeArr <= 3:
        fileName = "index.html"
    return fileName

# Download file 
def downloadFile(data,FileName,path_w):
    path_w = path_w + "\\" + FileName
    with open(path_w,"wb") as f:
        f.write(data)
        f.close()
        
def processChunk(fileContent):
    res = b""
    while True:
        post = fileContent.find(b"\r\n")
        chunkSize = int(fileContent[:post].decode(),base = 16)
        if(chunkSize == 0):
            break
        res = res + fileContent[(post+2):(post+2+chunkSize)]

        fileContent = fileContent[(post+4+chunkSize):]

    return res
# Ham nhan du lieu bang Transfer Encoding Chunk
def recvByTranferEncodingChunk(buffsize, domain, s, path_w, residueData):
    contentFile = b""
    host = processDomain(domain)
    request = "GET {Domain} HTTP/1.1\r\nHost:{Host}\r\n\r\n".format(Domain = domain, Host = host)
    First = True

    s.sendall(request.encode())
    while True:
        try:
            data = s.recv(2048)
        except socket.timeout:
            print("[<!>] DIDN'T RECEEIVE DATA! [TIME OUT] ")
            sys.exit(1)

        if(First == True):
            data = residueData + data
            posHeader = data.find(b"\r\n\r\n") + 4
            header = data[:posHeader]
            header = header.decode()
 
            contentFile = data[posHeader:]
            First = False

        else:
            contentFile = contentFile + data
       

        if(data.find(b"0\r\n\r\n") != -1):
            break


    contentFile = processChunk(contentFile)
    fileName = processFileName(domain)
    
    # Download folder
    print("Download FILE: "+ fileName)
    print("[<] : Start ...")
    print("[<] : Downloading...")
    downloadFile(contentFile,fileName,path_w)
    print("[<] Download Successfully ! ")

# Ham nhan du lieu bang content - length
def recvByContentLength(buffsize, domain, s,path_w):
    contentFile = b""
    host = processDomain(domain)
    request = "GET {Domain} HTTP/1.1\r\nHost:{Host}\r\n\r\n".format(Domain = domain, Host = host)
    First = True

    preBuffsize = 0
    s.sendall(request.encode())
    while True:
        try:
            data = s.recv(2048)
        except socket.timeout:
            print("[<!>] DIDN'T RECEEIVE DATA! [TIME OUT] ")
            sys.exit(1)
        contentFile = contentFile + data
        preBuffsize = preBuffsize + buffsize

        if(First == True):
            posHeader = data.find(b"\r\n\r\n") + 4
            header = data[:posHeader]

            header = header.decode()
            
            posContentLength = header.find("Content-Length: ") + 16
            # Khong tim thay Content-Lenght
            if(posContentLength == 15):
                return data

            cutHeader = header[posContentLength :]
            posEndLength = cutHeader.find("\r\n") 
         
            contentLength = int(cutHeader[:posEndLength])
         
            contentFile = contentFile[posHeader:(posHeader+contentLength)]
            First = False

       
        if(len(contentFile) == contentLength):
            break

    fileName = processFileName(domain)
    
    # Download folder
    if(fileName.find(".") == -1):
        return contentFile
    else:
         print("Download FILE: "+ fileName)
         print("[<] : Start ...")
         print("[<] : Downloading...")
         downloadFile(contentFile,fileName,path_w)
         print("[<] Download Successfully ! ")

def seperateLink(fileContent):
    fileContent = fileContent.decode()
    pos = 0
    res = []
    i = 0
    while True:
        pos = fileContent.find("href=")
        if(pos == -1):
            break
        pos = pos + 6
        fileContent = fileContent[pos:]
        end = fileContent.find(">") - 1
        if(fileContent[:end].find("?") == -1):
           res.append(fileContent[:end])
        fileContent = fileContent[end:]
    while (i<len(res)):
        if( res[i].find(".") == -1):
            res.remove(res[i])
        i = i + 1
    return res  

def downloadFolder(domain,s):
    host = processDomain(domain)
    buffsize = 1000

    test  = domain[:len(domain) - 1]

    folderName = processFileName(test)

    print(folderName)
    path_w = os.getcwd() + "\\" + folderName
    print(path_w)
    os.makedirs(path_w,exist_ok=True)

    fileContent = recvByContentLength(buffsize,domain,s,path_w)
    listLink = seperateLink(fileContent)
    print(listLink)
    i = 0
           

    while (i < len(listLink)):
        keep = domain
        domain = domain  + listLink[i]

        fileName = processFileName(domain)

        recvByContentLength(buffsize,domain,s,path_w)

        domain = keep
        i = i + 1

# Ham kiem tra co phai la Download Folder     
def isDownloadFolder(domain):
    list = domain.split("/")
    size = len(list)
    if size <= 5:
        return False
    if(list[size - 1] == "" and list[size -2].find(".") == -1):
        return True
    return False

# Ham phan giai ten mien thanh host
def mainProccess (domain):
    host = processDomain(domain)
    print(host)

# Test ten host hop le hay khong
    try:
        remote_ip = socket.gethostbyname(host)
    except socket.gaierror:
       # Ten mien khong phan giai duoc
        print("Hostname could not be resolved. Exiting !")
        sys.exit()

    try: 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Socket successfully created")
    except socket.error as err:
        print("Socket creation failed with error %s" %(err))

    # Port mac dinh
    port = 80
    buffsize = 1000
    timeout = 10
    data = b""
    s.settimeout(timeout)

    s.connect((host, port))

    path_w =  path_w = os.getcwd() 
    
    if(isDownloadFolder(domain) == True):
        downloadFolder(domain,s)
    else:
        data = recvByContentLength(buffsize,domain,s,path_w)
        if(data != None):
            recvByTranferEncodingChunk(buffsize,domain,s,path_w,data)

    s.close()


if __name__ == '__main__':
  listDomain = commandLine()
  if listDomain == None:
    print("INVALID ARGUMENT!")
  else:
    if(len(listDomain) == 1):
        mainProccess(listDomain[0])
    else:
        threads = list()
        for i in range(len(listDomain)):
            x = threading.Thread(target=mainProccess,args=(listDomain[i - 1],))
            threads.append(x)
            x.start()
    
#print("So tham so dong lenh: ",len(sys.argv))
#print("Danh sach tham so: ",str(sys.argv))

