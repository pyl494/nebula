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
    import time

    t0 = time.perf_counter()
    for change_request in change_request_list:
        t1 = time.perf_counter()
        universe_name = change_request.get_issue_map().get_universe_name()
        self.send('<h1>%s</h1>' % universe_name)
        try:
            model = change_request.get_machine_learning_model()

            self.send('<h2>Preparing Data</h2>')
            model.prepare_dataset()

            self.send('<h2>Splitting Data</h2>')
            model.split_dataset()

            self.send('<h2>Vectorizing</h2>')
            model.fit_vectorizer()

            self.send('<h2>Training</h2>')
            import wormhole

            script = '''
def work(queue):
    import issues
    import change_requests

    issue_map = issues.Issues('{universe_name}')
    change_request = change_requests.ChangeRequest(issue_map)
    model = change_request.get_machine_learning_model()

    model.train(n={part}, configurations=queue, mpqueue=True)
            '''

            part = 0
            scripts = []
            queue = []
            configurations = model.get_configuration_permutations()

            #import random
            #random.shuffle(configurations)

            from multiprocessing import cpu_count
            split_count = cpu_count() * cpu_count()
            split_size = int(len(configurations) / split_count + 0.5)

            for i in range(cpu_count()):
                s = script.format(
                    universe_name=universe_name,
                    part=part
                )
                part += 1
                scripts += [s]

            for i in range(split_count):
                split = configurations[i * split_size : (i+1) * split_size]
                queue += [split]
            print(scripts)

            self.send('Added: %s<br/>' % str(wormhole.add(scripts, queue)))

            self.send('Success: %s<br/>' % str(wormhole.run()))

            model.combine_models(list(range(part)))
            self.send('Timer: %s s<br/>' % str(time.perf_counter() - t1))

            #model.train(incremental=False)
        except Exception as e:
            self.send(exception_html(e))

        self.send('Timer: %s s<br/>' % str(time.perf_counter() - t0))

except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
}
