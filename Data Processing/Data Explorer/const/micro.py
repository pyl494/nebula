self.send_response(200)
self.send_header("Content-type", "text/json")
self.end_headers()

try:
    import importlib
    mIssues_spec = importlib.util.spec_from_file_location('issues', '../Data Processing/issues.py')
    mIssues = importlib.util.module_from_spec(mIssues_spec)
    mIssues_spec.loader.exec_module(mIssues)

    response = {'result': 'None'}

    from sklearn.feature_extraction import DictVectorizer
    from sklearn import metrics
    from sklearn.utils.extmath import density
    import datetime

    if querystring['type'] == 'handshake':
        change_request_issue_key = querystring['change_request']
        server_last_updated = mIssues.Issues.parseDateTime(querystring['updated'])

        found = False
        for change_request in change_request_list:
            issue_map = change_request.getIssueMap()
            
            if issue_map.getUniverseName() == 'Microservice Demo':
                change_request_meta_map = change_request.getChangeRequestMetaMap()

                if change_request_issue_key in change_request_meta_map:
                    change_request_meta = change_request_meta_map[change_request_issue_key]

                    local_last_updated = change_request_meta['last_updated']

                    if local_last_updated < server_last_updated:
                        response['result'] = 'Not Up-To-Date'
                    else:
                        features = change_request.getExtractedFeatures(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))
                        mlabel = change_request.getManualRiskLabel(change_request_issue_key)

                        if mlabel is None or mlabel in ['None', 'low', 'medium', 'high']:
                            data = [{
                                    'number_of_issues': features['number_of_issues'],
                                    'number_of_bugs': features['number_of_bugs'],
                                    'number_of_features': features['number_of_features'],
                                    'number_of_improvements': features['number_of_improvements'],
                                    'number_of_other': features['number_of_other'],
                                    'number_of_comments': features['number_of_comments'],
                                    'discussion_time': features['discussion_time'].days,
                                    'number_of_blocked_by_issues': features['number_of_blocked_by_issues'],
                                    'number_of_blocks_issues': features['number_of_blocks_issues'],
                                    'number_of_participants': features['number_of_participants'],
                                    'elapsed_time': features['elapsed_time'].days,
                                    'delays': features['delays'].days
                                }]

                            response['features'] = data[0]
                            response['predictions'] = {}
                        
                            X = DictVectorizer(sparse=True).fit_transform(data)
                            
                            for name, clf in classifiers.items():
                                prediction = clf.predict(X)[0]
                                response['predictions'][name] = ['low', 'medium', 'high'][prediction]
                        else:
                            response['override'] = mlabel
                        
                        response['result'] = 'ok'

                    found = True
                    break

        if not found:
            response['result'] = 'Not Found'

    elif querystring['type'] == 'override':
        change_request_issue_key = querystring['change_request']
        label = querystring['label']

        found = False
        for change_request in change_request_list:
            issue_map = change_request.getIssueMap()

            if issue_map.getUniverseName() == 'Microservice Demo':
                change_request_meta_map = change_request.getChangeRequestMetaMap()

                if change_request_issue_key in change_request_meta_map:
                    found = True
                    change_request.setManualRiskLabel(change_request_issue_key, label)
                    mlabel = change_request.getManualRiskLabel(change_request_issue_key)

                    if label == mlabel:
                        response['result'] = 'ok'
                    else:
                        response['result'] = 'Failed'

                    break
        if not found:
            response['result'] = 'Not Found'

    elif querystring['type'] == 'add':

        for change_request in change_request_list:
            issue_map = change_request.getIssueMap()

            if issue_map.getUniverseName() == 'Microservice Demo':
                issue_map.add(postvars['raw'])
                change_request.generate()
                response['result'] = 'ok'
                break
    
    self.send(json.dumps(response))

except Exception as e:
    response['result'] = 'error'
    response['exception'] = str(exception_html(e))

    self.send(json.dumps(response))

exports = {
    'change_request_list': change_request_list
}
