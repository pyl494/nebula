import importlib.util
jsonquery_spec = importlib.util.spec_from_file_location('jsonquery', '../Data Processing/jsonquery.py')
jsonquery = importlib.util.module_from_spec(jsonquery_spec)
jsonquery_spec.loader.exec_module(jsonquery)

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
            <h1>Results</h1>""")

for change_request in change_request_list:
    issue_map = change_request.getIssueMap()

    self.send("<h2>%s</h2>" % html.escape(issue_map.getUniverseName()))

    projects_version_info_map = change_request.getProjectsVersionInfoMap()
    projects_fixVersion_issue_map = change_request.getProjectsFixVersionIssueMap()
    projects_affectsVersion_issue_map = change_request.getProjectsAffectsVersionIssueMap()
    
    for project_key, version_info_map in projects_version_info_map.items():
        self.send("<h3>%s</h3>" % html.escape(project_key))
        self.send("<table><tr><th>Date</th><th>Project</th><th>Version</th><th># issues w/ FixVersion</th><th># issues w/ Affected Version</th><th>Auto Label</th><th>Manual Label</th><th>Extracted Feature</th></tr>")

        for version_name, version_info in sorted(version_info_map.items(), key=lambda v: v[1]['releaseDate'] if 'releaseDate' in v[1] else (' ' * 20) + 'unreleased' + v[0]):
            fcount = 0
            acount = 0

            if project_key in projects_fixVersion_issue_map:
                fversions = projects_fixVersion_issue_map[project_key]

                if version_name in fversions:
                    fcount = len(fversions[version_name])

            if project_key in projects_affectsVersion_issue_map:
                aversions = projects_affectsVersion_issue_map[project_key]

                if version_name in aversions:
                    acount = len(aversions[version_name])

            release_date = "Unreleased"
            if 'releaseDate' in version_info:
                release_date = version_info['releaseDate']

            universe_name = change_request.getIssueMap().getUniverseName()

            feature = None
            if project_key in projects_fixVersion_issue_map:
                version_issue_map = projects_fixVersion_issue_map[project_key]
                if version_name in version_issue_map:
                    feature = change_request.getExtractedFeatures(project_key, version_name, version_issue_map[version_name])['delays']

            self.send("""
                <tr style="background-color: {bgcol};">
                    <td>{date}</td>
                    <td>{key}</td>
                    <td>{version}</td>
                    <td>
                        <a href="/view?universe={universe}&project={key}&version={version}&view=fixes">{fcount}</a>
                    </td>
                    <td>
                        <a href="/view?universe={universe}&project={key}&version={version}&view=affected">{acount}</a>
                    </td>
                    <td>{alabel}</td>
                    <td>{mlabel}</td>
                    <td>{feature}</td>
                </tr>""".format(
                bgcol = 'transparent' if fcount == 0 else '#ddd',
                universe = html.escape(universe_name),
                date = html.escape(release_date),
                version = html.escape(version_name),
                key = html.escape(project_key),
                acount = acount,
                fcount = fcount,
                alabel = str(change_request.getAutomaticRiskLabel(project_key, version_name)),
                mlabel = str(change_request.getManualRiskLabel(project_key, version_name)),
                feature = str(feature)
            ))
        self.send("</table>")

self.send("""
        </body>
    </html>""")