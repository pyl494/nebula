import importlib.util
jsonquery_spec = importlib.util.spec_from_file_location('jsonquery', '../Data Processing/jsonquery.py')
jsonquery = importlib.util.module_from_spec(jsonquery_spec)
jsonquery_spec.loader.exec_module(jsonquery)

datautil_spec = importlib.util.spec_from_file_location('datautil', '../Data Processing/datautil.py')
datautil = importlib.util.module_from_spec(datautil_spec)
datautil_spec.loader.exec_module(datautil)

import datetime

self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

self.send("""
    <html>
        <head>
            <title>Explorer</title>
            <link rel="stylesheet" href="/css" media="all">
        </head>
        <body>
            <h1>Results</h1>
            <ul>
                <li><a href="/results?mode=default">Default View</a></li>
                <li><a href="/results?mode=features">Features View</a></li>
                <li><a href="/results?mode=stats">Stats View</a></li>
            </ul>
            """)

mode = 'default'
if 'mode' in querystring:
    mode = querystring['mode']

for change_request in change_request_list:
    issue_map = change_request.getIssueMap()

    self.send("<h2>%s</h2>" % html.escape(issue_map.getUniverseName()))

    change_request_meta_map = change_request.getChangeRequestMetaMap()
    projects_version_info_map = change_request.getProjectsVersionInfoMap()
    projects_fixVersion_issue_map = change_request.getProjectsFixVersionIssueMap()
    projects_affectsVersion_issue_map = change_request.getProjectsAffectsVersionIssueMap()

    prev_project_key = None    
    for change_request_issue_key, change_request_meta in sorted(change_request_meta_map.items(), key=lambda v: (v[1]['project_key'], v[1]['release_date'])):
        project_key = change_request_meta['project_key']
        version_name = change_request_meta['fixVersion']

        if prev_project_key != project_key:
            if not prev_project_key is None:
                self.send("</table>")
    
            self.send("<h3>%s</h3>" % html.escape(project_key))

            if mode == 'default':
                self.send("<table><tr><th>Date</th><th>Change Request Issue Key</th><th>Project</th><th>Version</th><th># issues w/ FixVersion</th><th># issues w/ Affected Version</th><th>Auto Label</th><th>Manual Label</th><th>Test Handshake</th></tr>")
            elif mode == 'features':
                self.send("<table><tr><th>Change Request Issue Key</th><th>Project</th><th>Version</th><th># issues w/ FixVersion</th><th># issues w/ Affected Version</th><th>Elapsed Time</th><th>Delays</th><th># of comments</th><th># of comments after release</th><th># of Votes</th><th>Discussion Time</th><th># of Participants</th><th># of Blocked By/Blocks Issues</th></tr>")
        
        prev_project_key = project_key

        fcount = len(change_request_meta['linked_issues'])
        acount = len(change_request_meta['affected_issues'])

        fvote_count = 0
        for issue_key in change_request_meta['linked_issues']:
            issue = issue_map.get(issue_key)
            fvote_count += issue['fields']['votes']['votes']

        acomment_count = acount
        avote_count = 0
        for issue_key in change_request_meta['affected_issues']:
            issue = issue_map.get(issue_key)
            acomment_count += len(issue['fields']['comment']['comments'])
            avote_count += issue['fields']['votes']['votes']

        release_date = change_request_meta['release_date']

        universe_name = change_request.getIssueMap().getUniverseName()

        if mode == 'features':
            features = change_request.getExtractedFeatures(change_request_issue_key, release_date)
            features_2 = change_request.getExtractedFeatures(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))

        if mode == 'default':
            self.send("""
                <tr style="background-color: {bgcol};">
                    <td>{date}</td>
                    <td>{change_request_issue_key}</td>
                    <td>{project_key}</td>
                    <td>{version}</td>
                    <td>
                        <a href="/view?universe={universe}&change_request={change_request_issue_key}&view=linked">{fcount}</a>
                    </td>
                    <td>
                        <a href="/view?universe={universe}&change_request={change_request_issue_key}&&view=affected">{acount}</a>
                    </td>
                    <td>{alabel}</td>
                    <td>{mlabel}</td>
                    <td><a href="/micro?type=test-handshake&change_request={change_request_issue_key}">Test</a></td>
                </tr>""".format(
                bgcol = 'transparent' if fcount == 0 else '#ddd',
                universe = html.escape(universe_name),
                date = html.escape(str(release_date)),
                change_request_issue_key = html.escape(change_request_issue_key),
                version = html.escape(str(version_name)),
                project_key = html.escape(project_key),
                acount = acount,
                fcount = fcount,
                alabel = str(change_request.getAutomaticRiskLabel(change_request_issue_key)),
                mlabel = str(change_request.getManualRiskLabel(change_request_issue_key))
            ))

        elif mode == 'features':
            self.send("""
                <tr style="background-color: {bgcol};">
                    <td>{change_request_issue_key}</td>
                    <td>{key}</td>
                    <td>{version}</td>
                    <td>
                        <a href="/view?universe={universe}&change_request={change_request_issue_key}&view=linked">{fcount}</a>
                    </td>
                    <td>
                        <a href="/view?universe={universe}&change_request={change_request_issue_key}&view=affected">{acount}</a>
                    </td>
                    <td>{elapsedtime}</td>
                    <td>{delays}</td>
                    <td>{numcomments}</td>
                    <td>{numcomments_post} + {acomment_count}</td>
                    <td>{fvote_count} + {avote_count}</td>
                    <td>{discussiontime}</td>
                    <td>{numparticipants}</td>
                    <td>{numblockedby} / {numblocks}</td>
                </tr>""".format(
                bgcol = 'transparent' if fcount == 0 else '#ddd',
                universe = html.escape(universe_name),
                date = html.escape(str(release_date)),
                key = html.escape(project_key),
                change_request_issue_key = html.escape(change_request_issue_key),
                version = html.escape(str(version_name)),
                acount = acount,
                fcount = fcount,
                elapsedtime = str(datautil.map_get(features, ('elapsed_time',))),
                delays = str(datautil.map_get(features, ('delays',))),
                numcomments = str(datautil.map_get(features, ('number_of_comments',))),
                numcomments_post = str(datautil.map_get(features_2, ('number_of_comments','sum')) - datautil.map_get(features, ('number_of_comments','sum'))),
                acomment_count = str(acomment_count),
                fvote_count = str(fvote_count),
                avote_count = str(avote_count),
                discussiontime = str(datautil.map_get(features, ('discussion_time',))),
                numparticipants = str(datautil.map_get(features, ('number_of_participants',))),
                numblockedby = str(datautil.map_get(features, ('number_of_blocked_by_issues',))),
                numblocks = str(datautil.map_get(features, ('number_of_blocks_issues',)))

            ))
    self.send("</table>")

self.send("""
        </body>
    </html>""")