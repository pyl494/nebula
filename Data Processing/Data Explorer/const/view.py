self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

import datetime
import importlib.util
import html

out = ""

try:
    jsonquery_spec = importlib.util.spec_from_file_location('jsonquery', '../Data Processing/jsonquery.py')
    jsonquery = importlib.util.module_from_spec(jsonquery_spec)
    jsonquery_spec.loader.exec_module(jsonquery)

    datautil_spec = importlib.util.spec_from_file_location('datautil', '../Data Processing/datautil.py')
    datautil = importlib.util.module_from_spec(datautil_spec)
    datautil_spec.loader.exec_module(datautil)

    mIssues_spec = importlib.util.spec_from_file_location('issues', '../Data Processing/issues.py')
    mIssues = importlib.util.module_from_spec(mIssues_spec)
    mIssues_spec.loader.exec_module(mIssues)

    def extract_changes(type, changes, created_date):
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
        out = '<table><tr><th>Priority</th><th>Issue Type</th><th>Status</th><th>Issue Key</th><th>Fix Versions</th><th>Affects Versions</th><th width="50%">Summary</th><th>Data</th><th>Relationship</th></tr>'
        for issue in issuelinks:
            issue_key = datautil.unlist_one(jsonquery.query(issue, direction + 'Issue.^key'))
            priority = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.priority.^name'))
            status = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.status.^name'))
            issuetype = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.issuetype.^name'))
            relationship = ' :: '.join(jsonquery.query(issue, 'type.^' + direction))
            summary = datautil.unlist_one(jsonquery.query(issue, direction + 'Issue.fields.^summary'))

            gissue = issue_map.get(issue_key)
            fixversion_names = jsonquery.query(gissue, 'fields.fixVersions.^name')
            affectversion_names = jsonquery.query(gissue, 'fields.versions.^name')

            out += """
                <tr>
                    <td>{priority}</td>
                    <td>{issuetype}</td>
                    <td>{status}</td>
                    <td>{issue_key}</td>
                    <td>{fixversions}</td>
                    <td>{affectsversions}</td>
                    <td>{summary}</td>
                    <td>
                        <a href="/view?universe={universe}&project={key}&version={version}&issuekey={issue_key}&view={view}">View Issue</a>
                    </td>
                    <td>{relationship}</td>
                </tr>
            """.format(
                universe = html.escape(querystring['universe']),
                view = html.escape(querystring['view']),
                key = html.escape(querystring['project']),
                priority = html.escape(priority),
                status = html.escape(status),
                issuetype = html.escape(issuetype),
                fixversions = iterate_list(fixversion_names),
                affectsversions = iterate_list(affectversion_names),
                version = html.escape(querystring['version']),
                issue_key = html.escape(str(issue_key)),
                summary = html.escape(str(summary)),
                relationship = html.escape(relationship)
            )

        out += '</table>'

        return out

    def displaySubtasks(subtasks, issue_map):
        out = '<table><tr><th>Priority</th><th>Issue Type</th><th>Status</th><th>Issue Key</th><th>Fix Versions</th><th>Affects Versions</th><th width="50%">Summary</th><th>Data</th></tr>'
        for issue in subtasks:
            issue_key = datautil.unlist_one(jsonquery.query(issue,  '^key'))
            priority = ' :: '.join(jsonquery.query(issue, 'fields.priority.^name'))
            status = ' :: '.join(jsonquery.query(issue, 'fields.status.^name'))
            issuetype = ' :: '.join(jsonquery.query(issue, 'fields.issuetype.^name'))
            summary = datautil.unlist_one(jsonquery.query(issue, 'fields.^summary'))

            gissue = issue_map.get(issue_key)
            fixversion_names = jsonquery.query(gissue, 'fields.fixVersions.^name')
            affectversion_names = jsonquery.query(gissue, 'fields.versions.^name')

            out += """
                <tr>
                    <td>{priority}</td>
                    <td>{issuetype}</td>
                    <td>{status}</td>
                    <td>{issue_key}</td>
                    <td>{fixversions}</td>
                    <td>{affectsversions}</td>
                    <td>{summary}</td>
                    <td>
                        <a href="/view?universe={universe}&project={key}&version={version}&issuekey={issue_key}&view={view}">View Issue</a>
                    </td>
                </tr>
            """.format(
                universe = html.escape(querystring['universe']),
                view = html.escape(querystring['view']),
                key = html.escape(querystring['project']),
                priority = html.escape(priority),
                status = html.escape(status),
                issuetype = html.escape(issuetype),
                fixversions = iterate_list(fixversion_names),
                affectsversions = iterate_list(affectversion_names),
                version = html.escape(querystring['version']),
                issue_key = html.escape(str(issue_key)),
                summary = html.escape(str(summary))
            )

        out += '</table>'

        return out

    projects_fixVersions_issue_map = None
    projects_affectsVersions_issue_map = None
    issue_map = None
    projects_version_info_map = None

    for change_request in change_request_list:
        if change_request.getIssueMap().getUniverseName() == querystring['universe']:
            issue_map = change_request.getIssueMap()
            projects_fixVersions_issue_map = change_request.getProjectsFixVersionIssueMap()
            projects_affectsVersions_issue_map = change_request.getProjectsAffectsVersionIssueMap()
            projects_version_info_map = change_request.getProjectsVersionInfoMap()
            break

    if querystring['view'] == 'fixes' or querystring['view'] == 'affected':
        version_issue_map = {}

        if querystring['view'] == 'fixes':
            version_issue_map = projects_fixVersions_issue_map[querystring['project']]
        else:
            version_issue_map = projects_affectsVersions_issue_map[querystring['project']]

        if querystring['version'] in version_issue_map:
            version_issues = version_issue_map[querystring['version']]
            
            out += '''
                <ul>
                    <li><a href="view?universe={universe}&project={project}&version={version}&view=fixes">View Fix Versions [Change Request]</a></li>
                    <li><a href="view?universe={universe}&project={project}&version={version}&view=affected">View Affected Versions</a></li>
                </ul>
            '''.format(
                universe = querystring['universe'],
                project = querystring['project'],
                version = querystring['version']
            )

            mlabel = change_request.getManualRiskLabel(querystring['project'], querystring['version'])

            out += '''
                <h2>Automatic Label:</h2>
                {alabel}
                <h2>Manual Label:</h2>
                <span id="mlabel">{mlabel}</span><br/><br/>
                '''.format(
                    alabel = change_request.getAutomaticRiskLabel(querystring['project'], querystring['version']),
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

                    xhttp.open("GET", `/label?type=change request&universe=%s&project=%s&version=%s&label=${label}`, true);
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
                querystring['project'],
                querystring['version'],
                str(mlabel)
            )

            out += '<hr/>'
            out += '<h2>Extracted Features</h2>'

            #issues_bugs = datautil.unlist_one(jsonquery.query(issue, 'fields.issuetype.name:Bug'))
            #issues_features = datautil.unlist_one(jsonquery.query(issue, 'fields.issuetype.name:Feature'))

            extracted_features = change_request.getExtractedFeatures(querystring['project'], querystring['version'], version_issues)

            out += '<h3>Change Request</h3>'
            out += '<h4>Release Date</h4>%s' % str(extracted_features['release_date'])
            out += '<h4>Elapsed Time</h4>%s' % str(extracted_features['elapsed_time'])

            out += "<h3>Issues</h3>"
            out += '<h4>Number of Issues</h4>%s' % str(extracted_features['number_of_issues'])
            out += '<h4>Number of Bugs</h4>%s' % str(extracted_features['number_of_bugs'])
            out += '<h4>Number of Features</h4>%s' % str(extracted_features['number_of_features'])
            out += '<h4>Number of Improvements</h4>%s' % str(extracted_features['number_of_improvements'])
            out += '<h4>Number of Other</h4>%s' % str(extracted_features['number_of_other'])
            out += '<h4>Discussion Time</h4>%s' % str(extracted_features['discussion_time'])
            out += '<h4>Number of Comments</h4>%s' % str(extracted_features['number_of_comments'])
            out += '<h4>Number of Blocked By Issues</h4>%s' % str(extracted_features['number_of_blocked_by_issues'])
            out += '<h4>Number of Blocks Issues</h4>%s' % str(extracted_features['number_of_blocks_issues'])
            out += '<h4>Delays</h4>%s' % str(extracted_features['delays'])
            out += '<h4>Number of Participants</h4>%s' % str(extracted_features['number_of_participants'])
            out += "<h4>Participants</h4>%s" % str(extracted_features['participants'].values())

            out += '<hr/>'


            out += '<table><tr><th>Created Date</th><th>Updated Date</th><th>Priority</th><th>Issue Type</th><th>Status</th><th>Resolution</th><th>Issue Key</th><th width="50%">Summary</th><th>Data</th><th>External Link</th></tr>'

            issues = {
                #issue_key:{
                #   'issue':{issuedata}
                #   'subtasks': {#issue_key:{...}}
                # }
            }

            for issue_key in version_issues:
                issue = issue_map.get(issue_key)

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
                    issue = issue_map.get(issue_key)
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
                                <a href="/view?universe={universe}&project={key}&version={version}&issuekey={issue_key}&view={view}issue">View Issue</a>
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
                        key = html.escape(querystring['project']),
                        priority = html.escape(priority),
                        status = html.escape(status),
                        resolution = html.escape(resolution),
                        issuetype = html.escape(issuetype),
                        version = html.escape(querystring['version']),
                        issue_key = html.escape(issue_key),
                        summary = html.escape(issue['fields']['summary']),
                        external = html.escape(issue['self'])
                    )

            out += '</table>'

    elif querystring['view'] == 'fixesissue' or querystring['view'] == 'affectedissue':
        
        version_issue_map = []
        if querystring['view'] == 'fixesissue':
            version_issue_map = projects_fixVersions_issue_map[querystring['project']]
        else: 
            version_issue_map = projects_affectsVersions_issue_map[querystring['project']]

        if querystring['version'] in version_issue_map:
            version_issues = version_issue_map[querystring['version']]

            if querystring['issuekey'] in version_issues:
                issue = issue_map.get(querystring['issuekey'])

                extracted_features = issue_map.getExtractedFeatures(querystring['issuekey'], projects_version_info_map[querystring['project']])

                out += '<h2>Extracted Data:</h2>'
                if not extracted_features['parent_key'] is None:
                    out += '<h3>Parent: <a href="/view?universe={universe}&project={project}&version={version}&issuekey={issue_key}&view={view}">{issue_key} - {summary}</a></h3>'.format(
                        universe = html.escape(querystring['universe']),
                        project = html.escape(querystring['project']),
                        version = html.escape(querystring['version']),
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
                out += '<h3>Fix Versions:</h3> <p>%s</p>' % iterate_list(extracted_features['fixversion_names'])
                out += '<h3>Affected Versions:</h3> <p>%s</p>' % iterate_list(extracted_features['affectversion_names'])
                out += '<h3>Description:</h3> <p>%s</p>' % html.escape(str(extracted_features['description'])).replace('\n', '<br/>')

                out += '<h3>Subtasks</h3>'
                out += displaySubtasks(extracted_features['subtasks'], issue_map)

                out += '<h3>Inward Issues</h3>'
                out += displayIssueLinks('inward', extracted_features['issuelinks_inward'], issue_map)

                out += '<h3>Outward Issues</h3>'
                out += displayIssueLinks('outward', extracted_features['issuelinks_outward'], issue_map)
                
                out += '<h3>Comments:</h3>'
                out += '<table><tr><th>Post Date</th><th>Author</th><th width="80%">Message</th></tr>'
                for comment in extracted_features['comments_extracted']:
                    out += '<tr><td>{pdate}</td><td>{author}</td><td>{message}</td></tr>'.format(
                        pdate = html.escape(comment['created_timestamp']),
                        author = html.escape(comment['author_displayName']),
                        message = html.escape(comment['message'])
                    )
                out += '</table>'

                out += '<hr/>'
                out += '<h2>Change Log:</h2>'
                out += '<h3>Assignee Changes:</h2>'
                out += extract_changes('assignee', extracted_features['assignee_changes'], extracted_features['created_date'])

                out += '<h3>Resolution Changes:</h2>'
                out += extract_changes('resolution', extracted_features['resolution_changes'], extracted_features['created_date'])

                out += '<h3>Status Changes:</h2>'
                out += extract_changes('status', extracted_features['status_changes'], extracted_features['created_date'])

                out += '<h3>Priority Changes*:</h2>'
                out += extract_changes('priority', extracted_features['priority_changes'], extracted_features['created_date'])

                out += '<h3>Issue Type Changes:</h2>'
                out += extract_changes('issuetype', extracted_features['issuetype_changes'], extracted_features['created_date'])

                out += '<h3>Fix Version Changes*:</h2>'
                out += extract_changes('Fix Version', extracted_features['fixversion_changes'], extracted_features['created_date'])

                out += '<h3>Affects Version Changes:</h2>'
                out += extract_changes('Version', extracted_features['affectsversion_changes'], extracted_features['created_date'])
                
                out += '<h3>Description Changes*:</h2>'
                out += extract_changes('description', extracted_features['description_changes'], extracted_features['created_date'])

                out += '<hr/>'
                out += '<h2>Derived Data:</h2>'
                out += '<h3>Creation To Last Update:</h3> %s' % html.escape(str(extracted_features['issue_duration']))
                out += '<h3>Delays* [~]:</h3> %s' % html.escape(str(extracted_features['delays']))
                out += '<h3>Number of Fix Versions*:</h3> <p>%s</p>' % extracted_features['number_of_fixversions']
                out += '<h3>Number of Affects Versions:</h3> <p>%s</p>' % extracted_features['number_of_affectsversions']
                out += '<h3>Number of subtasks:</h3> <p>%s</p>' % extracted_features['number_of_subtasks']
                out += '<h3>Number of issues links*:</h3> <p>%s</p>' % extracted_features['number_of_issuelinks']
                out += '<h3>Number of issues blocking this issue*:</h3> <p>%s</p>' % extracted_features['number_of_blocked_by_issues']
                out += '<h3>Number of issues this blocks* [?]:</h3> <p>%s</p>' % extracted_features['number_of_blocks_issues']
                out += '<h3>Number of Comments*:</h3> <p>%s</p>' % extracted_features['number_of_comments']
                out += '<h3>Discussion Time*:</h3> %s' % html.escape(str(extracted_features['discussion_time']))

                out += '<hr/>'
                out += '<h2>Raw Data:</h2>'
                out += '<pre>%s</pre>' % html.escape(json.dumps(issue, indent=4))

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
            <h1>%s - %s - %s - version %s</h1>
            %s
            
        </body>
    </html>"""  % (html.escape(querystring['universe']), html.escape(querystring['project']), html.escape(querystring['view']), html.escape(querystring['version']), out))
