self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

self.send(
    '''
    <html>
        <head>
            <title>Explorer - Debug</title>
            <link rel="stylesheet" href="/css" media="all">
        </head>
        <body>''')

import json

change_fields = {}

for change_request in change_request_list:
    issue_map = change_request.getIssueMap()
    self.send('<h1>%s</h1>' % issue_map.getUniverseName())
    for issue_key, issue in issue_map.get().items():
        if 'histories' in issue['changelog']:
            total = issue['changelog']['total']
            maxResults = issue['changelog']['maxResults']
            if total != maxResults:
                self.send('<b>Warning, incomplete changelog</b>: %s (%s of %s)<br/>' % (issue_key, str(maxResults), str(total)))

            for change in issue['changelog']['histories']:
                for item in change['items']:
                    c = item['field']
                    
                    if 'fieldId' in item:
                        c += ' : %s' % item['fieldId']
                    
                    if 'fieldtype' in item:
                        c += ' (%s)' % item['fieldtype']
                        
                    change_fields[c] = item

      
self.send('<h2>Change fields</h2> <pre>%s</pre><br/>' % json.dumps(change_fields, indent=2))


def blah(self, change_request_list):
    import datetime
    from issues import Issues
    import html
    import jsonquery
    import json

    for change_request in change_request_list:
        change_request_meta_map = change_request.getChangeRequestMetaMap()
        issue_map = change_request.getIssueMap()
        projects_version_info_map = change_request.getProjectsVersionInfoMap()

        for change_request_issue_key, change_request_meta in change_request_meta_map.items():
            project_key = change_request_meta['project_key']
            linked_issues = change_request_meta['linked_issues']
            
            if len(linked_issues) > 10:
                for issue_key in linked_issues:
                    self.send('<h2>%s - %s</h2>' % (change_request_issue_key, issue_key))
                    self.send('<table><tr><th>@Creation</th><th>Latest</th></tr>')
                    self.send('<tr class="nohover"><td>')
                    date = Issues.parseDateTime('2018-07-26T09:04:26.161-0500')
                    datenow = datetime.datetime.now(tz=datetime.timezone.utc)

                    features = issue_map.getExtractedFeatures(issue_key, projects_version_info_map[project_key], date)
                    for feature_key, feature in features.items():
                        self.send('<b>%s</b> %s<br/>' %(feature_key, html.escape(str(feature))))

                    self.send('</td><td>')

                    features = issue_map.getExtractedFeatures(issue_key, projects_version_info_map[project_key], datenow)
                    for feature_key, feature in features.items():
                        self.send('<b>%s</b> %s<br/>' %(feature_key, html.escape(str(feature))))

                    self.send('</td></tr></table>')

                    return
            else:
                continue
        continue
        features = change_request.getExtractedFeatures(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))
        if features['number_of_issues'] > 10:
            for feature_key, feature in features.items():
                self.send('%s %s<br/>' %(feature_key, feature))
                
                self.send('----------<br/>')
                features = change_request.getExtractedFeatures(change_request_issue_key, Issues.parseDateTimeSimple('2019-07-25'))
                for feature_key, feature in features.items():
                    self.send('%s %s<br/>' %(feature_key, feature))
            
            return

self.send('<h2>Extracted Features Time</h2>')
blah(self, change_request_list)

self.send('</></html>')
