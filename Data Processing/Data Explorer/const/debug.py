self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

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