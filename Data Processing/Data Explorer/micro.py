self.send_response(200)
self.send_header("Content-type", "text/json")
self.end_headers()

try:
    response = {'result': 'None'}

    def load():
        import json
        import importlib.util
        jsonquery_spec = importlib.util.spec_from_file_location('jsonquery', '../Data Processing/jsonquery.py')
        jsonquery = importlib.util.module_from_spec(jsonquery_spec)
        jsonquery_spec.loader.exec_module(jsonquery)

        change_requests_spec = importlib.util.spec_from_file_location('change_requests', '../Data Processing/change_requests.py')
        change_request = importlib.util.module_from_spec(change_requests_spec)
        change_requests_spec.loader.exec_module(change_request)

        issues_spec = importlib.util.spec_from_file_location('issues', '../Data Processing/issues.py')
        issues = importlib.util.module_from_spec(issues_spec)
        issues_spec.loader.exec_module(issues)

        issue_maps = [issues.Issues('Microservice Demo')]

        change_request_list = [change_request.ChangeRequest(x) for x in issue_maps]

        return issue_maps, change_request_list

    if querystring['type'] == 'init':
        issue_maps, change_request_list = load()
        response['result'] = 'ok'

    elif querystring['type'] == 'handshake':
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
                        extracted_features = change_request.getExtractedFeatures(project_key, version_name, issues)
                        
                        response = extracted_features
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
