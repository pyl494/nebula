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
                change_request_meta = change_request.get_change_request_meta(change_request_issue_key)

                if not change_request_meta is None:
                    local_last_updated = change_request_meta['last_updated'].replace(tzinfo=None)

                    if local_last_updated < server_last_updated and not debug_test_mode:
                        response['result'] = 'Not Up-To-Date'
                    else:
                        model = change_request.getMachineLearningModel()
                        features, label = model.prepare_data(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))

                        response['features'] = {}
                        response['predictions'] = {}

                        if debug_test_mode:
                            self.send('Data:\n%s\n\n' % str(features))

                        X_test, y_test = ([], [])

                        for X, y in model.get_dataset_test():
                            X_test += X
                            y_test += y
                        
                        #if debug_test_mode:
                        #    self.send('%s\n%s\n\n' % (str(len(X_test)), str(len(y_test))))

                        for x in model.iterate_test([features, X_test]):
                            X_fselected = x['X'][0]
                            X_test_fselected = x['X'][1]

                            scaling_name = x['scaling_name']
                            sampling_name = x['sampling_name']
                            fselection_name = x['fselection_name']
                            classifier_name = x['classifier_name']
                            DV = x['DV']
                            scaler = x['scaler']
                            sampler = x['sampler']
                            selector = x['selector']
                            classifier = x['classifier']
                            feature_names_list = x['feature_names_list']
                            selected_feature_names_list = x['selected_feature_names_list']

                            if debug_test_mode:
                                self.send('Vocabulary:\n%s\n\n' % str(DV.vocabulary_))
                                self.send('Feature Name List:\n%s\n\n' % str(feature_names_list))
                                self.send('%s\n' % str(X_test))
                            
                            classifier = fselections_[classifier_name]

                            model_name = '%s - %s - %s - %s' % (scaling_name, sampling_name, fselection_name, classifier_name)
                            prediction = classifier.predict(X_fselected)[0]
                            response['predictions'][model_name] = prediction
                            
                            try:
                                #response['feature_weights'][model_name] = sorted(list(zip(DV.vocabulary_, classifier.feature_importances_)), key=lambda x: -x[1])
                                #f debug_test_mode:
                                #    self.send('Feature Importances: \n%s\n\n' % str(sorted(list(zip(selected_feature_names_list, classifier.feature_importances_)), key=lambda x: -x[1])))
                                
                                importance = permutation_importance(classifier, X_test_fselected, y_test, random_state = 1)
                                importances = [(x[0][0], x[0][1], x[1]) for x in sorted(list(zip(selected_feature_names_list, importance['importances_mean'])), key=lambda x: -x[1])]

                                this_importance = permutation_importance(classifier, np.concatenate((X_test_fselected, X_fselected)), np.concatenate((y_test, np.array([prediction]))), random_state = 1)
                                this_importances = [(x[0][0], x[0][1], x[1]) for x in sorted(list(zip(selected_feature_names_list, this_importance['importances_mean'])), key=lambda x: -x[1])]
                                
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
                change_request_meta = change_request.get_change_request_meta(change_request_issue_key)

                if not change_request_meta is None:
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
                change_request.add(postvars['raw'])
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
