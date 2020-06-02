self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

result = ""
htmlinjection = ""
d = dict(locals(), **globals())

variables = "<table><tr><th>Variable</th><th>Value</th></tr>"

for key, value in d.items():
    v = ''

    if isinstance(value, list):
        v = '[...] len: %s, size: %s bytes' % (html.escape(str(len(value))), html.escape(str(sys.getsizeof(value))))
    elif isinstance(value, tuple):
        v = '(...) len: %s, size: %s bytes' % (html.escape(str(len(value))), html.escape(str(sys.getsizeof(value))))
    elif isinstance(value, dict):
        v = '{...} size: %s bytes' % html.escape(str(sys.getsizeof(value)))
    else:
        v = str(value)
    
    variables += "<tr><td>{variable}</td><td>{value}</td></tr>".format(
        variable = html.escape(key),
        value = html.escape(v)
    )

variables += "</table>"

default = """
print("Hello world!")
result = "Hello world !"
    """

out = ["""
    <h2>Enter code</h2>
    <div class="columncontainer">
        <div class="column" style="flex-basis: 200%; flex-grow: 2;">
            <form action="/repl" method="GET">
                <textarea id="myTextArea" name="source" rows="12" cols="120">{default}</textarea> <br/>
                <button type="submit">Submit</button>
            </form>
        </div>
        <div class="column">
            <div class="variableinspector">
                {variables}
            </div>
        </div>
    </div>
    <br/>
    """]

if 'source' in querystring:
    source = querystring['source']
    default = source

    out += ["<hr><br/><h2>Source</h2><pre>{source}</pre><br/><hr><br/><h2>Output</h2>".format(source=source)]
    
    try:
        with stdoutIO() as o:
            exec(source, d, d)

            out += ["<pre>%s</pre><br/>" % html.escape(o.getvalue())]
            
    except Exception as e:
        sys.stdout = STDOUT
        out += [exception_html(e)]

    out += ["<hr><br/><h2>Result:</h2><pre>{result}</pre>".format(
        result = html.escape(str(d['result']))
    )]

    out += [str(d['htmlinjection'])]

out[0] = out[0].format(
    default = html.escape(default),
    variables = variables
)

self.wfile.write(bytes(
    """
    <html>
        <head>
            <title>Explorer</title>
            <link rel="stylesheet" href="/css" media="all">
            <link rel="stylesheet" href="/Third Party/codemirror.css">
            <script src="/Third Party/codemirror.js"></script>
            <script src="/Third Party/codemirror_python.js"></script>
        </head>
        <body>
            <h1>Python REPL</h1>
            You can interact with the python without restarting the server.<br/>""", 'utf-8'))

for line in out:
    self.wfile.write(bytes(line, 'utf-8'))

self.wfile.write(bytes("""
            <script>
            var myTextArea = document.getElementById('myTextArea');
            var myCodeMirror = CodeMirror.fromTextArea(myTextArea, { 
                value: myTextArea.value,
                lineNumbers: true
            });
            editor.setOption("extraKeys", {
                Tab: function(cm) {
                    var spaces = Array(cm.getOption("indentUnit") + 1).join(" ");
                    cm.replaceSelection(spaces);
                }
            });
            </script>
        </body>
    </html>""", 'utf-8'))
    