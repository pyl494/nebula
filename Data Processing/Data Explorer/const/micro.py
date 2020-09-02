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
    from sklearn.model_selection import train_test_split

    from change_requests import ChangeRequest

    import datetime
    import json

    import debug

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
                print(change_request_meta)

                if not change_request_meta is None:
                    last_predicted_date = change_request_meta['last_predicted_date']
                    local_last_updated = change_request_meta['last_updated']

                    if local_last_updated is None or local_last_updated < server_last_updated and not debug_test_mode:
                        response['result'] = 'Not Up-To-Date'
                    elif last_predicted_date is None or last_predicted_date < server_last_updated:
                        model = change_request.get_machine_learning_model()
                        features, label = model.prepare_data(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))

                        response['features'] = {}
                        response['predictions'] = {}

                        if debug_test_mode:
                            self.send('Data:\n%s\n\n' % str(features))

                        for other_change_request in change_request_list:
                            try:
                                other_model = other_change_request.get_machine_learning_model()
                                other_universe_name = other_change_request.get_issue_map().get_universe_name()

                                if debug_test_mode:
                                    self.send('\n\n--------\n%s\n--------\n' % other_universe_name)

                                X_test, y_test = ([], [])

                                for X, y in other_model.get_dataset_test():
                                    X_test += X
                                    y_test += y

                                X_test, y_test = (np.array(X_test), np.array(y_test))

                                X_discard, X_test, y_discard, y_test = train_test_split(
                                    X_test, y_test, stratify=y_test,
                                    test_size=.1, random_state=1)

                                #if debug_test_mode:
                                #    self.send('%s\n%s\n\n' % (str(len(X_test)), str(len(y_test))))

                                for x in other_model.iterate_test([features, X_test], X_impute_examples=X_test, configurations=[{'scaler_name': 'Robust Scaler', 'sampler_name': 'Oversample - ADASYN', 'selector_name': 'All Features', 'reducer_name': 'No Reduction', 'classifier_name': 'Random Forest (imbalance penalty)'}]):
                                    globals()['features'] = features
                                    feature_name_list = [(x, globals()['features'][0][x]) for x, y in sorted(x['DV'].vocabulary_.items(), key=lambda x: x[1]) if x in globals()['features'][0]]

                                    selected_feature_names_list = feature_name_list

                                    if not x['selector'] is None:
                                        selected_feature_names_list = [(x[0], globals()['features'][x[0]]) for x, y in zip(feature_name_list, x['selector'].get_support())
                                            if y == 1]

                                    if debug_test_mode:
                                        self.send('Vocabulary:\n%s\n\n' % str(x['DV'].vocabulary_))
                                        self.send('Feature Name List:\n%s\n\n' % str(x['feature_names_list']))
                                        self.send('%s\n\n' % str(x['X'][0]))

                                    model_name = '%s - %s - %s - %s - %s - %s' % (other_universe_name, x['scaler_name'], x['sampler_name'], x['selector_name'], x['reducer_name'], x['classifier_name'])
                                    prediction = x['classifier'].predict(x['X'][0])[0]

                                    response['predictions'][model_name] = prediction

                                    if debug_test_mode:
                                        self.send('Model: %s\n' % model_name)
                                        self.send('Prediction: %s\n\n' % prediction)
                                        self.send('Shapes:\nfeatures vs out: %s vs %s\nX_test vs out vs labels: %s vs %s vs %s\n' % (str(len(features)), str(x['X'][0].shape), str(X_test.shape), str(x['X'][1].shape), str(y_test.shape)))

                                    try:
                                        importance = permutation_importance(x['classifier'],  x['X'][1], y_test, random_state = 1)

                                        this_importance = permutation_importance(x['classifier'], np.concatenate((x['X'][1],  x['X'][0])), np.concatenate((y_test, np.array([prediction]))), random_state = 1)

                                        this_importances = [(x[0][0], x[0][1], x[1]) for x in sorted(list(zip(selected_feature_names_list, this_importance['importances_mean'])), key=lambda x: -x[1])]

                                        if debug_test_mode:
                                            importances = [(x[0][0], x[0][1], x[1]) for x in sorted(list(zip(selected_feature_names_list, importance['importances_mean'])), key=lambda x: -x[1])]
                                            self.send('Importances:\n%s\n\n' % str(importances))
                                            self.send('This Importances:\n%s\n\n' % str(this_importances))

                                        response['features'][model_name] = this_importances

                                        break # TODO: STOPPING EARLY FOR QUICKER RESPONSE

                                    except Exception as e:
                                        if debug_test_mode:
                                            self.send(str(debug.exception_html(e)))

                            except Exception as e:
                                if debug_test_mode:
                                    self.send(str(debug.exception_html(e)))

                        change_request.update_change_request_predictions(change_request_issue_key, {'predictions': response['predictions'], 'features': response['features']})
                        response['result'] = 'ok'

                    else:
                        response['predictions'] = change_request_meta['last_predictions']['predictions']
                        response['features'] = change_request_meta['last_predictions']['features']
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
                issues = json.loads(postvars['raw'])
                change_request.add(issues['issues'])
                response['result'] = 'ok'
                break

    self.send(json.dumps(response))

except Exception as e:
    response['result'] = 'error'
    response['exception'] = str(debug.exception_html(e))

    self.send(json.dumps(response))

exports = {
    'change_request_list': change_request_list
}
