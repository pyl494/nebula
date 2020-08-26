self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

import datetime
import importlib.util
import html

out = ""

try:
    import sys

    if 'issues' in sys.modules:
        del sys.modules['issues']

    if 'change_requests' in sys.modules:
        del sys.modules['change_requests']

    if 'jsonquery' in sys.modules:
        del sys.modules['jsonquery']

    if 'datautil' in sys.modules:
        del sys.modules['datautil']

    import jsonquery
    import datautil

    import issues as mIssues
    import change_requests

    def displayIssueChanges(type, changes, created_date):
        global datautil
        global jsonquery
        global mIssues

        out = '<table><tr><th>Date</th><th>Time Since Creation</th><th>From</th><th>To</th></tr>'

        for change in changes:
            change_timestamp = datautil.unlist_one(jsonquery.query(change, '^created'))
            change_date = mIssues.Issues.parseDateTime(change_timestamp)
            time_since_created = change_date - created_date

            items = jsonquery.query(change, 'items.$field:%s' % type)
            for item in items:
                item_from = item['fromString']
                item_to = item['toString']

                out += '''<tr>
                    <td>{date}</td>
                    <td>{time_since}</td>
                    <td>{sfrom}</td>
                    <td>{to}</td>
                </tr>'''.format(
                    date = html.escape(change_timestamp),
                    time_since = html.escape(str(time_since_created)),
                    sfrom = html.escape(str(item_from)),
                    to = html.escape(str(item_to))
                )
        out += '</table>'
        return out

    def iterate_list(items):
        global html
        out = '<ul>'
        for item in items:
            out += '<li>%s</li>' % html.escape(item)
        out += '</ul>'

        return out

    def displayIssueLinks(direction, issuelinks, issue_map):
        global iterate_list
        global datautil
        global jsonquery
        global mIssues
        global change_request_issue_key
        global change_request_project_key

        out = '<table><tr><th>Priority</th><th>Issue Type</th><th>Status</th><th>Issue Key</th><th>Fix Versions</th><th>Affects Versions</th><th width="50%">Summary</th><th>Data</th><th>Relationship</th></tr>'
        for issue in issuelinks:
            issue_key = datautil.unlist_one(jsonquery.query(issue, direction + 'Issue.^key'))
            priority = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.priority.^name'))
            status = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.status.^name'))
            issuetype = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.issuetype.^name'))
            relationship = ' :: '.join(jsonquery.query(issue, 'type.^' + direction))
            summary = datautil.unlist_one(jsonquery.query(issue, direction + 'Issue.fields.^summary'))

            gissue = issue_map.getIssueByKey(issue_key)
            fixVersion_names = jsonquery.query(gissue, 'fields.fixVersions.^name')
            affectsVersion_names = jsonquery.query(gissue, 'fields.versions.^name')

            out += """
                <tr>
                    <td>{priority}</td>
                    <td>{issuetype}</td>
                    <td>{status}</td>
                    <td>{issue_key}</td>
                    <td>{fixVersions}</td>
                    <td>{affectsversions}</td>
                    <td>{summary}</td>
                    <td>
                        <a href="/view?universe={universe}&change_request={change_request_issue_key}&issue_key={issue_key}&view={view}">View Issue</a>
                    </td>
                    <td>{relationship}</td>
                </tr>
            """.format(
                universe = html.escape(querystring['universe']),
                view = html.escape(querystring['view']),
                priority = html.escape(priority),
                status = html.escape(status),
                issuetype = html.escape(issuetype),
                fixVersions = iterate_list(fixVersion_names),
                affectsversions = iterate_list(affectsVersion_names),
                change_request_issue_key = html.escape(str(change_request_issue_key)),
                issue_key = html.escape(str(issue_key)),
                summary = html.escape(str(summary)),
                relationship = html.escape(relationship)
            )

        out += '</table>'

        return out

    def displaySubtasks(subtasks, issue_map):
        global iterate_list
        global datautil
        global jsonquery
        global mIssues
        global change_request_issue_key

        out = '<table><tr><th>Priority</th><th>Issue Type</th><th>Status</th><th>Issue Key</th><th>Fix Versions</th><th>Affects Versions</th><th width="50%">Summary</th><th>Data</th></tr>'
        for issue in subtasks:
            issue_key = datautil.unlist_one(jsonquery.query(issue,  '^key'))
            priority = ' :: '.join(jsonquery.query(issue, 'fields.priority.^name'))
            status = ' :: '.join(jsonquery.query(issue, 'fields.status.^name'))
            issuetype = ' :: '.join(jsonquery.query(issue, 'fields.issuetype.^name'))
            summary = datautil.unlist_one(jsonquery.query(issue, 'fields.^summary'))

            gissue = issue_map.getIssueByKey(issue_key)
            fixVersion_names = jsonquery.query(gissue, 'fields.fixVersions.^name')
            affectsVersion_names = jsonquery.query(gissue, 'fields.versions.^name')

            out += """
                <tr>
                    <td>{priority}</td>
                    <td>{issuetype}</td>
                    <td>{status}</td>
                    <td>{issue_key}</td>
                    <td>{fixVersions}</td>
                    <td>{affectsversions}</td>
                    <td>{summary}</td>
                    <td>
                        <a href="/view?universe={universe}&change_request={change_request_issue_key}&issuekey={issue_key}&view={view}">View Issue</a>
                    </td>
                </tr>
            """.format(
                universe = html.escape(querystring['universe']),
                view = html.escape(querystring['view']),
                key = html.escape(str(change_request_project_key)),
                priority = html.escape(priority),
                status = html.escape(status),
                issuetype = html.escape(issuetype),
                fixVersions = iterate_list(fixVersion_names),
                affectsversions = iterate_list(affectsVersion_names),
                version = html.escape(str(change_request_version_name)),
                change_request_issue_key = html.escape(str(change_request_issue_key)),
                issue_key = html.escape(str(issue_key)),
                summary = html.escape(str(summary))
            )

        out += '</table>'

        return out

    def displayIssueExtractedFeatures(issue_map, extracted_features):
        global change_request_project_key
        global change_request_version_name
        global change_request_issue_key
        global displaySubtasks
        global displayIssueLinks
        global displayIssueChanges

        out = ''
        if not extracted_features['parent_key'] is None:
            out += '<h3>Parent: <a href="/view?universe={universe}&change_request={change_request_issue_key}&issue_key={issue_key}&view=issue">{issue_key} - {summary}</a></h3>'.format(
                universe = html.escape(querystring['universe']),
                project = html.escape(str(change_request_project_key)),
                version = html.escape(str(change_request_version_name)),
                change_request_issue_key = html.escape(str(change_request_issue_key)),
                issue_key = html.escape(extracted_features['parent_key']),
                view = html.escape(querystring['view']),
                summary = html.escape(extracted_features['parent_summary'])
            )
        out += '<h3>Summary: %s</h3>' % html.escape(extracted_features['summary'])
        out += '<h3>Resolution:</h3> <p>%s</p>' % html.escape(str(extracted_features['resolution_name']))
        out += '<h3>Issue Type:</h3> <p>%s</p>' % html.escape(str(extracted_features['issuetype_name']))
        out += '<h3>Priority*:</h3> <p>%s</p>' % html.escape(str(extracted_features['priority_name']))
        out += '<h3>Assignee:</h3> <p>%s - %s</p>' % (html.escape(str(extracted_features['assignee_displayName'])), html.escape(str(extracted_features['assignee_accountId'])))
        out += '<h3>Reporter:</h3> <p>%s - %s</p>' % (html.escape(str(extracted_features['reporter_displayName'])), html.escape(str(extracted_features['reporter_accountId'])))
        out += '<h3>Created Date:</h3> <p>%s</p>' % html.escape(str(extracted_features['created_timestamp']))
        out += '<h3>Resolution Date:</h3> <p>%s</p>' % html.escape(str(extracted_features['resolutiondate_timestamp']))
        out += '<h3>Last Updated Date:</h3> <p>%s</p>' % html.escape(str(extracted_features['updated_timestamp']))
        out += '<h3>Due Date:</h3> <p>%s</p>' % html.escape(str(extracted_features['duedate_timestamp']))
        out += '<h3>Fix Versions:</h3> <p>%s</p>' % iterate_list(extracted_features['fixVersion_names'])
        out += '<h3>Affected Versions:</h3> <p>%s</p>' % iterate_list(extracted_features['affectsVersion_names'])
        out += '<h3>Description:</h3> <p>%s</p>' % html.escape(str(extracted_features['description'])).replace('\n', '<br/>')

        out += '<h3>Subtasks</h3>'
        out += displaySubtasks(extracted_features['subtasks'], issue_map)

        out += '<h3>Inward Issues</h3>'
        out += displayIssueLinks('inward', extracted_features['issuelinks_inward'], issue_map)

        out += '<h3>Outward Issues</h3>'
        out += displayIssueLinks('outward', extracted_features['issuelinks_outward'], issue_map)

        out += '<h3>Comments:</h3>'
        out += '<table><tr><th>Post Date</th><th>Author</th><th width="80%">Message</th></tr>'
        for comment in extracted_features['comments']:
            out += '<tr><td>{pdate}</td><td>{author}</td><td>{message}</td></tr>'.format(
                pdate = html.escape(comment['created_timestamp']),
                author = html.escape(comment['author_displayName']),
                message = html.escape(comment['message'])
            )
        out += '</table>'

        out += '<hr/>'
        out += '<h2>Change Log:</h2>'
        out += '<h3>Assignee Changes:</h2>'
        out += displayIssueChanges('assignee', extracted_features['changes']['assignee_displayName'], extracted_features['created_date'])

        out += '<h3>Reporter Changes:</h2>'
        out += displayIssueChanges('reporter', extracted_features['changes']['reporter_displayName'], extracted_features['created_date'])

        out += '<h3>Resolution Changes:</h2>'
        out += displayIssueChanges('resolution', extracted_features['changes']['resolution_name'], extracted_features['created_date'])

        out += '<h3>Status Changes:</h2>'
        out += displayIssueChanges('status', extracted_features['changes']['status_name'], extracted_features['created_date'])

        out += '<h3>Priority Changes*:</h2>'
        out += displayIssueChanges('priority', extracted_features['changes']['priority_name'], extracted_features['created_date'])

        out += '<h3>Issue Type Changes:</h2>'
        out += displayIssueChanges('issuetype', extracted_features['changes']['issuetype_name'], extracted_features['created_date'])

        out += '<h3>Fix Version Changes*:</h2>'
        out += displayIssueChanges('Fix Version', extracted_features['changes']['fixVersion_names'], extracted_features['created_date'])

        out += '<h3>Affects Version Changes:</h2>'
        out += displayIssueChanges('Version', extracted_features['changes']['affectsVersion_names'], extracted_features['created_date'])

        out += '<h3>Description Changes*:</h2>'
        out += displayIssueChanges('description', extracted_features['changes']['description'], extracted_features['created_date'])

        out += '<hr/>'
        out += '<h2>Derived Data:</h2>'
        out += '<h3>Creation To Last Update:</h3> %s' % html.escape(str(extracted_features['issue_duration']))
        out += '<h3>Delays* [~]:</h3> %s' % html.escape(str(extracted_features['delays']))
        out += '<h3>Number of Fix Versions*:</h3> <p>%s</p>' % extracted_features['number_of_fixVersions']
        out += '<h3>Number of Affects Versions:</h3> <p>%s</p>' % extracted_features['number_of_affectsversions']
        out += '<h3>Number of subtasks:</h3> <p>%s</p>' % extracted_features['number_of_subtasks']
        out += '<h3>Number of issues links*:</h3> <p>%s</p>' % extracted_features['number_of_issuelinks']
        out += '<h3>Number of issues blocking this issue*:</h3> <p>%s</p>' % extracted_features['number_of_blocked_by_issues']
        out += '<h3>Number of issues this blocks* [?]:</h3> <p>%s</p>' % extracted_features['number_of_blocks_issues']
        out += '<h3>Number of Comments*:</h3> <p>%s</p>' % extracted_features['number_of_comments']
        out += '<h3>Discussion Time*:</h3> %s' % html.escape(str(extracted_features['discussion_time']))

        return out

    issue_map = None
    change_request_meta = None
    change_request_project_key = None
    change_request_version_name = None
    change_request_issue_key = None
    if 'change_request' in querystring:
        change_request_issue_key = querystring['change_request']

    for change_request in change_request_list:
        if change_request.getIssueMap().getUniverseName() == querystring['universe']:
            issue_map = change_request.getIssueMap()
            if not change_request_issue_key is None:
                change_request_meta = change_request.get_change_request_meta(change_request_issue_key)
                change_request_project_key = change_request_meta['project_key']
                change_request_version_name = str(change_request_meta['fixVersion_name'])
            break

    if querystring['view'] == 'linked' or querystring['view'] == 'affected':

        these_issues = change_request_meta[querystring['view'] + '_issues']

        out += '''
            <ul>
                <li><a href="view?universe={universe}&change_request={change_request_issue_key}&&view=linked">View Fix Versions [Change Request]</a></li>
                <li><a href="view?universe={universe}&change_request={change_request_issue_key}&&view=affected">View Affected Versions</a></li>
            </ul>
        '''.format(
            universe = querystring['universe'],
            change_request_issue_key = html.escape(change_request_issue_key)
        )

        mlabel = change_request.getManualRiskLabel(change_request_issue_key)

        out += '''
            <h2>Automatic Label:</h2>
            {alabel}
            <h2>Manual Label:</h2>
            <span id="mlabel">{mlabel}</span><br/><br/>
            '''.format(
                alabel = change_request.getAutomaticRiskLabel(change_request_issue_key),
                mlabel = str(mlabel)
            )

        out += '''
        <script>
            function handleMLabel(element){
                let label = element.options[element.selectedIndex].value;

                let xhttp = new XMLHttpRequest();
                xhttp.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200) {
                        document.getElementById("mlabel").innerHTML = xhttp.responseText;
                    }
                };

                xhttp.open("GET", `/label?type=change request&universe=%s&change_request=%s&label=${label}`, true);
                xhttp.send();
            }
        </script>
        <form>
            <select name="label" id="label" onchange="handleMLabel(this);" onload="setMLabel(this);">
                <option value="None">None</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
            </select>
        </form>
        <script>
            function setMLabel(element){
                element.value = '%s';
                console.log(element.selectedIndex);
            }
            setMLabel(document.getElementById('label'));
        </script>
        <br/>
        ''' % (
            querystring['universe'],
            change_request_issue_key,
            str(mlabel)
        )

        out += '<hr/>'
        out += '<h2>Extracted Features</h2>'

        #issues_bugs = datautil.unlist_one(jsonquery.query(issue, 'fields.issuetype.name:Bug'))
        #issues_features = datautil.unlist_one(jsonquery.query(issue, 'fields.issuetype.name:Feature'))

        extracted_features = change_request.getExtractedFeatures(change_request_issue_key, change_request_meta['release_date'])

        out += '<h3>Change Request</h3>'
        out += '<h4>Release Date</h4>%s' % str(extracted_features['release_date'])
        out += '<h4>Elapsed Time</h4>%s' % str(extracted_features['elapsed_time'])

        out += "<h3>Issues</h3>"
        out += '<h4>Number of Issues</h4>%s' % str(extracted_features['number_of_issues'])

        out += '<h4>Statistical Aggregations</h4>'
        out += '<table><tr><th>Feature</th>'
        for aggregator_name in extracted_features['Meta']['aggregators']:
            out += '<th>%s</th>' % aggregator_name
        out += '</tr>'
        for feature in extracted_features['Meta']['aggregated_features']:
            out += '<tr><td>%s</td>' % feature
            for aggregator_name in extracted_features['Meta']['aggregators']:
                out += '<td>%s</td>' % str(extracted_features[feature][aggregator_name])
            out += '</tr>'
        out += '</table>'

        out += '<h4>Discussion Time</h4>%s' % str(extracted_features['discussion_time'])
        out += '<h4>Number of Comments</h4>%s' % str(extracted_features['number_of_comments'])
        out += '<h4>Number of Blocked By Issues</h4>%s' % str(extracted_features['number_of_blocked_by_issues'])
        out += '<h4>Number of Blocks Issues</h4>%s' % str(extracted_features['number_of_blocks_issues'])
        out += '<h4>Delays</h4>%s' % str(extracted_features['delays'])
        out += '<h4>Number of Participants</h4>%s' % str(extracted_features['number_of_participants'])
        out += "<h4>Participants</h4>%s" % str(extracted_features['participants'].values())
        out += '<h4>Number of Team Members</h4>%s' % str(extracted_features['number_of_team_members'])
        out += "<h4>Team Members</h4>%s" % str(extracted_features['team_members'].values())
        out += '<h4>Number of Reporters</h4>%s' % str(extracted_features['number_of_reporters'])
        out += "<h4>Reporters</h4>%s" % str(extracted_features['reporters'].values())

        out += '<hr/>'


        out += '<table><tr><th>Created Date</th><th>Updated Date</th><th>Priority</th><th>Issue Type</th><th>Status</th><th>Resolution</th><th>Issue Key</th><th width="50%">Summary</th><th>Data</th><th>External Link</th></tr>'

        issues = {
            #issue_key:{
            #   'issue':{issuedata}
            #   'subtasks': {#issue_key:{...}}
            # }
        }

        for issue in issue_map.getIssuesByKeys(these_issues):
            issue_key = issue['key']

            parent_key = jsonquery.query(issue, 'fields.parent.^key')
            subtasks = datautil.unlist_one(jsonquery.query(issue, 'fields.^subtasks'))

            if len(parent_key) == 1:
                datautil.map_list(issues, (parent_key[0],), issue_key)
            else:
                datautil.map_touch(issues, (issue_key, ), [])

        for parent_key, subtasks in issues.items():
            issuepack = [{'issuekey': parent_key, 'indent': 0}]
            issuepack += [{'issuekey': x, 'indent': 1} for x in subtasks]

            for pack in issuepack:
                issue_key = pack['issuekey']
                issue = issue_map.getIssueByKey(issue_key)
                indent = pack['indent']

                priority = ' :: '.join(jsonquery.query(issue, 'fields.priority.^name'))
                status = ' :: '.join(jsonquery.query(issue, 'fields.status.^name'))
                resolution = ' :: '.join(jsonquery.query(issue, 'fields.resolution.^name'))
                issuetype = ' :: '.join(jsonquery.query(issue, 'fields.issuetype.^name'))

                out += """
                    <tr>
                        <td style="padding-left: {indent}px">{cdate}</td>
                        <td>{udate}</td>
                        <td>{priority}</td>
                        <td>{issuetype}</td>
                        <td>{status}</td>
                        <td>{resolution}</td>
                        <td>{issue_key}</td>
                        <td>{summary}</td>
                        <td>
                            <a href="/view?universe={universe}&change_request={change_request_issue_key}&issue_key={issue_key}&view=issue">View Issue</a>
                        </td>
                        <td>
                            <a href="{external}">External Link</a>
                        </td>
                    </tr>
                """.format(
                    universe = html.escape(querystring['universe']),
                    view = html.escape(querystring['view']),
                    indent = str(indent * 20),
                    cdate = html.escape(issue['fields']['created']),
                    udate = html.escape(issue['fields']['updated']),
                    key = html.escape(change_request_project_key),
                    priority = html.escape(priority),
                    status = html.escape(status),
                    resolution = html.escape(resolution),
                    issuetype = html.escape(issuetype),
                    version = html.escape(change_request_version_name),
                    change_request_issue_key = html.escape(change_request_issue_key),
                    issue_key = html.escape(issue_key),
                    summary = html.escape(issue['fields']['summary']),
                    external = html.escape(issue['self'])
                )

        out += '</table>'

    elif querystring['view'] == 'issue':
        issue = issue_map.getIssueByKey(querystring['issue_key'])

        change_request_release_date = None
        version_info_map = []
        if not change_request_meta is None:
            change_request_release_date = change_request_meta['release_date']
            version_info_map = change_request.get_project_versions(change_request_project_key)

        out += '<h2>Extracted Data:</h2>'
        out += '<table><tr><th>@Creation</th><th>@Change Request Release Date - %s</th><th>@Latest</th></tr>' % str(change_request_release_date)

        out += '<tr class="nohover"><td>'
        extracted_features = issue_map.getExtractedFeatures(issue, version_info_map, mIssues.Issues.parseDateTime(issue['fields']['created']))
        out += displayIssueExtractedFeatures(issue_map, extracted_features)

        out += '</td><td>'

        if not change_request_release_date is None:
            extracted_features = issue_map.getExtractedFeatures(issue, version_info_map, change_request_release_date)
            if not extracted_features is None:
                out += displayIssueExtractedFeatures(issue_map, extracted_features)
            else:
                out += "This issue was created after the change request release date."

        out += '</td><td>'

        extracted_features = issue_map.getExtractedFeatures(issue, version_info_map, datetime.datetime.now(tz=datetime.timezone.utc))
        out += displayIssueExtractedFeatures(issue_map, extracted_features)

        out += '</td></tr></table>'

        out += '<hr/>'
        out += '<h2>Raw Data:</h2>'
        out += '<pre>%s</pre>' % html.escape(json.dumps(issue, indent=4, cls=change_requests.JSONDumper))

except Exception as e:
    out += exception_html(e)

self.send(
    """
    <html>
        <head>
            <title>Explorer</title>
            <link rel="stylesheet" href="/css" media="all">
        </head>
        <body>
            <h1>[%s] %s - %s - %s - version %s</h1>
            %s

        </body>
    </html>"""  % (html.escape(str(change_request_issue_key)), html.escape(querystring['universe']), html.escape(str(change_request_project_key)), html.escape(querystring['view']), html.escape(str(change_request_version_name)), out))
