/*
Purpose
This is the new version. It uses the Jira Server API to dump the data from jira projects.

Instructions
Paste this into a browser developer console when you are on the domain of a jira project

Status
This should run.

Source
Harun Delic
*/

if(typeof(String.prototype.trim) === "undefined")
{
    String.prototype.trim = function() 
    {
        return String(this).replace(/^\s+|\s+$/g, '');
    };
}

function getpage(data, pagesRemaining, page){
    if (pagesRemaining.length > 0)
    {
        let target = pagesRemaining[0];

        if (('total' in pagesRemaining) && pagesRemaining.total < page)
        {
            console.log(target.project, 'DONE');
            return;
        }
        
        console.log('GET', target.project, page);
        let query = encodeURIComponent(`ORDER BY priority DESC, updated DESC`);
        let req = new Request(`${target.baseurl}rest/api/2/search?jql=${query}&validateQuery=false&maxResults=1000&startAt=${page}&fields=*all&expand=names,changelog`);
        fetch(req)
            .then(response => {
                console.log(response.status, response.statusText);
                if (response.status == 200)
                {
                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.indexOf("application/json") !== -1) {
                        return response.json().then(issues => {
                            console.log('SAVING', target.project, page);
                            if ('total' in issues)
                            {
                                pagesRemaining.total = issues['total'];
                            }

                            if ('issues' in issues)
                            {
                                downloaddata(JSON.stringify({'issues': issues.issues}, null, 4), target.project + '_' + page.toString());
                                getpage('', pagesRemaining, page + 1000);
                            }
                            else
                                return Promise.reject('bad json');
                        });
                    }
                    else
                        return Promise.reject('not json response');
                }
                else
                {
                    console.log('DONE', target.project, page);
                    pagesRemaining.splice(0, 1);
                    getpage('', pagesRemaining, 0);
                    return Promise.reject('not 200 response');
                }
            }).catch((error)=>{
                console.log('ERROR', target.project, page);
                console.log(error);
                pagesRemaining.splice(0, 1);
                getpage('', pagesRemaining, 0);
            })
    }
};

let pull = function(pages)
{
    getpage('', pages, 0);
}

function downloaddata(data, name){
    var file = new Blob([data], {type: 'text/json'});
    var a = document.createElement("a"),
    url = URL.createObjectURL(file);
    a.href = url;
    a.download = `${name}.json`;
    document.body.appendChild(a);
    a.click();
    setTimeout(function() {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);  
    }, 0); 
};

pull([{
    baseurl: 'https://issues.apache.org/jira/',
    project: 'APACHE'
}])

pull([{
    baseurl: 'https://jira.atlassian.com/',
    project: 'ATLASSIAN'
}])

pull([{
    baseurl: 'https://tngtech-oss.atlassian.net/',
    project: 'TNGTECH'
}])

pull([{
    baseurl: 'https://jira.sakaiproject.org/',
    project: 'SAKAI'
}])

pull([{
    baseurl: 'https://bugreports.qt.io/',
    project: 'QT'
}])

