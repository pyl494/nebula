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

    from change_requests import ChangeRequest

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
                        extracted_features = change_request.getExtractedFeatures(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))
                        extracted_features_meta = extracted_features['Meta']
                        mlabel = change_request.getManualRiskLabel(change_request_issue_key)

                        if mlabel is None or mlabel in ['None', 'low', 'medium', 'high']:
                            features = {
                                'number_of_issues': extracted_features['number_of_issues'],
                                'number_of_bugs': extracted_features['number_of_bugs'],
                                'number_of_features': extracted_features['number_of_features'],
                                'number_of_improvements': extracted_features['number_of_improvements'],
                                'number_of_other': extracted_features['number_of_other'],
                                'number_of_participants': extracted_features['number_of_participants'],
                                'elapsed_time': extracted_features['elapsed_time'].total_seconds(),
                            }

                            for feature in extracted_features_meta['aggregated_features']:
                                for aggregator_name in extracted_features_meta['aggregators']:
                                    features['%s_%s' % (feature, aggregator_name)] = extracted_features[feature][aggregator_name]

                            data = [features]

                            response['features'] = data[0]
                            response['predictions'] = {}
                        
                            X_test = DictVectorizer(sparse=False).fit_transform(data)
                            
                            for scaling_name, scalings_ in trained_models.items():
                                if not isinstance(scalings_, dict):
                                    continue
                                    
                                X_test_scaled = X_test
                                if 'scaler' in scalings_:
                                    X_test_scaled = scalings_['scaler'].transform(X_test)
                                
                                for sampling_name, samplings_ in scalings_.items():
                                    if not isinstance(samplings_, dict):
                                        continue
                                    
                                    X_test_sampled = X_test_scaled
                                    
                                    for fselection_name, fselections_ in samplings_.items():
                                        if not isinstance(fselections_, dict):
                                            continue
                                            
                                        X_test_fselected = X_test_sampled
                                        if 'selector' in fselections_:
                                            X_test_fselected = fselections_['selector'].transform(X_test_sampled)
                                        
                                        for classifier_name, classifier in fselections_.items():
                                            prediction = classifier.predict(X)[0]
                                            response['predictions']['%s - %s - %s - %s' % (scaling_name, sampling_name, fselection_name, classifier_name)] = ['low', 'medium', 'high'][prediction]
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
