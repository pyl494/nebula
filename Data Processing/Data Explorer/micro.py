self.send_response(200)
self.send_header("Content-type", "text/json")
self.end_headers()

try:
    response = {'result': 'None'}

    from sklearn.feature_extraction import DictVectorizer
    from sklearn import metrics
    from sklearn.utils.extmath import density

    if querystring['type'] == 'handshake':
        project_key = querystring['project']
        version_name = querystring['version']

        found = False
        for change_request in change_request_list:
            issue_map = change_request.getIssueMap()
            projects_fixVersion_issue_map = change_request.getProjectsFixVersionIssueMap()

            if issue_map.getUniverseName() == 'Microservice Demo':
                if project_key in projects_fixVersion_issue_map:
                    version_issue_map = projects_fixVersion_issue_map[project_key]
                    if version_name in version_issue_map:
                        issues = version_issue_map[version_name]
                        features = change_request.getExtractedFeatures(project_key, version_name, issues)

                        if mlabel is None or mlabel == 'None':
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
                            
                            for name, clf in zip(names, classifiers):
                                prediction = clf.predict(X)[0]
                                print(prediction)
                                response['predictions'][name] = ['low', 'medium', 'high'][prediction]

                        
                        response['result'] = 'ok'

                        found = True
                        break

        if not found:
            response['result'] = 'Not Found'

    elif querystring['type'] == 'add':    
        for change_request in change_request_list:
            issue_map = change_request.getIssueMap()

            if issue_map.getUniverseName() == 'Microservice Demo':
                issue_map.add(postvars['issues'])
                change_request.generate()
                response['result'] = 'ok'
                break
    
    self.send(json.dumps(response))

except Exception as e:
    response['result'] = 'error'
    response['exception'] = str(exception_html(e))

    self.send(json.dumps(response))
