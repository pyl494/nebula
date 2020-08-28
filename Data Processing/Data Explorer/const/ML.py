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
        universe_name = change_request.getIssueMap().getUniverseName()
        self.send('<h1>%s</h1>' % universe_name)
        try:
            model = change_request.getMachineLearningModel()

            self.send('<h2>Preparing Data</h2>')
            model.prepare_dataset()

            self.send('<h2>Splitting Data</h2>')
            model.split_dataset()

            self.send('<h2>Vectorizing</h2>')
            model.fit_vectorizer()

            self.send('<h2>Training</h2>')
            import wormhole

            script = '''
import issues
import change_requests

issue_map = issues.Issues('{universe_name}')
change_request = change_requests.ChangeRequest(issue_map)
model = change_request.getMachineLearningModel()

model.scalers = {scalers}
model.samplers = {samplers}
model.feature_selections = {selectors}
model.dimensional_reducers = {reducers}
model.classifiers = {classifiers}

model.train(n={part})
            '''

            part = 0
            scripts = []
            settings = []
            for scaler_name in model.scalers:
                for sampler_name in model.samplers:
                    for selector_name in model.feature_selections:
                        for reducer_name in model.dimensional_reducers:
                            for classifier_name in model.classifiers:
                                settings += [{
                                    'scaler': scaler_name,
                                    'sampler': sampler_name,
                                    'selector': selector_name,
                                    'reducer': reducer_name,
                                    'classifier': classifier_name
                                }]
            from multiprocessing import cpu_count
            split_count = cpu_count() * cpu_count()
            split_size = int(len(settings) / split_count + 0.5)
            for i in range(split_count):
                split = settings[i * split_size : (i+1) * split_size]
                scalers = {}
                samplers = {}
                selectors = {}
                reducers = {}
                classifiers = {}
                for setting in split:
                    scalers[setting['scaler']] = model.scalers[setting['scaler']]
                    samplers[setting['sampler']] = model.samplers[setting['sampler']]
                    selectors[setting['selector']] = model.feature_selections[setting['selector']]
                    reducers[setting['reducer']] = model.dimensional_reducers[setting['reducer']]
                    classifiers[setting['classifier']] = model.classifiers[setting['classifier']]

                s = script.format(
                    universe_name=universe_name,
                    scalers=scalers,
                    samplers=samplers,
                    selectors=selectors,
                    reducers=reducers,
                    classifiers=classifiers,
                    part=part
                )
                part += 1
                scripts += [s]
            print(scripts)

            self.send('Added: %s<br/>' % str(wormhole.add(scripts)))

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
