
self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

self.send(
    """
    <html>
        <head>
            <title>Explorer</title>
            <link rel="stylesheet" href="/css" media="all">
        </head>
        <body>
            <h1>Starting</h1>""")
try:
    import subprocess, os

    cwd = os.path.abspath(os.getcwd()+ '/../')

    try:
        if server_wormhole.poll():
            raise
    except:
        server_wormhole = subprocess.Popen('cmd', stdin=subprocess.PIPE, bufsize=1, shell=False, universal_newlines=True, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=cwd)

        server_wormhole.stdin.write('%USERPROFILE%\\Anaconda3\\Scripts\\activate.bat %USERPROFILE%\\Anaconda3\n')
        server_wormhole.stdin.write('conda activate myenv && set CONDA_DLL_SEARCH_MODIFICATION_ENABLE=1\n')
        server_wormhole.stdin.write('cd "Data Processing"\n')
        server_wormhole.stdin.write('python wormhole_server.py\n')

    try:
        if server_mongo.poll():
            raise
    except:
        server_mongo = subprocess.Popen('cmd', shell=False, stdin=subprocess.PIPE, bufsize=1, universal_newlines=True, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=cwd)
        server_mongo.stdin.write('"./Third Party/mongodb-win32-x86_64-windows-4.4.0/bin/mongod.exe" -dbpath="./Data"\n')

except Exception as e:
    self.send(debug.exception_html(e))

self.send('</body></html>')

exports = {
    'server_wormhole': server_wormhole,
    'server_mongo': server_mongo
}
