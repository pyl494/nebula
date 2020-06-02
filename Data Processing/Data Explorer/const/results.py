self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

out = ""

for changeRequest in changeRequests:
    issueMap = changeRequest.getIssueMap()

    out += "<h2>%s</h2>" % html.escape(issueMap.getUniverseName())

    versionMap = changeRequest.getVersionMap()
    projectsFixVersions = changeRequest.getProjectsFixVersions()
    projectsAffectsVersions = changeRequest.getProjectsAffectsVersions()
    
    for key, versions in versionMap.items():
        out += "<h3>%s</h3>" % html.escape(key)
        out += "<table><tr><th>Date</th><th>Project</th><th>Version</th><th># issues w/ FixVersion</th><th># issues w/ Affected Version</th></tr>"

        for versionName, version in sorted(versions.items(), key=lambda v: v[1]['releaseDate'] if 'releaseDate' in v[1] else (' ' * 20) + 'unreleased' + v[0]):
            fcount = 0
            acount = 0

            if key in projectsFixVersions:
                fversions = projectsFixVersions[key]

                if versionName in fversions:
                    fcount = len(fversions[versionName])

            if key in projectsAffectsVersions:
                aversions = projectsAffectsVersions[key]

                if versionName in aversions:
                    acount = len(aversions[versionName])

            releaseDate = "Unreleased"
            if 'releaseDate' in version:
                releaseDate = version['releaseDate']

            out += """
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
                </tr>""".format(
                bgcol = 'transparent' if fcount == 0 else '#ddd',
                universe = html.escape(changeRequest.getIssueMap().getUniverseName()),
                date = html.escape(releaseDate),
                version = html.escape(versionName),
                key = html.escape(key),
                acount = acount,
                fcount = fcount
            )
        out += "</table>"

self.wfile.write(bytes(
    """
    <html>
        <head>
            <title>Explorer</title>
            <link rel="stylesheet" href="/css" media="all">
        </head>
        <body>
            <h1>Results</h1>
            %s
            
        </body>
    </html>"""  % out, "utf-8"))