self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

self.send(
    '''
    <html>
        <head>
            <title>Explorer - Tests</title>
            <link rel="stylesheet" href="/css" media="all">
        </head>
        <body>''')

def embed_progress(self, name):
    self.send('''
        <span id="%s"></span>
        <script>
            progress.%s = "";
        </script>''' % (name, name))

def update_progress(self, name, i, m):
    self.send('<script>progress.%s = `${(%s.0 / %s.0 * 100).toString()} %% - %s of %s`;</script>' % (name, str(i), str(m), str(i), str(m)))

self.send('''<script>var progress = { };
            window.setInterval(function(){
                    let keys = Object.keys(progress);
                    for (key of keys){
                        document.getElementById(key).innerHTML = progress[key];
                    }

                    let scripts = document.getElementsByTagName("script");
                    for (let i = scripts.length - 1; i > 0; --i){
                        scripts[i].remove();
                    }
                }, 100);
        </script>''')

self.send('<h1>Issue Extracted Feature Test:</h1>')
embed_progress(self, 'ieft_1')
import datetime

try:
    i = 0
    m = 0

    for change_request in change_request_list:
        issue_map = change_request.getIssueMap()
        
        m += len(issue_map.get().keys())

    for change_request in change_request_list:
        issue_map = change_request.getIssueMap()
        
        for issue_key, issue in issue_map.get().items():
            i += 1
            extracted_features = issue_map.getExtractedFeatures(issue_key, [], datetime.datetime.now(tz=datetime.timezone.utc))
            update_progress(self, 'ieft_1', i, m)

except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')
