self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

out = ""

try:
    import importlib.util
    jsonquery_spec = importlib.util.spec_from_file_location('jsonquery', '../Data Processing/jsonquery.py')
    jsonquery = importlib.util.module_from_spec(jsonquery_spec)
    jsonquery_spec.loader.exec_module(jsonquery)

    datautil_spec = importlib.util.spec_from_file_location('datautil', '../Data Processing/datautil.py')
    datautil = importlib.util.module_from_spec(datautil_spec)
    datautil_spec.loader.exec_module(datautil)

    def unlist_one(x):
        if len(x) == 1:
            return x[0]
        return x

    def extract_changes(type, changes):
        out = '<table><tr><th>Date</th><th>Time Since Creation</th><th>From</th><th>To</th></tr>'
        for change in changes:
            change_timestamp = unlist_one(jsonquery.query(change, '^created'))
            change_date = datetime.strptime(change_timestamp, datetime_format)
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
        out = '<ul>'
        for item in items:
            out += '<li>%s</li>' % html.escape(item)
        out += '</ul>'

        return out

    def displayIssueLinks(direction, issuelinks, issueMap):
        out = '<table><tr><th>Priority</th><th>Issue Type</th><th>Status</th><th>Issue Key</th><th>Fix Versions</th><th>Affects Versions</th><th width="50%">Summary</th><th>Data</th><th>Relationship</th></tr>'
        for issue in issuelinks:
            issuekey = unlist_one(jsonquery.query(issue, direction + 'Issue.^key'))
            priority = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.priority.^name'))
            status = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.status.^name'))
            issuetype = ' :: '.join(jsonquery.query(issue, direction + 'Issue.fields.issuetype.^name'))
            relationship = ' :: '.join(jsonquery.query(issue, 'type.^' + direction))
            summary = unlist_one(jsonquery.query(issue, direction + 'Issue.fields.^summary'))

            gissue = issueMap.get(issuekey)
            fixversion_names = jsonquery.query(gissue, 'fields.fixVersions.^name')
            affectversion_names = jsonquery.query(gissue, 'fields.versions.^name')

            out += """
                <tr>
                    <td>{priority}</td>
                    <td>{issuetype}</td>
                    <td>{status}</td>
                    <td>{issuekey}</td>
                    <td>{fixversions}</td>
                    <td>{affectsversions}</td>
                    <td>{summary}</td>
                    <td>
                        <a href="/view?universe={universe}&project={key}&version={version}&issuekey={issuekey}&view={view}">View Issue</a>
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
                issuekey = html.escape(str(issuekey)),
                summary = html.escape(str(summary)),
                relationship = html.escape(relationship)
            )

        out += '</table>'

        return out

    def displaySubtasks(subtasks, issueMap):
        out = '<table><tr><th>Priority</th><th>Issue Type</th><th>Status</th><th>Issue Key</th><th>Fix Versions</th><th>Affects Versions</th><th width="50%">Summary</th><th>Data</th></tr>'
        for issue in subtasks:
            issuekey = unlist_one(jsonquery.query(issue,  '^key'))
            priority = ' :: '.join(jsonquery.query(issue, 'fields.priority.^name'))
            status = ' :: '.join(jsonquery.query(issue, 'fields.status.^name'))
            issuetype = ' :: '.join(jsonquery.query(issue, 'fields.issuetype.^name'))
            summary = unlist_one(jsonquery.query(issue, 'fields.^summary'))

            gissue = issueMap.get(issuekey)
            fixversion_names = jsonquery.query(gissue, 'fields.fixVersions.^name')
            affectversion_names = jsonquery.query(gissue, 'fields.versions.^name')

            out += """
                <tr>
                    <td>{priority}</td>
                    <td>{issuetype}</td>
                    <td>{status}</td>
                    <td>{issuekey}</td>
                    <td>{fixversions}</td>
                    <td>{affectsversions}</td>
                    <td>{summary}</td>
                    <td>
                        <a href="/view?universe={universe}&project={key}&version={version}&issuekey={issuekey}&view={view}">View Issue</a>
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
                issuekey = html.escape(str(issuekey)),
                summary = html.escape(str(summary))
            )

        out += '</table>'

        return out

    projectsFixVersions = None
    projectsAffectsVersions = None
    issueMap = None
    versionMap = None

    for changeRequest in changeRequests:
        if changeRequest.getIssueMap().getUniverseName() == querystring['universe']:
            issueMap = changeRequest.getIssueMap()
            projectsFixVersions = changeRequest.getProjectsFixVersions()
            projectsAffectsVersions = changeRequest.getProjectsAffectsVersions()
            versionMap = changeRequest.getVersionMap()
            break

    if querystring['view'] == 'fixes' or querystring['view'] == 'affected':
        versions = {}

        if querystring['view'] == 'fixes':
            versions = projectsFixVersions[querystring['project']]
        else:
            versions = projectsAffectsVersions[querystring['project']]

        if querystring['version'] in versions:
            version = versions[querystring['version']]

            mlabel = changeRequest.getManualRiskLabel(querystring['project'], querystring['version'])

            out += '''
                <h2>Automatic Label:</h2>
                {alabel}
                <h2>Manual Label:</h2>
                <span id="mlabel">{mlabel}</span><br/><br/>
                '''.format(
                    alabel = changeRequest.getAutomaticRiskLabel(querystring['project'], querystring['version']),
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


            out += '<table><tr><th>Created Date</th><th>Updated Date</th><th>Priority</th><th>Issue Type</th><th>Status</th><th>Resolution</th><th>Issue Key</th><th width="50%">Summary</th><th>Data</th><th>External Link</th></tr>'

            issues = {
                #issuekey:{
                #   'issue':{issuedata}
                #   'subtasks': {#issuekey:{...}}
                # }
            }

            for issuekey in version:
                issue = issueMap.get(issuekey)

                parentkey = jsonquery.query(issue, 'fields.parent.^key')
                subtasks = unlist_one(jsonquery.query(issue, 'fields.^subtasks'))

                if len(parentkey) == 1:
                    datautil.map_list(issues, (parentkey[0],), issuekey)
                else:
                    datautil.map_touch(issues, (issuekey, ), [])

            for parentkey, subtasks in issues.items():
                issuepack = [{'issuekey': parentkey, 'indent': 0}]
                issuepack += [{'issuekey': x, 'indent': 1} for x in subtasks]

                for pack in issuepack:
                    issuekey = pack['issuekey']
                    issue = issueMap.get(issuekey)
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
                            <td>{issuekey}</td>
                            <td>{summary}</td>
                            <td>
                                <a href="/view?universe={universe}&project={key}&version={version}&issuekey={issuekey}&view={view}issue">View Issue</a>
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
                        issuekey = html.escape(issuekey),
                        summary = html.escape(issue['fields']['summary']),
                        external = html.escape(issue['self'])
                    )

            out += '</table>'

    elif querystring['view'] == 'fixesissue' or querystring['view'] == 'affectedissue':
        
        versions = []
        if querystring['view'] == 'fixesissue':
            versions = projectsFixVersions[querystring['project']]
        else: 
            versions = projectsAffectsVersions[querystring['project']]

        if querystring['version'] in versions:
            version = versions[querystring['version']]

            if querystring['issuekey'] in version:
                issue = issueMap.get(querystring['issuekey'])

                from datetime import datetime

                summary = unlist_one(jsonquery.query(issue, 'fields.^summary'))
                resolution_name = unlist_one(jsonquery.query(issue, 'fields.resolution.^name'))
                issuetype_name = unlist_one(jsonquery.query(issue, 'fields.issuetype.^name'))
                priority_name = unlist_one(jsonquery.query(issue, 'fields.priority.^name'))
                assignee_displayName = unlist_one(jsonquery.query(issue, 'fields.assignee.^displayName'))
                assignee_accountId = unlist_one(jsonquery.query(issue, 'fields.assignee.^accountId'))
                reporter_displayName = unlist_one(jsonquery.query(issue, 'fields.reporter.^displayName'))
                reporter_accountId = unlist_one(jsonquery.query(issue, 'fields.reporter.^accountId'))
                fixversion_names = jsonquery.query(issue, 'fields.fixVersions.^name')
                affectversion_names = jsonquery.query(issue, 'fields.versions.^name')
                created_timestamp = unlist_one(jsonquery.query(issue, 'fields.^created'))
                updated_timestamp = unlist_one(jsonquery.query(issue, 'fields.^updated'))
                duedate_timestamp = unlist_one(jsonquery.query(issue, 'fields.^duedate'))
                resolutiondate_timestamp = unlist_one(jsonquery.query(issue, 'fields.^resolutiondate'))
                
                assignee_changes = jsonquery.query(issue, 'changelog.histories.$items.field:assignee')
                status_changes = jsonquery.query(issue, 'changelog.histories.$items.field:status')
                resolution_changes = jsonquery.query(issue, 'changelog.histories.$items.field:resolution')
                priority_changes = jsonquery.query(issue, 'changelog.histories.$items.field:priority')
                issuetype_changes = jsonquery.query(issue, 'changelog.histories.$items.field:issuetype')
                fixversion_changes = jsonquery.query(issue, 'changelog.histories.$items.field:Fix Version')
                affectsversion_changes = jsonquery.query(issue, 'changelog.histories.$items.field:Version')
                description_changes = jsonquery.query(issue, 'changelog.histories.$items.field:description')

                datetime_format = '%Y-%m-%dT%H:%M:%S.%f%z'
                created_date = datetime.strptime(created_timestamp, datetime_format)
                
                updated_date = None
                if not updated_timestamp is None:
                    updated_date = datetime.strptime(updated_timestamp, datetime_format)
                
                resolutiondate_date = None
                if not resolutiondate_timestamp is None:
                    resolutiondate_date = datetime.strptime(resolutiondate_timestamp, datetime_format)

                issue_duration = None
                if not updated_date is None:
                    issue_duration = updated_date - created_date

                duedate_date = None
                if not duedate_timestamp is None:
                    duedate_date = datetime.fromisoformat(duedate_timestamp)
                
                earliest_duedate = duedate_date
                check_versions = []
                if len(fixversion_changes) > 0:
                    for change in fixversion_changes:
                        items = jsonquery.query(change, 'items.$field:Fix Version')
                        for item in items:
                            item_from = item['fromString']
                            item_to = item['toString'] 

                            if not item_from is None:
                                check_versions += [item_from]

                            if not item_to is None:
                                check_versions += [item_to]
                                
                if len(fixversion_names) > 0:
                    check_versions += fixversion_names

                versions = versionMap[querystring['project']]
                for version_name in check_versions:
                    if version_name in versions:
                        version = versions[version_name]
                        if 'releaseDate' in version:
                            version_date = datetime.strptime(version['releaseDate'] + "T0:0:0.000+0000", datetime_format)
                            if earliest_duedate is None or version_date < earliest_duedate:
                                earliest_duedate = version_date
                
                overdue = 0
                if not earliest_duedate is None:
                    overdue = resolutiondate_date - earliest_duedate

                number_of_fixversions = len(fixversion_names)
                number_of_affectsversions = len(affectversion_names)

                description = unlist_one(jsonquery.query(issue, 'fields.^description'))

                comments = jsonquery.query(issue, 'fields.^comment')[0]['comments']
                number_of_comments = len(comments)
                discussion_time = 0
                if len(comments) > 0:
                    first_comment_timestamp = comments[0]['created']
                    last_comment_timestamp = comments[len(comments) - 1]['created']

                    first_comment_date = datetime.strptime(first_comment_timestamp, datetime_format)
                    last_comment_date = datetime.strptime(last_comment_timestamp, datetime_format)

                    discussion_time = last_comment_date - first_comment_date

                issuelinks = unlist_one(jsonquery.query(issue, 'fields.^issuelinks'))
                issuelinks_outward = jsonquery.query(issue, 'fields.issuelinks.$outwardIssue')
                issuelinks_inward = jsonquery.query(issue, 'fields.issuelinks.$inwardIssue')
                
                blocked_by_issuelinks = jsonquery.query(issuelinks, '$type.outward:is blocked by')
                blocks_issuelinks = jsonquery.query(issuelinks, '$type.outward:blocks')

                number_of_issuelinks = len(issuelinks)
                number_of_blocked_by_issues = len(blocked_by_issuelinks)
                number_of_blocks_issues = len(blocks_issuelinks)

                parentKey = jsonquery.query(issue, 'fields.parent.^key')
                parentSummary = unlist_one(jsonquery.query(issue, 'fields.parent.fields.^summary'))
                if len(parentKey) == 1:
                    parentKey = parentKey[0]
                else:
                    parentKey = None

                subtasks = unlist_one(jsonquery.query(issue, 'fields.^subtasks'))

                number_of_subtasks = len(subtasks)

                out += '<h2>Extracted Data:</h2>'
                if not parentKey is None:
                    out += '<h3>Parent: <a href="/view?universe={universe}&project={project}&version={version}&issuekey={issuekey}&view={view}">{issuekey} - {summary}</a></h3>'.format(
                        universe = html.escape(querystring['universe']),
                        project = html.escape(querystring['project']),
                        version = html.escape(querystring['version']),
                        issuekey = html.escape(parentKey),
                        view = html.escape(querystring['view']),
                        summary = html.escape(parentSummary)
                    )
                out += '<h3>Summary: %s</h3>' % html.escape(summary)
                out += '<h3>Resolution:</h3> <p>%s</p>' % html.escape(str(resolution_name))
                out += '<h3>Issue Type:</h3> <p>%s</p>' % html.escape(str(issuetype_name))
                out += '<h3>Priority*:</h3> <p>%s</p>' % html.escape(str(priority_name))
                out += '<h3>Assignee:</h3> <p>%s - %s</p>' % (html.escape(str(assignee_displayName)), html.escape(str(assignee_accountId)))
                out += '<h3>Reporter:</h3> <p>%s - %s</p>' % (html.escape(str(reporter_displayName)), html.escape(str(reporter_accountId)))
                out += '<h3>Created Date:</h3> <p>%s</p>' % html.escape(str(created_timestamp))
                out += '<h3>Resolution Date:</h3> <p>%s</p>' % html.escape(str(resolutiondate_timestamp))
                out += '<h3>Last Updated Date:</h3> <p>%s</p>' % html.escape(str(updated_timestamp))
                out += '<h3>Due Date:</h3> <p>%s</p>' % html.escape(str(duedate_timestamp))
                out += '<h3>Fix Versions:</h3> <p>%s</p>' % iterate_list(fixversion_names)
                out += '<h3>Affected Versions:</h3> <p>%s</p>' % iterate_list(affectversion_names)
                out += '<h3>Description:</h3> <p>%s</p>' % html.escape(str(description)).replace('\n', '<br/>')

                out += '<h3>Subtasks</h3>'
                out += displaySubtasks(subtasks, issueMap)

                out += '<h3>Inward Issues</h3>'
                out += displayIssueLinks('inward', issuelinks_inward, issueMap)

                out += '<h3>Outward Issues</h3>'
                out += displayIssueLinks('outward', issuelinks_outward, issueMap)
                
                out += '<h3>Comments:</h3>'
                out += '<table><tr><th>Post Date</th><th>Author</th><th width="80%">Message</th></tr>'
                for comment in comments:
                    out += '<tr><td>{pdate}</td><td>{author}</td><td>{message}</td></tr>'.format(
                        pdate = html.escape(comment['created']),
                        author = html.escape(comment['author']['displayName']),
                        message = html.escape(comment['body'])
                    )
                out += '</table>'

                out += '<hr/>'
                out += '<h2>Change Log:</h2>'
                out += '<h3>Assignee Changes:</h2>'
                out += extract_changes('assignee', assignee_changes)

                out += '<h3>Resolution Changes:</h2>'
                out += extract_changes('resolution', resolution_changes)

                out += '<h3>Status Changes:</h2>'
                out += extract_changes('status', status_changes)

                out += '<h3>Priority Changes*:</h2>'
                out += extract_changes('priority', priority_changes)

                out += '<h3>Issue Type Changes:</h2>'
                out += extract_changes('issuetype', issuetype_changes)

                out += '<h3>Fix Version Changes*:</h2>'
                out += extract_changes('Fix Version', fixversion_changes)

                out += '<h3>Affects Version Changes:</h2>'
                out += extract_changes('Version', affectsversion_changes)
                
                out += '<h3>Description Changes*:</h2>'
                out += extract_changes('description', description_changes)

                out += '<hr/>'
                out += '<h2>Derived Data:</h2>'
                out += '<h3>Creation To Last Update:</h3> %s' % html.escape(str(issue_duration))
                out += '<h3>Overdue Duration* [~]:</h3> %s' % html.escape(str(overdue))
                out += '<h3>Number of Fix Versions*:</h3> <p>%s</p>' % number_of_fixversions
                out += '<h3>Number of Affects Versions:</h3> <p>%s</p>' % number_of_affectsversions
                out += '<h3>Number of subtasks:</h3> <p>%s</p>' % number_of_subtasks
                out += '<h3>Number of issues links*:</h3> <p>%s</p>' % number_of_issuelinks
                out += '<h3>Number of issues blocking this issue*:</h3> <p>%s</p>' % number_of_blocked_by_issues
                out += '<h3>Number of issues this blocks* [?]:</h3> <p>%s</p>' % number_of_blocks_issues
                out += '<h3>Number of Comments*:</h3> <p>%s</p>' % number_of_comments
                out += '<h3>Discussion Time*:</h3> %s' % html.escape(str(discussion_time))

                out += '<hr/>'
                out += '<h2>Raw Data:</h2>'
                out += '<pre>%s</pre>' % html.escape(json.dumps(issue, indent=4))

except Exception as e:
    out += exception_html(e)
    
self.wfile.write(bytes(
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
    </html>"""  % (html.escape(querystring['universe']), html.escape(querystring['project']), html.escape(querystring['view']), html.escape(querystring['version']), out), "utf-8"))
