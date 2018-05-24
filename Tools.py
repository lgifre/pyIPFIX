def readFile(path):
    f = open(path, 'r')
    content = f.read()
    f.close()
    return(content)

def writeFile(path, data):
    f = open(path, 'w')
    f.write(data)
    f.close()
