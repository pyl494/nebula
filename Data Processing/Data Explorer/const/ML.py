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
        <body>""")

try:
    import datetime

    for change_request in change_request_list:
        self.send('<h1>%s</h1>' % change_request.getIssueMap().getUniverseName())
        try:
            model = change_request.getMachineLearningModel()

            self.send('<h2>Preparing Data</h2>')
            model.prepare_dataset()

            self.send('<h2>Splitting Data</h2>')
            model.split_dataset()

            self.send('<h2>Training</h2>')
            model.train(incremental=False)
        except Exception as e:
            self.send(exception_html(e))

except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
}
