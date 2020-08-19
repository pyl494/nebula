self.send_response(200)
self.send_header("Content-type", "text/json")
self.end_headers()

try:
    import importlib
    mIssues_spec = importlib.util.spec_from_file_location('issues', '../Data Processing/issues.py')
    mIssues = importlib.util.module_from_spec(mIssues_spec)
    mIssues_spec.loader.exec_module(mIssues)

    response = {'result': 'None'}

    import numpy as np
    from sklearn.feature_extraction import DictVectorizer
    from sklearn import metrics
    from sklearn.utils.extmath import density
    from sklearn.inspection import permutation_importance

    from change_requests import ChangeRequest

    import datetime
    
    debug_test_mode = False

    if querystring['type'] == 'test-handshake':
        querystring['type'] = 'handshake'
        if not 'change_request' in querystring:
            querystring['change_request'] = 'AC_gcr_-3'
        querystring['updated'] = '2100-02-25T18:22:41.988-0600'
        debug_test_mode = True

    if querystring['type'] == 'handshake':
        change_request_issue_key = querystring['change_request']
        server_last_updated = mIssues.Issues.parseDateTime(querystring['updated'])

        found = False
        for change_request in change_request_list:
            issue_map = change_request.getIssueMap()
            
            if issue_map.getUniverseName() == 'Microservice Demo' or debug_test_mode:
                change_request_meta_map = change_request.getChangeRequestMetaMap()

                if change_request_issue_key in change_request_meta_map:
                    change_request_meta = change_request_meta_map[change_request_issue_key]

                    local_last_updated = change_request_meta['last_updated']
                    extracted_features = change_request.getExtractedFeatures(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))
                    extracted_features_meta = extracted_features['Meta']
                    mlabel = change_request.getManualRiskLabel(change_request_issue_key)

                    if mlabel is None or mlabel == 'None':
                        response['manual'] = None
                    else:
                        response['manual'] = mlabel
                        
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

                    response['features'] = {}
                    response['predictions'] = {}

                    if debug_test_mode:
                        self.send('Data:\n%s\n\n' % str(features))
                    
                    X = DV.transform(data)

                    X_test = test_data_set[0]
                    y_test = test_data_set[1]
                    
                    if debug_test_mode:
                        self.send('%s\n%s\n\n' % (str(len(X_test)), str(len(y_test))))

                    feature_name_list = []
                    for x, y in sorted(DV.vocabulary_.items(), key=lambda x: x[1]):
                        feature_name_list += [(x, features[x])]

                    if debug_test_mode:
                        self.send('Vocabulary:\n%s\n\n' % str(DV.vocabulary_))
                        self.send('Feature Name List:\n%s\n\n' % str(feature_name_list))
                        self.send('%s\n' % str(X_test))
                    
                    #for scaling_name, scalings_ in trained_models.items():
                    if True:
                        scaling_name = 'Robust Scaler'
                        scalings_ = trained_models[scaling_name]

                        if not isinstance(scalings_, dict):
                            continue
                        
                        X_scaled = X
                        X_test_scaled = X_test
                        if 'scaler' in scalings_:
                            X_scaled = scalings_['scaler'].transform(X)
                            X_test_scaled = scalings_['scaler'].transform(X_test)
                        
                        #for sampling_name, samplings_ in scalings_.items():
                        if True:
                            sampling_name = 'Undersample - Random Under Sample'
                            samplings_ = scalings_[sampling_name]

                            if not isinstance(samplings_, dict):
                                continue
                            
                            X_sampled = X_scaled
                            X_test_sampled = X_test_scaled
                            
                            #for fselection_name, fselections_ in samplings_.items():
                            if True:
                                fselection_name = 'Random Forest'
                                fselections_ = samplings_[fselection_name]

                                if not isinstance(fselections_, dict):
                                    continue
                                    
                                X_test_fselected = X_sampled
                                X_test_fselected = X_test_sampled
                                selected_feature_name_list = feature_name_list

                                if 'selector' in fselections_:
                                    X_fselected = fselections_['selector'].transform(X_sampled)
                                    X_test_fselected = fselections_['selector'].transform(X_test_sampled)

                                    selected_feature_name_list = []
                                    for x, y in zip(feature_name_list, fselections_['selector'].get_support()):
                                        if y == 1:
                                            if debug_test_mode:
                                                self.send('%s\n' % str(x))
                                            selected_feature_name_list += [(x[0], features[x[0]])]
                                
                                if debug_test_mode:
                                    self.send('Selected Feature Names List:\n%s\n\n' % str(selected_feature_name_list))
                                
                                #for classifier_name, classifier in fselections_.items():
                                #    if classifier_name == 'selector':
                                #        continue
                                if True:
                                    classifier_name = 'Random Forest (imbalance penalty)'
                                    classifier = fselections_[classifier_name]

                                    model_name = '%s - %s - %s - %s' % (scaling_name, sampling_name, fselection_name, classifier_name)
                                    prediction = classifier.predict(X_fselected)[0]
                                    response['predictions'][model_name] = prediction
                                    
                                    try:
                                        #response['feature_weights'][model_name] = sorted(list(zip(DV.vocabulary_, classifier.feature_importances_)), key=lambda x: -x[1])
                                        if debug_test_mode:
                                            self.send('Feature Importances: \n%s\n\n' % str(sorted(list(zip(selected_feature_name_list, classifier.feature_importances_)), key=lambda x: -x[1])))
                                        
                                        importance = permutation_importance(classifier, X_test_fselected, y_test, random_state = 1)
                                        importances = [(x[0][0], x[0][1], x[1]) for x in sorted(list(zip(selected_feature_name_list, importance['importances_mean'])), key=lambda x: -x[1])]

                                        this_importance = permutation_importance(classifier, np.concatenate((X_test_fselected, X_fselected)), np.concatenate((y_test, np.array([prediction]))), random_state = 1)
                                        this_importances = [(x[0][0], x[0][1], x[1]) for x in sorted(list(zip(selected_feature_name_list, this_importance['importances_mean'])), key=lambda x: -x[1])]
                                        
                                        if debug_test_mode:
                                            self.send('Importances:\n%s\n\n' % str(importances))
                                            self.send('This Importances:\n%s\n\n' % str(this_importances))
                                        
                                        response['features'][model_name] = this_importances
                                    except Exception as e:
                                        self.send('Exception %s\n\n' % str(exception_html(e)))
                                        pass
                    
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
