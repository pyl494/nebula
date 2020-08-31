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
        server_last_updated = mIssues.Issues.parse_date_time(querystring['updated'])

        found = False
        for change_request in change_request_list:
            issue_map = change_request.get_issue_map()

            if issue_map.get_universe_name() == 'Microservice Demo' or debug_test_mode:
                change_request_meta = change_request.get_change_request_meta(change_request_issue_key)

                if not change_request_meta is None:
                    local_last_updated = change_request_meta['last_updated']

                    if local_last_updated < server_last_updated and not debug_test_mode:
                        response['result'] = 'Not Up-To-Date'
                    else:
                        model = change_request.get_machine_learning_model()
                        features, label = model.prepare_data(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))

                        response['features'] = {}
                        response['predictions'] = {}

                        if debug_test_mode:
                            self.send('Data:\n%s\n\n' % str(features))

                        for other_change_request in change_request_list:
                            other_model = other_change_request.get_machine_learning_model()
                            other_universe_name = other_change_request.get_issue_map().get_universe_name()

                            if debug_test_mode:
                                self.send('\n\n--------\n%s\n--------\n' % other_universe_name)

                            response['predictions'][other_universe_name] = {}
                            X_test, y_test = ([], [])

                            for X, y in model.get_dataset_test():
                                X_test += X
                                y_test += y

                            #if debug_test_mode:
                            #    self.send('%s\n%s\n\n' % (str(len(X_test)), str(len(y_test))))
                            try:
                                for x in other_model.iterate_test([features], X_impute_examples=X_test, configurations=[{'scaler_name': 'No Scaling', 'sampler_name': 'No Sampling', 'selector_name': 'All Features', 'reducer_name': 'No Reduction', 'classifier_name': 'Linear SVC'}]):
                                    X_test_ = x['X'][0]

                                    feature_names_list = x['feature_names_list']
                                    selected_feature_names_list = x['selected_feature_names_list']

                                    if debug_test_mode:
                                        self.send('Vocabulary:\n%s\n\n' % str(x['DV'].vocabulary_))
                                        self.send('Feature Name List:\n%s\n\n' % str(x['feature_names_list']))
                                        self.send('%s\n\n' % str(X_test_))

                                    model_name = '%s - %s - %s - %s' % (x['scaler_name'], x['sampler_name'], x['selector_name'], x['classifier_name'])
                                    prediction = x['classifier'].predict(X_test_)[0]

                                    response['predictions'][other_universe_name][model_name] = prediction

                                    if debug_test_mode:
                                        self.send('Model: %s\n' % model_name)
                                        self.send('Prediction: %s\n\n' % prediction)
                            except Exception as e:
                                if debug_test_mode:
                                    self.send(str(exception_html(e)))

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
            issue_map = change_request.get_issue_map()

            if issue_map.get_universe_name() == 'Microservice Demo':
                change_request_meta = change_request.get_change_request_meta(change_request_issue_key)

                if not change_request_meta is None:
                    found = True
                    change_request.set_manual_risk_label(change_request_issue_key, label)
                    mlabel = change_request.get_manual_risk_label(change_request_issue_key)

                    if label == mlabel:
                        response['result'] = 'ok'
                    else:
                        response['result'] = 'Failed'

                    break
        if not found:
            response['result'] = 'Not Found'

    elif querystring['type'] == 'add':

        for change_request in change_request_list:
            issue_map = change_request.get_issue_map()

            if issue_map.get_universe_name() == 'Microservice Demo':
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
